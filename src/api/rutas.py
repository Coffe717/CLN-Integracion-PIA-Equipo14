"""Endpoints REST de CargoBox (controllers): solo traducen HTTP <-> casos de uso."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from src.application.excepciones import SolicitudInvalidaException

api = Blueprint("api", __name__, url_prefix="/api/v1")


def _c():
    return current_app.config["CONTENEDOR"]


def _cuerpo() -> dict:
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise SolicitudInvalidaException("El cuerpo debe ser un JSON válido (objeto)")
    return datos


def _requeridos(datos: dict, *campos: str) -> None:
    faltan = [c for c in campos if datos.get(c) in (None, "")]
    if faltan:
        raise SolicitudInvalidaException("Faltan campos obligatorios: " + ", ".join(faltan))


def _opcional() -> dict:
    """Cuerpo opcional (acciones sin datos obligatorios)."""
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


# ------------------------------------------------------------------ sistema y catálogos
@api.get("/health")
def health():
    return jsonify({"estado": "ok", "servicio": "cargobox"})


@api.get("/remitentes")
def remitentes():
    return jsonify(_c().consulta.listar_remitentes())


# ------------------------------------------------------------------ cotización y recepción
@api.post("/cotizaciones")
def cotizar():
    d = _cuerpo()
    _requeridos(d, "peso_kg", "largo_cm", "ancho_cm", "alto_cm", "destino_ciudad", "nivel_servicio")
    return jsonify(_c().cotizacion.cotizar_envio(
        d["peso_kg"], d["largo_cm"], d["ancho_cm"], d["alto_cm"], d["destino_ciudad"], d["nivel_servicio"]))


@api.post("/paquetes")
def registrar_paquete():
    d = _cuerpo()
    _requeridos(d, "remitente_id", "destinatario_nombre", "destino_calle", "destino_ciudad", "peso_kg",
                "largo_cm", "ancho_cm", "alto_cm", "nivel_servicio")
    paquete = _c().recepcion.registrar_recepcion_paquete(
        d["remitente_id"], d["destinatario_nombre"], d.get("destinatario_telefono", ""),
        d.get("origen_calle") or "Sucursal CargoBox", d.get("origen_ciudad") or "Monterrey",
        d["destino_calle"], d["destino_ciudad"], d["peso_kg"], d["largo_cm"], d["ancho_cm"], d["alto_cm"],
        d["nivel_servicio"], d.get("contenido", ""), d.get("empleado", ""))
    return jsonify(paquete), 201


@api.get("/paquetes")
def listar_paquetes():
    return jsonify(_c().consulta.listar_paquetes(request.args.get("estado"), request.args.get("remitente_id")))


@api.get("/paquetes/<guia>")
def obtener_paquete(guia):
    return jsonify(_c().consulta.consultar_linea_de_tiempo(guia))


@api.get("/paquetes/<guia>/rastreo")
def rastreo(guia):
    return jsonify(_c().consulta.consultar_linea_de_tiempo(guia))


@api.get("/paquetes/<guia>/evidencia")
def evidencia(guia):
    return jsonify(_c().consulta.consultar_evidencia_entrega(guia))


# ------------------------------------------------------------------ operación logística
@api.post("/paquetes/<guia>/clasificar")
def clasificar(guia):
    d = _cuerpo()
    _requeridos(d, "instalacion")
    return jsonify(_c().logistica.clasificar_paquete(guia, d["instalacion"], d.get("operador", "")))


@api.post("/paquetes/<guia>/arribo")
def arribo_guia(guia):
    d = _cuerpo()
    _requeridos(d, "instalacion")
    return jsonify(_c().logistica.registrar_arribo_por_guia(guia, d["instalacion"], d.get("operador", "")))


@api.post("/manifiestos")
def despachar_manifiesto():
    d = _cuerpo()
    _requeridos(d, "origen", "destino", "guias")
    if not isinstance(d["guias"], list):
        raise SolicitudInvalidaException("guias debe ser una lista")
    return jsonify(_c().logistica.despachar_manifiesto_viaje(
        d["origen"], d["destino"], d["guias"], d.get("operador", ""))), 201


@api.post("/manifiestos/<manifiesto_id>/arribo")
def arribo_manifiesto(manifiesto_id):
    d = _cuerpo()
    _requeridos(d, "instalacion")
    return jsonify(_c().logistica.registrar_arribo_centro_destino(
        manifiesto_id, d["instalacion"], d.get("operador", "")))


# ------------------------------------------------------------------ reparto y entrega
@api.post("/rutas")
def iniciar_ruta():
    d = _cuerpo()
    _requeridos(d, "repartidor", "guias")
    if not isinstance(d["guias"], list):
        raise SolicitudInvalidaException("guias debe ser una lista")
    return jsonify(_c().entrega.iniciar_ruta_reparto(d["repartidor"], d["guias"])), 201


@api.post("/paquetes/<guia>/entrega")
def entregar(guia):
    d = _cuerpo()
    return jsonify(_c().entrega.finalizar_entrega_con_evidencia(
        guia, d.get("receptor", ""), d.get("firma"), d.get("foto"), d.get("repartidor", "")))


@api.post("/paquetes/<guia>/ausencia")
def ausencia(guia):
    return jsonify(_c().entrega.registrar_destinatario_ausente(guia, _opcional().get("repartidor", "")))


@api.post("/paquetes/<guia>/autorizar-reintento")
def autorizar(guia):
    d = _cuerpo()
    _requeridos(d, "autorizador", "rol")
    return jsonify(_c().entrega.autorizar_tercer_intento(guia, d["autorizador"], d["rol"]))


@api.post("/paquetes/<guia>/rechazo")
def rechazo(guia):
    d = _cuerpo()
    return jsonify(_c().entrega.registrar_rechazo_destinatario(guia, d.get("motivo", ""), d.get("repartidor", "")))


@api.post("/paquetes/<guia>/devolucion")
def devolucion(guia):
    return jsonify(_c().entrega.confirmar_devolucion_a_origen(guia, _opcional().get("empleado", "")))


@api.post("/paquetes/<guia>/cancelar")
def cancelar(guia):
    d = _opcional()
    return jsonify(_c().entrega.cancelar_envio(guia, d.get("motivo", ""), d.get("actor", "")))


@api.post("/paquetes/<guia>/reanudar")
def reanudar(guia):
    return jsonify(_c().entrega.reanudar_reparto(guia, _opcional().get("repartidor", "")))


# ------------------------------------------------------------------ incidencias
@api.post("/paquetes/<guia>/direccion-incorrecta")
def direccion_incorrecta(guia):
    d = _opcional()
    return jsonify(_c().incidencias.reportar_direccion_incorrecta(
        guia, d.get("repartidor", ""), d.get("comentario", ""))), 201


@api.post("/paquetes/<guia>/incidencia-mayor")
def incidencia_mayor(guia):
    d = _cuerpo()
    _requeridos(d, "tipo")
    return jsonify(_c().incidencias.reportar_incidencia_mayor(
        guia, d["tipo"], d.get("descripcion", ""), d.get("repartidor", ""))), 201


@api.get("/incidencias")
def listar_incidencias():
    return jsonify(_c().incidencias.listar_incidencias(request.args.get("estado"), request.args.get("guia")))


@api.post("/incidencias/<incidencia_id>/resolver")
def resolver(incidencia_id):
    d = _cuerpo()
    _requeridos(d, "agente", "rol", "resolucion")
    return jsonify(_c().incidencias.resolver_incidencia(
        incidencia_id, d["agente"], d["rol"], d["resolucion"], d.get("nueva_calle", ""), d.get("nueva_ciudad", "")))


# ------------------------------------------------------------------ monitoreo y avisos
@api.get("/alertas")
def alertas():
    umbral = request.args.get("umbral_horas", current_app.config["UMBRAL_HORAS"])
    return jsonify(_c().monitoreo.detectar_paquetes_estancados(umbral))


@api.post("/alertas/ejecutar")
def ejecutar_monitoreo():
    d = _opcional()
    umbral = d.get("umbral_horas", current_app.config["UMBRAL_HORAS"])
    return jsonify(_c().monitoreo.detectar_paquetes_estancados(umbral, notificar=True))


@api.get("/notificaciones")
def notificaciones():
    return jsonify(_c().consulta.listar_notificaciones(request.args.get("destino")))

