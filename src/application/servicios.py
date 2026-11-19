"""Service Layer: casos de uso de CargoBox.

Regla de oro: los servicios NO deciden reglas de negocio. Cargan el agregado,
invocan un método del dominio, guardan y publican los eventos.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from src.application import dto
from src.application.eventos import PublicadorEventos
from src.application.excepciones import NoEncontradoException
from src.application.puertos import (
    IGeneradorGuia,
    IIncidenciaRepository,
    IManifiestoRepository,
    INotificador,
    IPaqueteRepository,
    IRemitenteRepository,
    IRutaRepository,
    IUnitOfWork,
)
from src.domain import eventos as ev
from src.domain.especificaciones import PaqueteEstancadoSpec, PuedeEnviarSpec
from src.domain.estado import ETIQUETAS
from src.domain.excepciones import ReglaNegocioException, ValorInvalidoException
from src.domain.incidencia import Incidencia, TipoIncidencia
from src.domain.manifiesto import ManifiestoViaje, RutaReparto
from src.domain.paquete import Paquete
from src.domain.tabulador import CalculadoraTarifa
from src.domain.valores import (
    AutorizacionReintento,
    Contacto,
    Dimensiones,
    Direccion,
    EvidenciaRecepcion,
    Instalacion,
    NivelServicio,
    Peso,
    ahora,
)

SUCURSAL_POR_DEFECTO = "Sucursal Monterrey Centro"


class _ServicioBase:
    def __init__(self, uow: IUnitOfWork, publicador: PublicadorEventos):
        self._uow = uow
        self._publicador = publicador


def _obtener_paquete(repo: IPaqueteRepository, guia: str) -> Paquete:
    paquete = repo.obtener_por_guia((guia or "").strip().upper())
    if paquete is None:
        raise NoEncontradoException(f"No existe un paquete con la guía {guia}")
    return paquete


# ------------------------------------------------------------------ cotización / recepción
class CotizacionService:
    def __init__(self, calculadora: CalculadoraTarifa):
        self._calculadora = calculadora

    def cotizar_envio(self, peso_kg, largo_cm, ancho_cm, alto_cm, destino_ciudad: str,
                      nivel_servicio: str) -> dict:
        peso = Peso(peso_kg)
        dimensiones = Dimensiones(largo_cm, ancho_cm, alto_cm)
        tarifa = self._calculadora.calcular(peso, dimensiones, destino_ciudad,
                                            NivelServicio.desde(nivel_servicio))
        return dto.tarifa_a_dto(tarifa)


class RecepcionService(_ServicioBase):
    def __init__(self, paquetes: IPaqueteRepository, remitentes: IRemitenteRepository,
                 calculadora: CalculadoraTarifa, generador: IGeneradorGuia,
                 uow: IUnitOfWork, publicador: PublicadorEventos):
        super().__init__(uow, publicador)
        self._paquetes = paquetes
        self._remitentes = remitentes
        self._calculadora = calculadora
        self._generador = generador

    def registrar_recepcion_paquete(self, remitente_id: str, destinatario_nombre: str,
                                    destinatario_telefono: str, origen_calle: str, origen_ciudad: str,
                                    destino_calle: str, destino_ciudad: str, peso_kg, largo_cm, ancho_cm,
                                    alto_cm, nivel_servicio: str, contenido: str = "",
                                    empleado: str = "", sucursal: str = SUCURSAL_POR_DEFECTO) -> dict:
        with self._uow:
            remitente = self._remitentes.obtener(remitente_id)
            if remitente is None:
                raise NoEncontradoException(f"No existe el remitente {remitente_id}")
            if not PuedeEnviarSpec().is_satisfied_by(remitente):
                raise ReglaNegocioException("El remitente está inactivo y no puede registrar envíos")
            paquete = Paquete.recibir(
                guia=self._generador.generar(),
                remitente_id=remitente_id,
                destinatario=Contacto(destinatario_nombre, destinatario_telefono),
                origen=Direccion(origen_calle, origen_ciudad),
                destino=Direccion(destino_calle, destino_ciudad),
                peso=Peso(peso_kg),
                dimensiones=Dimensiones(largo_cm, ancho_cm, alto_cm),
                nivel=NivelServicio.desde(nivel_servicio),
                calculadora=self._calculadora,
                sucursal=Instalacion(sucursal),
                empleado=empleado,
                contenido=contenido,
            )
            self._paquetes.guardar(paquete)
            eventos = paquete.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.paquete_a_dto(paquete)


# ------------------------------------------------------------------ operación logística
class OperacionLogisticaService(_ServicioBase):
    def __init__(self, paquetes: IPaqueteRepository, manifiestos: IManifiestoRepository,
                 uow: IUnitOfWork, publicador: PublicadorEventos):
        super().__init__(uow, publicador)
        self._paquetes = paquetes
        self._manifiestos = manifiestos

    def clasificar_paquete(self, guia: str, instalacion: str, operador: str = "") -> dict:
        with self._uow:
            paquete = _obtener_paquete(self._paquetes, guia)
            paquete.clasificar(Instalacion(instalacion), operador)
            self._paquetes.guardar(paquete)
            eventos = paquete.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.paquete_a_dto(paquete)

    def despachar_manifiesto_viaje(self, origen: str, destino: str, guias: List[str],
                                   operador: str = "") -> dict:
        with self._uow:
            manifiesto = ManifiestoViaje.crear(Instalacion(origen), Instalacion(destino), guias)
            eventos = []
            for guia in manifiesto.guias:
                paquete = _obtener_paquete(self._paquetes, guia)
                paquete.marcar_en_transito(manifiesto.id, operador)
                self._paquetes.guardar(paquete)
                eventos += paquete.pull_events()
            manifiesto.despachar()
            self._manifiestos.guardar(manifiesto)
            eventos += manifiesto.pull_events()
        self._publicador.publicar_todos(eventos)
        return self._manifiesto_dto(manifiesto)

    def registrar_arribo_centro_destino(self, manifiesto_id: str, instalacion: str,
                                        operador: str = "") -> dict:
        with self._uow:
            manifiesto = self._manifiestos.obtener(manifiesto_id)
            if manifiesto is None:
                raise NoEncontradoException(f"No existe el manifiesto {manifiesto_id}")
            manifiesto.arribar()
            eventos = []
            for guia in manifiesto.guias:
                paquete = _obtener_paquete(self._paquetes, guia)
                paquete.marcar_centro_destino(Instalacion(instalacion), operador)
                self._paquetes.guardar(paquete)
                eventos += paquete.pull_events()
            self._manifiestos.guardar(manifiesto)
            eventos += manifiesto.pull_events()
        self._publicador.publicar_todos(eventos)
        return self._manifiesto_dto(manifiesto)

    def registrar_arribo_por_guia(self, guia: str, instalacion: str, operador: str = "") -> dict:
        """Arribo individual (escaneo de la guía en la bahía de llegada)."""
        with self._uow:
            paquete = _obtener_paquete(self._paquetes, guia)
            paquete.marcar_centro_destino(Instalacion(instalacion), operador)
            self._paquetes.guardar(paquete)
            eventos = paquete.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.paquete_a_dto(paquete)

    @staticmethod
    def _manifiesto_dto(m: ManifiestoViaje) -> dict:
        return {
            "id": m.id, "origen": m.origen.nombre, "destino": m.destino.nombre, "guias": m.guias,
            "estado": m.estado.value,
            "despachado_en": m.despachado_en.isoformat() if m.despachado_en else None,
            "arribado_en": m.arribado_en.isoformat() if m.arribado_en else None,
        }


# ------------------------------------------------------------------ entrega y excepciones de entrega
class EntregaService(_ServicioBase):
    def __init__(self, paquetes: IPaqueteRepository, rutas: IRutaRepository,
                 uow: IUnitOfWork, publicador: PublicadorEventos):
        super().__init__(uow, publicador)
        self._paquetes = paquetes
        self._rutas = rutas

    def _aplicar(self, guia: str, accion) -> dict:
        with self._uow:
            paquete = _obtener_paquete(self._paquetes, guia)
            accion(paquete)
            self._paquetes.guardar(paquete)
            eventos = paquete.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.paquete_a_dto(paquete)

    def iniciar_ruta_reparto(self, repartidor: str, guias: List[str]) -> dict:
        with self._uow:
            ruta = RutaReparto.crear(repartidor, guias)
            eventos = []
            for guia in ruta.guias:
                paquete = _obtener_paquete(self._paquetes, guia)
                paquete.marcar_en_reparto(ruta.repartidor)
                self._paquetes.guardar(paquete)
                eventos += paquete.pull_events()
            ruta.iniciar()
            self._rutas.guardar(ruta)
            eventos += ruta.pull_events()
        self._publicador.publicar_todos(eventos)
        return {"id": ruta.id, "repartidor": ruta.repartidor, "guias": ruta.guias,
                "estado": ruta.estado.value}

    def finalizar_entrega_con_evidencia(self, guia: str, receptor: str = "", firma: Optional[str] = None,
                                        foto: Optional[str] = None, repartidor: str = "") -> dict:
        tiene_evidencia = bool((firma or "").strip() or (foto or "").strip())
        evidencia = EvidenciaRecepcion(receptor, firma, foto) if tiene_evidencia else None
        return self._aplicar(guia, lambda p: p.finalizar_entrega(evidencia, repartidor))

    def registrar_destinatario_ausente(self, guia: str, repartidor: str = "") -> dict:
        return self._aplicar(guia, lambda p: p.registrar_ausencia(repartidor))

    def autorizar_tercer_intento(self, guia: str, autorizador: str, rol: str) -> dict:
        autorizacion = AutorizacionReintento(autorizador, rol)
        return self._aplicar(guia, lambda p: p.autorizar_tercer_intento(autorizacion))

    def registrar_rechazo_destinatario(self, guia: str, motivo: str, repartidor: str = "") -> dict:
        return self._aplicar(guia, lambda p: p.registrar_rechazo(motivo, repartidor))

    def confirmar_devolucion_a_origen(self, guia: str, empleado: str = "",
                                      sucursal: str = SUCURSAL_POR_DEFECTO) -> dict:
        return self._aplicar(guia, lambda p: p.completar_devolucion(Instalacion(sucursal), empleado))

    def cancelar_envio(self, guia: str, motivo: str = "", actor: str = "") -> dict:
        return self._aplicar(guia, lambda p: p.cancelar(motivo, actor))

    def reanudar_reparto(self, guia: str, repartidor: str = "") -> dict:
        """Reintento tras corregir dirección, resolver incidencia o autorizar un reintento."""
        return self._aplicar(guia, lambda p: p.marcar_en_reparto(repartidor))


# ------------------------------------------------------------------ incidencias
class IncidenciaService(_ServicioBase):
    def __init__(self, paquetes: IPaqueteRepository, incidencias: IIncidenciaRepository,
                 uow: IUnitOfWork, publicador: PublicadorEventos):
        super().__init__(uow, publicador)
        self._paquetes = paquetes
        self._incidencias = incidencias

    def reportar_direccion_incorrecta(self, guia: str, repartidor: str = "", comentario: str = "") -> dict:
        with self._uow:
            paquete = _obtener_paquete(self._paquetes, guia)
            paquete.pausar_por_direccion_incorrecta(comentario, repartidor)
            incidencia = Incidencia.abrir(str(paquete.guia), TipoIncidencia.DIRECCION_INCORRECTA,
                                          comentario or "El repartidor no localiza el domicilio", repartidor)
            self._paquetes.guardar(paquete)
            self._incidencias.guardar(incidencia)
            eventos = paquete.pull_events() + incidencia.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.incidencia_a_dto(incidencia)

    def reportar_incidencia_mayor(self, guia: str, tipo: str, descripcion: str = "",
                                  repartidor: str = "") -> dict:
        try:
            tipo_inc = TipoIncidencia((tipo or "").strip().upper())
        except ValueError:
            raise ValorInvalidoException("El tipo debe ser DANO o PERDIDA") from None
        if tipo_inc is TipoIncidencia.DIRECCION_INCORRECTA:
            raise ValorInvalidoException("El tipo debe ser DANO o PERDIDA")
        with self._uow:
            paquete = _obtener_paquete(self._paquetes, guia)
            paquete.retener_por_incidencia(tipo_inc.value, descripcion, repartidor)
            incidencia = Incidencia.abrir(str(paquete.guia), tipo_inc, descripcion, repartidor)
            self._paquetes.guardar(paquete)
            self._incidencias.guardar(incidencia)
            eventos = paquete.pull_events() + incidencia.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.incidencia_a_dto(incidencia)

    def resolver_incidencia(self, incidencia_id: str, agente: str, rol: str, resolucion: str,
                            nueva_calle: str = "", nueva_ciudad: str = "") -> dict:
        with self._uow:
            incidencia = self._incidencias.obtener(incidencia_id)
            if incidencia is None:
                raise NoEncontradoException(f"No existe la incidencia {incidencia_id}")
            incidencia.resolver(agente, rol, resolucion)
            if incidencia.tipo is TipoIncidencia.DIRECCION_INCORRECTA:
                paquete = _obtener_paquete(self._paquetes, incidencia.guia)
                paquete.corregir_direccion(Direccion(nueva_calle, nueva_ciudad), agente)
                self._paquetes.guardar(paquete)
            self._incidencias.guardar(incidencia)
            eventos = incidencia.pull_events()
        self._publicador.publicar_todos(eventos)
        return dto.incidencia_a_dto(incidencia)

    def listar_incidencias(self, estado: Optional[str] = None, guia: Optional[str] = None) -> List[dict]:
        return [dto.incidencia_a_dto(i) for i in self._incidencias.listar(estado, guia)]


# ------------------------------------------------------------------ monitoreo y consulta
class MonitoreoService(_ServicioBase):
    def __init__(self, paquetes: IPaqueteRepository, uow: IUnitOfWork, publicador: PublicadorEventos):
        super().__init__(uow, publicador)
        self._paquetes = paquetes

    def detectar_paquetes_estancados(self, umbral_horas: float = 24, momento: Optional[datetime] = None,
                                     notificar: bool = False) -> List[dict]:
        """BR002: lista paquetes sin cambios por más del umbral. `notificar` avisa al supervisor."""
        try:
            umbral = float(umbral_horas)
        except (TypeError, ValueError):
            raise ValorInvalidoException("El umbral debe ser un número de horas") from None
        if umbral < 0:
            raise ValorInvalidoException("El umbral no puede ser negativo")
        momento = momento or ahora()
        spec = PaqueteEstancadoSpec(umbral, momento)
        alertas = []
        eventos = []
        with self._uow:
            for paquete in self._paquetes.listar():
                if spec.is_satisfied_by(paquete):
                    horas = round(paquete.horas_sin_actualizacion(momento), 1)
                    alertas.append({"guia": str(paquete.guia), "ultimo_estado": paquete.estado.value,
                                    "ultimo_estado_etiqueta": ETIQUETAS[paquete.estado],
                                    "horas_estancado": horas,
                                    "ultima_actualizacion": paquete.actualizado_en.isoformat()})
                    eventos.append(ev.PaqueteEstancadoDetectado(
                        str(paquete.guia), momento, {"horas": horas, "estado": paquete.estado.value}))
        if notificar:
            self._publicador.publicar_todos(eventos)
        alertas.sort(key=lambda a: -a["horas_estancado"])
        return alertas


class ConsultaRastreoService:
    """Solo lectura (queries): rastreo, evidencia, listados y notificaciones."""

    def __init__(self, paquetes: IPaqueteRepository, incidencias: IIncidenciaRepository,
                 remitentes: IRemitenteRepository, notificador: INotificador):
        self._paquetes = paquetes
        self._incidencias = incidencias
        self._remitentes = remitentes
        self._notificador = notificador

    def consultar_linea_de_tiempo(self, guia: str) -> dict:
        paquete = _obtener_paquete(self._paquetes, guia)
        resultado = dto.paquete_a_dto(paquete)
        resultado["linea_de_tiempo"] = dto.linea_de_tiempo(paquete)
        resultado["incidencias"] = [dto.incidencia_a_dto(i)
                                    for i in self._incidencias.listar(guia=str(paquete.guia))]
        resultado["evidencia"] = dto.evidencia_a_dto(paquete.evidencia)
        return resultado

    def consultar_evidencia_entrega(self, guia: str) -> dict:
        paquete = _obtener_paquete(self._paquetes, guia)
        if paquete.evidencia is None:
            raise ReglaNegocioException("El paquete aún no tiene evidencia de entrega")
        resultado = dto.evidencia_a_dto(paquete.evidencia, con_imagenes=True)
        resultado.update({"guia": str(paquete.guia), "estado": paquete.estado.value})
        return resultado

    def listar_paquetes(self, estado: Optional[str] = None, remitente_id: Optional[str] = None) -> List[dict]:
        paquetes = self._paquetes.listar(estado, remitente_id)
        return [dto.paquete_a_dto(p) for p in paquetes]

    def listar_remitentes(self) -> List[dict]:
        return [{"id": r.id, "nombre": r.nombre, "activo": r.activo, "preferente": r.preferente,
                 "ciudad": r.ciudad} for r in self._remitentes.listar()]

    def listar_notificaciones(self, destino: Optional[str] = None) -> List[dict]:
        return self._notificador.listar(destino)
