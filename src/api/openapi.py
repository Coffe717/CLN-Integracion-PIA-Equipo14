"""Especificación OpenAPI 3.0 de la API, generada desde una tabla de endpoints.

Se sirve en /openapi.json y se visualiza en /docs (Swagger UI).
Un test verifica que cada ruta de Flask esté documentada aquí.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

ERRORES = {
    "400": "Solicitud mal formada o faltan campos",
    "403": "Rol no permitido para la acción",
    "404": "No existe el recurso (guía, incidencia, manifiesto...)",
    "409": "Conflicto: transición de estado inválida o regla de negocio",
    "422": "Dato inválido o regla de validación (p. ej. evidencia obligatoria)",
}

# (método, ruta, etiqueta, resumen, campos del cuerpo (nombre, tipo, requerido), códigos de éxito, errores)
Campo = Tuple[str, str, bool]
ENDPOINTS: List[Tuple[str, str, str, str, List[Campo], str, List[str]]] = [
    ("get", "/health", "Sistema", "Estado del servicio", [], "200", []),
    ("get", "/remitentes", "Catálogos", "Lista de remitentes", [], "200", []),
    ("post", "/cotizaciones", "Sucursal", "Cotizar un envío (BR005, historias 1 y 15)",
     [("peso_kg", "number", True), ("largo_cm", "number", True), ("ancho_cm", "number", True),
      ("alto_cm", "number", True), ("destino_ciudad", "string", True), ("nivel_servicio", "string", True)],
     "200", ["400", "422"]),
    ("post", "/paquetes", "Sucursal", "Registrar la recepción y generar guía única (BR006, BR007)",
     [("remitente_id", "string", True), ("destinatario_nombre", "string", True),
      ("destinatario_telefono", "string", False), ("origen_calle", "string", False),
      ("origen_ciudad", "string", False), ("destino_calle", "string", True),
      ("destino_ciudad", "string", True), ("peso_kg", "number", True), ("largo_cm", "number", True),
      ("ancho_cm", "number", True), ("alto_cm", "number", True), ("nivel_servicio", "string", True),
      ("contenido", "string", False), ("empleado", "string", False)],
     "201", ["400", "404", "409", "422"]),
    ("get", "/paquetes", "Rastreo", "Listar paquetes (filtros: estado, remitente_id)", [], "200", []),
    ("get", "/paquetes/{guia}", "Rastreo", "Detalle y línea de tiempo de una guía (BR001)", [], "200", ["404"]),
    ("get", "/paquetes/{guia}/rastreo", "Rastreo", "Línea de tiempo completa con incidencias y evidencia",
     [], "200", ["404"]),
    ("get", "/paquetes/{guia}/evidencia", "Auditoría", "Evidencia de entrega con firma y foto (BR004)",
     [], "200", ["404", "409"]),
    ("post", "/paquetes/{guia}/clasificar", "Centro de distribución", "Clasificar el paquete (BR008)",
     [("instalacion", "string", True), ("operador", "string", False)], "200", ["400", "404", "409"]),
    ("post", "/paquetes/{guia}/arribo", "Centro de distribución", "Registrar arribo a centro destino (BR010)",
     [("instalacion", "string", True), ("operador", "string", False)], "200", ["400", "404", "409"]),
    ("post", "/manifiestos", "Centro de distribución", "Crear y despachar un manifiesto de viaje (BR009)",
     [("origen", "string", True), ("destino", "string", True), ("guias", "array", True),
      ("operador", "string", False)], "201", ["400", "404", "409", "422"]),
    ("post", "/manifiestos/{manifiesto_id}/arribo", "Centro de distribución",
     "Registrar el arribo de todo un manifiesto (BR010)",
     [("instalacion", "string", True), ("operador", "string", False)], "200", ["400", "404", "409"]),
    ("post", "/rutas", "Reparto", "Iniciar la ruta del repartidor: paquetes En reparto (BR011)",
     [("repartidor", "string", True), ("guias", "array", True)], "201", ["400", "404", "409", "422"]),
    ("post", "/paquetes/{guia}/entrega", "Reparto", "Finalizar entrega con evidencia obligatoria (BR012)",
     [("receptor", "string", False), ("firma", "string", False), ("foto", "string", False),
      ("repartidor", "string", False)], "200", ["404", "409", "422"]),
    ("post", "/paquetes/{guia}/ausencia", "Reparto", "Destinatario ausente: 2.º intento automático (BR014)",
     [("repartidor", "string", False)], "200", ["404", "409"]),
    ("post", "/paquetes/{guia}/autorizar-reintento", "Atención al cliente",
     "Autorizar el tercer intento (supervisor / atención) (BR014)",
     [("autorizador", "string", True), ("rol", "string", True)], "200", ["400", "403", "404", "409"]),
    ("post", "/paquetes/{guia}/rechazo", "Reparto", "Registrar rechazo y devolver a origen",
     [("motivo", "string", True), ("repartidor", "string", False)], "200", ["404", "409", "422"]),
    ("post", "/paquetes/{guia}/devolucion", "Sucursal", "Confirmar devolución a la sucursal de origen",
     [("empleado", "string", False)], "200", ["404", "409"]),
    ("post", "/paquetes/{guia}/cancelar", "Sucursal", "Cancelar un envío recién recibido",
     [("motivo", "string", False), ("actor", "string", False)], "200", ["404", "409"]),
    ("post", "/paquetes/{guia}/reanudar", "Reparto", "Reintentar la entrega tras una pausa o autorización",
     [("repartidor", "string", False)], "200", ["404", "409"]),
    ("post", "/paquetes/{guia}/direccion-incorrecta", "Reparto", "Excepción: dirección incorrecta (BR013)",
     [("repartidor", "string", False), ("comentario", "string", False)], "201", ["404", "409"]),
    ("post", "/paquetes/{guia}/incidencia-mayor", "Reparto", "Escalar daño o pérdida (BR003)",
     [("tipo", "string", True), ("descripcion", "string", False), ("repartidor", "string", False)],
     "201", ["400", "404", "409", "422"]),
    ("get", "/incidencias", "Atención al cliente", "Bandeja de incidencias (filtros: estado, guia)", [], "200", []),
    ("post", "/incidencias/{incidencia_id}/resolver", "Atención al cliente",
     "Resolver una incidencia (solo Atención al cliente) (BR003)",
     [("agente", "string", True), ("rol", "string", True), ("resolucion", "string", True),
      ("nueva_calle", "string", False), ("nueva_ciudad", "string", False)],
     "200", ["400", "403", "404", "409", "422"]),
    ("get", "/alertas", "Supervisor", "Paquetes estancados (BR002), parámetro umbral_horas", [], "200", ["422"]),
    ("post", "/alertas/ejecutar", "Supervisor", "Ejecutar el monitoreo y avisar al supervisor",
     [("umbral_horas", "number", False)], "200", ["422"]),
    ("get", "/notificaciones", "Supervisor", "Avisos para Atención al cliente / Supervisor", [], "200", []),
]


def _parametros(ruta: str) -> List[dict]:
    parametros = []
    for segmento in ruta.split("/"):
        if segmento.startswith("{"):
            parametros.append({"name": segmento.strip("{}"), "in": "path", "required": True,
                               "schema": {"type": "string"}})
    return parametros


def _cuerpo(campos: List[Campo]) -> Optional[dict]:
    if not campos:
        return None
    propiedades: Dict[str, dict] = {}
    for nombre, tipo, _ in campos:
        propiedades[nombre] = {"type": "array", "items": {"type": "string"}} if tipo == "array" else {"type": tipo}
    esquema: dict = {"type": "object", "properties": propiedades}
    requeridos = [n for n, _, req in campos if req]
    if requeridos:
        esquema["required"] = requeridos
    return {"required": bool(requeridos), "content": {"application/json": {"schema": esquema}}}


def construir_openapi() -> dict:
    paths: Dict[str, dict] = {}
    for metodo, ruta, etiqueta, resumen, campos, exito, errores in ENDPOINTS:
        operacion: dict = {"tags": [etiqueta], "summary": resumen, "parameters": _parametros(ruta),
                           "responses": {exito: {"description": "Operación exitosa"}}}
        if metodo == "get" and ruta in ("/paquetes", "/incidencias", "/notificaciones"):
            filtros = {"/paquetes": ["estado", "remitente_id"], "/incidencias": ["estado", "guia"],
                       "/notificaciones": ["destino"]}[ruta]
            operacion["parameters"] += [{"name": f, "in": "query", "schema": {"type": "string"}} for f in filtros]
        if ruta == "/alertas":
            operacion["parameters"].append({"name": "umbral_horas", "in": "query", "schema": {"type": "number"}})
        cuerpo = _cuerpo(campos)
        if cuerpo:
            operacion["requestBody"] = cuerpo
        for codigo in errores:
            operacion["responses"][codigo] = {
                "description": ERRORES[codigo],
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}}
        paths.setdefault("/api/v1" + ruta, {})[metodo] = operacion
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "CargoBox API",
            "version": "1.0.0",
            "description": ("API de gestión y rastreo de envíos CargoBox (PIA - Componentes de Lógica de "
                            "Negocio). Contrato: 200/201 éxito · 400 solicitud inválida · 403 rol no "
                            "permitido · 404 no existe · 409 conflicto de estado o regla · 422 validación."),
        },
        "servers": [{"url": "/"}],
        "paths": paths,
        "components": {"schemas": {"Error": {
            "type": "object",
            "properties": {"error": {"type": "object", "properties": {
                "codigo": {"type": "string", "example": "EVIDENCIA_OBLIGATORIA"},
                "mensaje": {"type": "string"}}}}}}},
    }
