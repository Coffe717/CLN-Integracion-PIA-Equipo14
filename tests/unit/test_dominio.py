import pytest

from src.domain import eventos as ev
from src.domain.especificaciones import (
    EsTerminalSpec, EstadoEnSpec, IntentosAgotadosSpec, PaqueteEstancadoSpec, PuedeEntregarseSpec,
    PuedeEnviarSpec, RemitenteActivoSpec, RemitentePreferenteSpec, RequiereAutorizacionTercerIntentoSpec,
    SinActualizacionSpec, TieneAutorizacionSpec,
)
from src.domain.estado import ESTADOS_TERMINALES, ETIQUETAS, TRANSICIONES, EstadoEnvio, MaquinaEstados
from src.domain.excepciones import (
    ReglaNegocioException, ResolucionNoPermitidaException, TransicionEstadoInvalidaException,
    ValorInvalidoException,
)
from src.domain.incidencia import EstadoIncidencia, Incidencia, TipoIncidencia
from src.domain.manifiesto import EstadoManifiesto, EstadoRuta, ManifiestoViaje, RutaReparto
from src.domain.remitente import Remitente
from src.domain.valores import Direccion, Instalacion, ahora
from tests.helpers import autorizacion, con_dos_ausencias, nuevo_paquete, paquete_en

E = EstadoEnvio


class TestMaquinaEstados:
    def test_flujo_feliz_completo(self):
        p = paquete_en(E.ENTREGADO)
        assert [h.estado for h in p.historial] == [E.RECIBIDO, E.CLASIFICADO, E.EN_TRANSITO,
                                                   E.CENTRO_DESTINO, E.EN_REPARTO, E.ENTREGADO]
        assert p.es_terminal

    def test_todos_los_estados_tienen_etiqueta_y_reglas(self):
        assert set(TRANSICIONES) == set(E) == set(ETIQUETAS)
        assert {E.ENTREGADO, E.CANCELADO, E.DEVUELTO_A_ORIGEN} == set(ESTADOS_TERMINALES)

    @pytest.mark.parametrize("origen,destino", [
        (E.RECIBIDO, E.ENTREGADO), (E.CLASIFICADO, E.EN_REPARTO), (E.EN_TRANSITO, E.RECIBIDO),
        (E.ENTREGADO, E.EN_REPARTO), (E.CANCELADO, E.RECIBIDO)])
    def test_transiciones_invalidas(self, origen, destino):
        m = MaquinaEstados(origen)
        assert not m.puede(destino)
        with pytest.raises(TransicionEstadoInvalidaException):
            m.transicionar(destino)
        assert m.estado is origen

    def test_transicion_valida(self):
        m = MaquinaEstados()
        assert m.puede(E.CLASIFICADO) and not m.es_terminal
        assert m.transicionar(E.CLASIFICADO) is E.CLASIFICADO


class TestPaqueteAgregado:
    def test_recibir_genera_guia_tarifa_y_estado_inicial(self):
        p = nuevo_paquete(7)
        assert str(p.guia) == "CB-0000000007" and p.estado is E.RECIBIDO
        assert p.tarifa.total.monto == 150 and p.etiqueta_estado() == "Recibido"
        assert isinstance(p.pull_events()[0], ev.PaqueteRecibido)
        assert p.pull_events() == []

    def test_recibir_exige_remitente(self):
        from src.domain.paquete import Paquete
        p = nuevo_paquete()
        with pytest.raises(ValorInvalidoException):
            Paquete.recibir(p.guia, "", p.destinatario, p.origen, p.destino, p.peso, p.dimensiones,
                            p.nivel, __import__("src.domain.tabulador", fromlist=["x"]).CalculadoraTarifa(),
                            Instalacion("S"))

    def test_cancelar_solo_desde_recibido(self):
        p = paquete_en(E.CLASIFICADO)
        with pytest.raises(TransicionEstadoInvalidaException):
            p.cancelar("tarde")

    def test_no_se_puede_clasificar_dos_veces(self):
        p = paquete_en(E.CLASIFICADO)
        with pytest.raises(TransicionEstadoInvalidaException):
            p.clasificar(Instalacion("CD"))

    def test_segunda_ausencia_pide_autorizacion_y_no_reagenda(self):
        p = paquete_en(E.EN_REPARTO)
        p.registrar_ausencia("Juan"); p.marcar_en_reparto("Juan"); p.pull_events()
        p.registrar_ausencia("Juan")
        assert p.estado is E.SEGUNDO_INTENTO_PENDIENTE and p.intentos_fallidos == 2
        assert any(isinstance(e, ev.TercerIntentoRequiereAutorizacion) for e in p.pull_events())

    def test_ausencia_fuera_de_reparto_es_invalida(self):
        with pytest.raises(TransicionEstadoInvalidaException):
            paquete_en(E.CLASIFICADO).registrar_ausencia("Juan")

    def test_autorizar_antes_de_tiempo(self):
        with pytest.raises(ReglaNegocioException):
            paquete_en(E.EN_REPARTO).autorizar_tercer_intento(autorizacion())

    def test_autorizar_registra_evento_e_historial(self):
        p = con_dos_ausencias(paquete_en(E.EN_REPARTO))
        p.pull_events()
        p.autorizar_tercer_intento(autorizacion())
        assert not p.requiere_autorizacion_tercer_intento
        assert isinstance(p.pull_events()[0], ev.TercerIntentoAutorizado)
        assert "autorizado" in p.historial[-1].descripcion

    def test_rechazo_inicia_logistica_inversa(self):
        p = paquete_en(E.EN_REPARTO)
        p.pull_events()
        p.registrar_rechazo("No lo quiero", "Juan")
        assert p.estado is E.RECHAZADO_EN_DEVOLUCION and p.motivo_rechazo == "No lo quiero"
        assert [type(e) for e in p.pull_events()] == [ev.PaqueteRechazado, ev.DevolucionIniciada]
        p.completar_devolucion(Instalacion("Sucursal Centro"))
        assert p.estado is E.DEVUELTO_A_ORIGEN

    def test_rechazo_sin_motivo(self):
        with pytest.raises(ValorInvalidoException):
            paquete_en(E.EN_REPARTO).registrar_rechazo("  ")

    def test_direccion_incorrecta_pausa_y_se_corrige(self):
        p = paquete_en(E.DIRECCION_INCORRECTA)
        assert p.estado is E.DIRECCION_INCORRECTA
        p.corregir_direccion(Direccion("Calle Nueva 10", "Monterrey"), "Agente")
        assert p.destino.calle == "Calle Nueva 10"
        assert any(isinstance(e, ev.DireccionCorregida) for e in p.pull_events())
        p.marcar_en_reparto("Juan")
        assert p.estado is E.EN_REPARTO

    def test_corregir_direccion_solo_si_esta_pausado(self):
        with pytest.raises(ReglaNegocioException):
            paquete_en(E.EN_REPARTO).corregir_direccion(Direccion("X 1", "MTY"))

    def test_incidencia_mayor_retiene_y_se_puede_reanudar(self):
        p = paquete_en(E.RETENIDO_POR_INCIDENCIA)
        assert p.estado is E.RETENIDO_POR_INCIDENCIA
        p.marcar_en_reparto("Juan")
        assert p.estado is E.EN_REPARTO

    @pytest.mark.parametrize("estado", list(E))
    def test_paquetes_en_cualquier_estado_son_reconstruibles(self, estado):
        assert paquete_en(estado, 3).estado is estado

    def test_horas_sin_actualizacion(self):
        p = nuevo_paquete()
        futuro = ahora().replace(year=ahora().year + 1)
        assert p.horas_sin_actualizacion(futuro) > 24 * 300


class TestEspecificaciones:
    def test_combinacion_and_or_not(self):
        p = paquete_en(E.EN_REPARTO)
        en_reparto = EstadoEnSpec(E.EN_REPARTO)
        terminal = EsTerminalSpec()
        assert (en_reparto & ~terminal).is_satisfied_by(p)
        assert (terminal | en_reparto).is_satisfied_by(p)
        assert not (terminal & en_reparto).is_satisfied_by(p)
        assert (~en_reparto).is_satisfied_by(p) is False
        assert PuedeEntregarseSpec().is_satisfied_by(p)

    def test_requiere_autorizacion(self):
        p = con_dos_ausencias(paquete_en(E.EN_REPARTO))
        assert IntentosAgotadosSpec().is_satisfied_by(p)
        assert RequiereAutorizacionTercerIntentoSpec().is_satisfied_by(p)
        p.autorizar_tercer_intento(autorizacion())
        assert TieneAutorizacionSpec().is_satisfied_by(p)
        assert not RequiereAutorizacionTercerIntentoSpec().is_satisfied_by(p)

    def test_estancado(self):
        p = paquete_en(E.EN_TRANSITO)
        mañana = ahora().replace(day=ahora().day) 
        futuro = ahora().replace(year=ahora().year + 1)
        assert SinActualizacionSpec(24, futuro).is_satisfied_by(p)
        assert PaqueteEstancadoSpec(24, futuro).is_satisfied_by(p)
        assert not PaqueteEstancadoSpec(24, mañana).is_satisfied_by(p)
        assert not PaqueteEstancadoSpec(24, futuro).is_satisfied_by(paquete_en(E.ENTREGADO))

    def test_remitentes(self):
        activo = Remitente("A", "A", True, True)
        inactivo = Remitente("B", "B", False, False)
        assert RemitenteActivoSpec().is_satisfied_by(activo) and not RemitenteActivoSpec().is_satisfied_by(inactivo)
        assert RemitentePreferenteSpec().is_satisfied_by(activo)
        assert (RemitenteActivoSpec() & RemitentePreferenteSpec()).is_satisfied_by(activo)
        assert PuedeEnviarSpec().is_satisfied_by(activo) and not PuedeEnviarSpec().is_satisfied_by(inactivo)


class TestIncidencia:
    def test_ciclo_de_vida(self):
        i = Incidencia.abrir("CB-0000000001", TipoIncidencia.DANO, "caja rota", "Juan")
        assert i.estado is EstadoIncidencia.ABIERTA and i.asignada_a == "ATENCION_CLIENTE"
        assert isinstance(i.pull_events()[0], ev.IncidenciaAbierta)
        i.resolver("Laura", "atencion_cliente", "Se repone el envío")
        assert i.estado is EstadoIncidencia.RESUELTA and i.resuelta_por == "Laura"
        assert isinstance(i.pull_events()[0], ev.IncidenciaResuelta)
        with pytest.raises(ReglaNegocioException):
            i.resolver("Laura", "ATENCION_CLIENTE", "otra vez")

    @pytest.mark.parametrize("rol", ["REPARTIDOR", "SUPERVISOR", "", None])
    def test_solo_atencion_al_cliente_resuelve(self, rol):
        i = Incidencia.abrir("CB-0000000001", "PERDIDA", "no aparece", "Juan")
        with pytest.raises(ResolucionNoPermitidaException):
            i.resolver("Pedro", rol, "arreglado")
        assert i.estado is EstadoIncidencia.ABIERTA

    def test_resolucion_obligatoria(self):
        i = Incidencia.abrir("CB-0000000001", "DANO", "x", "Juan")
        with pytest.raises(ValorInvalidoException):
            i.resolver("Laura", "ATENCION_CLIENTE", " ")


class TestManifiestoYRuta:
    def test_manifiesto(self):
        m = ManifiestoViaje.crear(Instalacion("A"), Instalacion("B"), ["CB-1", "CB-1", "CB-2"])
        assert m.guias == ["CB-1", "CB-2"] and m.estado is EstadoManifiesto.ABIERTO
        with pytest.raises(ReglaNegocioException):
            m.arribar()
        m.despachar()
        assert isinstance(m.pull_events()[0], ev.ManifiestoDespachado)
        with pytest.raises(ReglaNegocioException):
            m.despachar()
        m.arribar()
        assert m.estado is EstadoManifiesto.ARRIBADO and m.arribado_en is not None

    def test_manifiesto_vacio(self):
        with pytest.raises(ValorInvalidoException):
            ManifiestoViaje.crear(Instalacion("A"), Instalacion("B"), [])
        vacio = ManifiestoViaje("MAN-X", Instalacion("A"), Instalacion("B"))
        with pytest.raises(ValorInvalidoException):
            vacio.despachar()

    def test_ruta(self):
        r = RutaReparto.crear(" Juan ", ["CB-1"])
        assert r.repartidor == "Juan" and r.estado is EstadoRuta.PLANEADA
        with pytest.raises(ReglaNegocioException):
            r.cerrar()
        r.iniciar()
        with pytest.raises(ReglaNegocioException):
            r.iniciar()
        r.cerrar()
        assert [type(e) for e in r.pull_events()] == [ev.RutaIniciada, ev.RutaCerrada]

    def test_ruta_invalida(self):
        with pytest.raises(ValorInvalidoException):
            RutaReparto.crear("", ["CB-1"])
        with pytest.raises(ValorInvalidoException):
            RutaReparto.crear("Juan", [])
