"""Pruebas de integración de la API REST (códigos 200/201/400/403/404/409/422)."""
import pytest

from tests.conftest import DATOS_ENVIO, alta_envio, llevar_a_reparto

API = "/api/v1"
FIRMA = "data:image/png;base64,AAAA"


def test_health_y_catalogo(cliente):
    assert cliente.get(f"{API}/health").json == {"estado": "ok", "servicio": "cargobox"}
    assert len(cliente.get(f"{API}/remitentes").json) == 3


def test_cotizacion_cp07_y_validaciones(cliente):
    cuerpo = {"peso_kg": 5, "largo_cm": 30, "ancho_cm": 30, "alto_cm": 30,
              "destino_ciudad": "Monterrey", "nivel_servicio": "Servicio Estándar"}
    r = cliente.post(f"{API}/cotizaciones", json=cuerpo)
    assert r.status_code == 200 and r.json["total"] == "150.00" and r.json["moneda"] == "MXN"
    assert cliente.post(f"{API}/cotizaciones", json={**cuerpo, "peso_kg": -5}).status_code == 422  # CP-08
    assert cliente.post(f"{API}/cotizaciones", json={**cuerpo, "alto_cm": 0}).status_code == 422    # CP-08
    assert cliente.post(f"{API}/cotizaciones", json={**cuerpo, "nivel_servicio": "x"}).status_code == 422
    assert cliente.post(f"{API}/cotizaciones", json={"peso_kg": 1}).status_code == 400
    assert cliente.post(f"{API}/cotizaciones", data="no-json", content_type="application/json").status_code == 400


def test_registro_201_y_errores(cliente):
    r = cliente.post(f"{API}/paquetes", json=DATOS_ENVIO)
    assert r.status_code == 201 and r.json["estado"] == "RECIBIDO" and r.json["guia"].startswith("CB-")
    assert cliente.post(f"{API}/paquetes", json={**DATOS_ENVIO, "remitente_id": "NOPE"}).status_code == 404
    assert cliente.post(f"{API}/paquetes", json={**DATOS_ENVIO, "remitente_id": "R2"}).status_code == 409
    assert cliente.post(f"{API}/paquetes", json={**DATOS_ENVIO, "peso_kg": 0}).status_code == 422
    assert cliente.post(f"{API}/paquetes", json={"remitente_id": "R1"}).status_code == 400


def test_rastreo_y_404(cliente):
    g = alta_envio(cliente)
    r = cliente.get(f"{API}/paquetes/{g}")
    assert r.status_code == 200 and r.json["linea_de_tiempo"][0]["estado"] == "RECIBIDO"
    assert cliente.get(f"{API}/paquetes/{g}/rastreo").status_code == 200
    assert cliente.get(f"{API}/paquetes/CB-0000000000").status_code == 404
    assert cliente.get(f"{API}/ruta-inexistente").status_code == 404
    assert cliente.delete(f"{API}/health").status_code == 405
    assert len(cliente.get(f"{API}/paquetes?estado=RECIBIDO").json) == 1


def test_cp01_entrega_con_evidencia_api(cliente):
    g = alta_envio(cliente)
    llevar_a_reparto(cliente, g)
    r = cliente.post(f"{API}/paquetes/{g}/entrega", json={"receptor": "Ana", "firma": FIRMA, "foto": FIRMA})
    assert r.status_code == 200 and r.json["estado"] == "ENTREGADO"
    ev = cliente.get(f"{API}/paquetes/{g}/evidencia")
    assert ev.status_code == 200 and ev.json["firma"] == FIRMA and ev.json["tiene_foto"]


def test_cp02_entrega_sin_evidencia_api(cliente):
    g = alta_envio(cliente)
    llevar_a_reparto(cliente, g)
    r = cliente.post(f"{API}/paquetes/{g}/entrega", json={"receptor": "Ana"})
    assert r.status_code == 422 and r.json["error"]["codigo"] == "EVIDENCIA_OBLIGATORIA"
    assert cliente.get(f"{API}/paquetes/{g}").json["estado"] == "EN_REPARTO"
    assert cliente.get(f"{API}/paquetes/{g}/evidencia").status_code == 409


def test_cp03_entregar_cancelado_api(cliente):
    g = alta_envio(cliente)
    assert cliente.post(f"{API}/paquetes/{g}/cancelar", json={"motivo": "error"}).status_code == 200
    r = cliente.post(f"{API}/paquetes/{g}/entrega", json={"receptor": "Ana", "firma": FIRMA})
    assert r.status_code == 409 and r.json["error"]["codigo"] == "TRANSICION_INVALIDA"


def test_cp04_cp05_cp06_intentos_api(cliente):
    g = alta_envio(cliente)
    llevar_a_reparto(cliente, g)
    r = cliente.post(f"{API}/paquetes/{g}/ausencia", json={})                     # CP-04
    assert r.status_code == 200 and r.json["estado"] == "SEGUNDO_INTENTO_PENDIENTE"
    cliente.post(f"{API}/paquetes/{g}/reanudar", json={})
    cliente.post(f"{API}/paquetes/{g}/ausencia")
    cliente.post(f"{API}/paquetes/{g}/reanudar")
    r = cliente.post(f"{API}/paquetes/{g}/ausencia")                              # CP-05
    assert r.status_code == 409 and r.json["error"]["codigo"] == "TERCER_INTENTO_NO_AUTORIZADO"
    assert cliente.post(f"{API}/paquetes/{g}/autorizar-reintento", json={"autorizador": "Pedro", "rol": "REPARTIDOR"}).status_code == 403
    assert cliente.post(f"{API}/paquetes/{g}/autorizar-reintento", json={"autorizador": "Pedro"}).status_code == 400
    ok = cliente.post(f"{API}/paquetes/{g}/autorizar-reintento", json={"autorizador": "Rosa", "rol": "SUPERVISOR"})
    assert ok.status_code == 200
    r = cliente.post(f"{API}/paquetes/{g}/ausencia")                              # CP-06
    assert r.status_code == 200 and r.json["estado"] == "RETENIDO_EN_SUCURSAL"


def test_validaciones_de_listas_y_campos(cliente):
    assert cliente.post(f"{API}/manifiestos", json={"origen": "A", "destino": "B", "guias": "CB-1"}).status_code == 400
    assert cliente.post(f"{API}/manifiestos", json={"origen": "A", "destino": "B", "guias": []}).status_code == 422
    assert cliente.post(f"{API}/rutas", json={"repartidor": "J", "guias": "x"}).status_code == 400
    assert cliente.post(f"{API}/manifiestos", json={"origen": "A", "destino": "B", "guias": ["CB-1"]}).status_code == 404
    assert cliente.post(f"{API}/paquetes/CB-X/clasificar", json={}).status_code == 400
    assert cliente.post(f"{API}/paquetes/CB-X/arribo", json={}).status_code == 400
    assert cliente.post(f"{API}/manifiestos/MAN-X/arribo", json={}).status_code == 400
    assert cliente.post(f"{API}/manifiestos/MAN-X/arribo", json={"instalacion": "A"}).status_code == 404


def test_rechazo_devolucion_y_manifiesto_arribo(cliente):
    a, b = alta_envio(cliente), alta_envio(cliente)
    for g in (a, b):
        cliente.post(f"{API}/paquetes/{g}/clasificar", json={"instalacion": "CD MTY", "operador": "Op"})
    m = cliente.post(f"{API}/manifiestos", json={"origen": "CD MTY", "destino": "CD SLW", "guias": [a, b]}).json
    assert cliente.post(f"{API}/manifiestos/{m['id']}/arribo", json={"instalacion": "CD SLW"}).json["estado"] == "ARRIBADO"
    assert cliente.post(f"{API}/rutas", json={"repartidor": "Juan", "guias": [a]}).status_code == 201
    r = cliente.post(f"{API}/paquetes/{a}/rechazo", json={"motivo": "no lo quiero", "repartidor": "Juan"})
    assert r.json["estado"] == "RECHAZADO_EN_DEVOLUCION"
    assert cliente.post(f"{API}/paquetes/{b}/rechazo", json={"motivo": "x"}).status_code == 409
    assert cliente.post(f"{API}/paquetes/{a}/devolucion", json={"empleado": "Emp"}).json["estado"] == "DEVUELTO_A_ORIGEN"


def test_incidencias_y_alertas_api(cliente):
    g = alta_envio(cliente)
    llevar_a_reparto(cliente, g)
    t = cliente.post(f"{API}/paquetes/{g}/direccion-incorrecta", json={"repartidor": "Juan", "comentario": "no existe"})
    assert t.status_code == 201
    iid = t.json["id"]
    assert cliente.get(f"{API}/incidencias?estado=ABIERTA").json[0]["id"] == iid
    assert cliente.post(f"{API}/incidencias/{iid}/resolver", json={"agente": "J", "rol": "REPARTIDOR", "resolucion": "x"}).status_code == 403
    assert cliente.post(f"{API}/incidencias/{iid}/resolver", json={"agente": "L"}).status_code == 400
    ok = cliente.post(f"{API}/incidencias/{iid}/resolver", json={
        "agente": "Laura", "rol": "ATENCION_CLIENTE", "resolucion": "confirmada", "nueva_calle": "Nueva 1", "nueva_ciudad": "Monterrey"})
    assert ok.status_code == 200
    assert cliente.post(f"{API}/paquetes/{g}/reanudar", json={}).status_code == 200
    d = cliente.post(f"{API}/paquetes/{g}/incidencia-mayor", json={"tipo": "DANO", "descripcion": "roto"})
    assert d.status_code == 201
    assert cliente.post(f"{API}/paquetes/{g}/incidencia-mayor", json={}).status_code == 400
    assert cliente.get(f"{API}/alertas?umbral_horas=0").status_code == 200
    assert cliente.get(f"{API}/alertas?umbral_horas=abc").status_code == 422
    assert cliente.post(f"{API}/alertas/ejecutar", json={"umbral_horas": 0}).status_code == 200
    assert cliente.post(f"{API}/alertas/ejecutar").status_code == 200
    assert cliente.get(f"{API}/alertas").json == []
    assert len(cliente.get(f"{API}/notificaciones?destino=ATENCION_CLIENTE").json) >= 2
    assert cliente.get(f"{API}/notificaciones").status_code == 200


def test_interfaz_y_swagger(cliente):
    assert "CargoBox" in cliente.get("/").get_data(as_text=True)
    assert cliente.get("/ruta-de-la-ui").status_code == 200  # cae al index
    assert "swagger-ui" in cliente.get("/docs").get_data(as_text=True)
    doc = cliente.get("/openapi.json").json
    assert doc["openapi"].startswith("3.") and "/api/v1/paquetes" in doc["paths"]


def test_openapi_documenta_todas_las_rutas(cliente):
    from flask import current_app  # noqa: F401
    app = cliente.application
    rutas = {r.rule.replace("<", "{").replace(">", "}") for r in app.url_map.iter_rules() if r.rule.startswith("/api")}
    documentadas = set(cliente.get("/openapi.json").json["paths"])
    assert rutas == documentadas
