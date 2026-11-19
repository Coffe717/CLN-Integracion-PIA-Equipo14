"""Casos de uso con repositorios en memoria y SQLite (fixture `contenedor`)."""
from datetime import timedelta

import pytest

from src.application.excepciones import NoEncontradoException
from src.domain.excepciones import (
    AutorizacionInvalidaException, EvidenciaObligatoriaException, ReglaNegocioException,
    ResolucionNoPermitidaException, TercerIntentoNoAutorizadoException, TransicionEstadoInvalidaException,
    ValorInvalidoException,
)
from src.domain.valores import ahora

ENVIO = dict(remitente_id="R1", destinatario_nombre="Ana", destinatario_telefono="8112345678",
             origen_calle="Juárez 1", origen_ciudad="Monterrey", destino_calle="Hidalgo 2",
             destino_ciudad="Saltillo", peso_kg=5, largo_cm=30, ancho_cm=30, alto_cm=30,
             nivel_servicio="ESTANDAR")


def recibir(c, **extra):
    return c.recepcion.registrar_recepcion_paquete(**{**ENVIO, **extra})["guia"]


def en_reparto(c, guia):
    c.logistica.clasificar_paquete(guia, "CD MTY")
    c.logistica.despachar_manifiesto_viaje("CD MTY", "CD SLW", [guia])
    c.logistica.registrar_arribo_por_guia(guia, "CD SLW")
    c.entrega.iniciar_ruta_reparto("Juan", [guia])


def test_cotizar(contenedor):
    t = contenedor.cotizacion.cotizar_envio(5, 30, 30, 30, "Monterrey", "Servicio Estándar")
    assert t["total"] == "150.00" and t["texto"] == "$150.00 MXN"
    with pytest.raises(ValorInvalidoException):
        contenedor.cotizacion.cotizar_envio(-5, 30, 30, 30, "Monterrey", "ESTANDAR")


def test_recepcion_genera_guia_y_estado_recibido(contenedor):
    p = contenedor.recepcion.registrar_recepcion_paquete(**ENVIO)
    assert p["estado"] == "RECIBIDO" and p["guia"].startswith("CB-")
    assert p["tarifa"]["zona"] == "REGIONAL" and p["tarifa"]["total"] == "187.50"
    assert contenedor.publicador.historial[-1].nombre == "PaqueteRecibido"


def test_recepcion_reglas(contenedor):
    with pytest.raises(NoEncontradoException):
        recibir(contenedor, remitente_id="NOPE")
    with pytest.raises(ReglaNegocioException):
        recibir(contenedor, remitente_id="R2")
    with pytest.raises(ValorInvalidoException):
        recibir(contenedor, peso_kg=0)
    assert contenedor.consulta.listar_paquetes() == []  # nada se guardó


def test_flujo_completo_hasta_entrega_con_evidencia(contenedor):
    g = recibir(contenedor)
    en_reparto(contenedor, g)
    with pytest.raises(EvidenciaObligatoriaException):
        contenedor.entrega.finalizar_entrega_con_evidencia(g, "Ana")
    assert contenedor.consulta.consultar_linea_de_tiempo(g)["estado"] == "EN_REPARTO"
    p = contenedor.entrega.finalizar_entrega_con_evidencia(g, "Ana", firma="FIRMA", repartidor="Juan")
    assert p["estado"] == "ENTREGADO" and p["tiene_evidencia"]
    ev = contenedor.consulta.consultar_evidencia_entrega(g)
    assert ev["firma"] == "FIRMA" and ev["receptor"] == "Ana"
    rastreo = contenedor.consulta.consultar_linea_de_tiempo(g)
    assert [t["estado"] for t in rastreo["linea_de_tiempo"]][-1] == "ENTREGADO"
    assert contenedor.consulta.listar_notificaciones("ATENCION_CLIENTE")


def test_evidencia_solo_si_hay_entrega(contenedor):
    g = recibir(contenedor)
    with pytest.raises(ReglaNegocioException):
        contenedor.consulta.consultar_evidencia_entrega(g)
    with pytest.raises(NoEncontradoException):
        contenedor.consulta.consultar_linea_de_tiempo("CB-9999999999")


def test_manifiesto_es_atomico(contenedor):
    a, b = recibir(contenedor), recibir(contenedor)
    contenedor.logistica.clasificar_paquete(a, "CD MTY")  # b sigue RECIBIDO
    with pytest.raises(TransicionEstadoInvalidaException):
        contenedor.logistica.despachar_manifiesto_viaje("CD MTY", "CD SLW", [a, b])
    estados = {p["guia"]: p["estado"] for p in contenedor.consulta.listar_paquetes()}
    assert estados[a] == "CLASIFICADO"  # rollback: a no quedó En tránsito


def test_manifiesto_y_arribo_por_manifiesto(contenedor):
    a, b = recibir(contenedor), recibir(contenedor)
    for g in (a, b):
        contenedor.logistica.clasificar_paquete(g, "CD MTY")
    m = contenedor.logistica.despachar_manifiesto_viaje("CD MTY", "CD SLW", [a, b], "Op")
    assert m["estado"] == "DESPACHADO" and len(m["guias"]) == 2
    r = contenedor.logistica.registrar_arribo_centro_destino(m["id"], "CD SLW")
    assert r["estado"] == "ARRIBADO"
    assert {p["estado"] for p in contenedor.consulta.listar_paquetes()} == {"CENTRO_DESTINO"}
    with pytest.raises(NoEncontradoException):
        contenedor.logistica.registrar_arribo_centro_destino("MAN-NOPE", "CD SLW")
    with pytest.raises(ReglaNegocioException):
        contenedor.logistica.registrar_arribo_centro_destino(m["id"], "CD SLW")


def test_ausencias_y_tercer_intento(contenedor):
    g = recibir(contenedor)
    en_reparto(contenedor, g)
    assert contenedor.entrega.registrar_destinatario_ausente(g)["estado"] == "SEGUNDO_INTENTO_PENDIENTE"
    contenedor.entrega.reanudar_reparto(g, "Juan")
    p = contenedor.entrega.registrar_destinatario_ausente(g)
    assert p["requiere_autorizacion_tercer_intento"]
    assert contenedor.consulta.listar_notificaciones("SUPERVISOR")
    contenedor.entrega.reanudar_reparto(g, "Juan")
    with pytest.raises(TercerIntentoNoAutorizadoException):
        contenedor.entrega.registrar_destinatario_ausente(g)
    with pytest.raises(AutorizacionInvalidaException):
        contenedor.entrega.autorizar_tercer_intento(g, "Pedro", "REPARTIDOR")
    assert contenedor.entrega.autorizar_tercer_intento(g, "Rosa", "SUPERVISOR")["tercer_intento_autorizado"]
    assert contenedor.entrega.registrar_destinatario_ausente(g)["estado"] == "RETENIDO_EN_SUCURSAL"


def test_rechazo_devolucion_y_cancelacion(contenedor):
    g, h = recibir(contenedor), recibir(contenedor)
    en_reparto(contenedor, g)
    assert contenedor.entrega.registrar_rechazo_destinatario(g, "No lo quiero")["estado"] == "RECHAZADO_EN_DEVOLUCION"
    assert contenedor.entrega.confirmar_devolucion_a_origen(g, "Emp")["estado"] == "DEVUELTO_A_ORIGEN"
    assert contenedor.entrega.cancelar_envio(h, "error", "Emp")["estado"] == "CANCELADO"
    with pytest.raises(TransicionEstadoInvalidaException):
        contenedor.entrega.finalizar_entrega_con_evidencia(h, "Ana", firma="F")


def test_direccion_incorrecta_ticket_y_correccion(contenedor):
    g = recibir(contenedor)
    en_reparto(contenedor, g)
    t = contenedor.incidencias.reportar_direccion_incorrecta(g, "Juan", "no existe el número")
    assert t["tipo"] == "DIRECCION_INCORRECTA" and t["asignada_a"] == "ATENCION_CLIENTE"
    assert contenedor.consulta.listar_notificaciones("ATENCION_CLIENTE")
    with pytest.raises(ResolucionNoPermitidaException):
        contenedor.incidencias.resolver_incidencia(t["id"], "Juan", "REPARTIDOR", "lo arreglo yo")
    with pytest.raises(ValorInvalidoException):
        contenedor.incidencias.resolver_incidencia(t["id"], "Laura", "ATENCION_CLIENTE", "ok")
    r = contenedor.incidencias.resolver_incidencia(t["id"], "Laura", "ATENCION_CLIENTE", "Dirección confirmada",
                                                   "Hidalgo 22", "Saltillo")
    assert r["estado"] == "RESUELTA"
    p = contenedor.entrega.reanudar_reparto(g, "Juan")
    assert p["estado"] == "EN_REPARTO" and p["destino"]["calle"] == "Hidalgo 22"
    assert contenedor.incidencias.listar_incidencias("ABIERTA") == []
    assert len(contenedor.incidencias.listar_incidencias(guia=g)) == 1
    with pytest.raises(NoEncontradoException):
        contenedor.incidencias.resolver_incidencia("INC-NOPE", "Laura", "ATENCION_CLIENTE", "x")


@pytest.mark.parametrize("tipo", ["DANO", "PERDIDA"])
def test_incidencia_mayor_se_escala(contenedor, tipo):
    g = recibir(contenedor)
    en_reparto(contenedor, g)
    t = contenedor.incidencias.reportar_incidencia_mayor(g, tipo, "daño grave", "Juan")
    assert t["tipo"] == tipo
    assert contenedor.consulta.consultar_linea_de_tiempo(g)["estado"] == "RETENIDO_POR_INCIDENCIA"
    r = contenedor.incidencias.resolver_incidencia(t["id"], "Laura", "ATENCION_CLIENTE", "Se repone")
    assert r["estado"] == "RESUELTA"


@pytest.mark.parametrize("tipo", ["ROBO", "DIRECCION_INCORRECTA", ""])
def test_incidencia_mayor_tipo_invalido(contenedor, tipo):
    g = recibir(contenedor)
    en_reparto(contenedor, g)
    with pytest.raises(ValorInvalidoException):
        contenedor.incidencias.reportar_incidencia_mayor(g, tipo, "x", "Juan")


def test_monitoreo_estancados(contenedor):
    g = recibir(contenedor)
    assert contenedor.monitoreo.detectar_paquetes_estancados(24) == []
    futuro = ahora() + timedelta(hours=50)
    alertas = contenedor.monitoreo.detectar_paquetes_estancados(24, futuro, notificar=True)
    assert alertas[0]["guia"] == g and alertas[0]["horas_estancado"] > 49
    assert any("estancado" in n["mensaje"] for n in contenedor.consulta.listar_notificaciones("SUPERVISOR"))
    for malo in ("abc", -1):
        with pytest.raises(ValorInvalidoException):
            contenedor.monitoreo.detectar_paquetes_estancados(malo)


def test_listados_y_remitentes(contenedor):
    recibir(contenedor)
    recibir(contenedor, remitente_id="R3")
    assert len(contenedor.consulta.listar_paquetes(remitente_id="R3")) == 1
    assert contenedor.consulta.listar_paquetes(estado="ENTREGADO") == []
    assert {r["id"] for r in contenedor.consulta.listar_remitentes()} == {"R1", "R2", "R3"}
    assert contenedor.consulta.listar_notificaciones("NADIE") == []
