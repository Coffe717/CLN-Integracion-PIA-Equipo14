"""Casos CP-01 a CP-08 (tabla del PIA) ejecutados de extremo a extremo.

Los mismos 8 casos de `tests/unit/test_casos_pia_imagen.py`, pero recorriendo
todas las capas: API REST -> servicios -> dominio -> repositorios SQL/memoria.
Así la suite de los casos del PIA (`pytest -m cp`) por sí sola supera el 80 %
de cobertura, además de la suite completa (`pytest`).
"""
import pytest

from src.domain.excepciones import (
    EvidenciaObligatoriaException,
    TercerIntentoNoAutorizadoException,
    TransicionEstadoInvalidaException,
    ValorInvalidoException,
)
from tests.conftest import DATOS_ENVIO, alta_envio, llevar_a_reparto

pytestmark = pytest.mark.cp

API = "/api/v1"
FIRMA = "data:image/png;base64,FIRMA"
FOTO = "data:image/jpeg;base64,FOTO"
COTIZACION_CP07 = {"peso_kg": 5, "largo_cm": 30, "ancho_cm": 30, "alto_cm": 30,
                   "destino_ciudad": "Monterrey", "nivel_servicio": "Servicio Estándar"}


# ----------------------------------------------------------------- apoyo (capa de servicios)
def recibir(c):
    return c.recepcion.registrar_recepcion_paquete(
        "R1", "Ana López", "8112345678", "Av. Juárez 100", "Monterrey", "Calle Hidalgo 45",
        "Monterrey", 5, 30, 30, 30, "ESTANDAR", "Caja", "Empleado")["guia"]


def a_reparto(c, guia):
    c.logistica.clasificar_paquete(guia, "CD Monterrey", "Op")
    m = c.logistica.despachar_manifiesto_viaje("CD Monterrey", "CD Saltillo", [guia], "Op")
    c.logistica.registrar_arribo_centro_destino(m["id"], "CD Saltillo", "Op")
    c.entrega.iniciar_ruta_reparto("Juan", [guia])


def dos_ausencias(c, guia):
    c.entrega.registrar_destinatario_ausente(guia, "Juan")
    c.entrega.reanudar_reparto(guia, "Juan")
    c.entrega.registrar_destinatario_ausente(guia, "Juan")
    c.entrega.reanudar_reparto(guia, "Juan")


def dos_ausencias_api(cliente, guia):
    for _ in range(2):
        assert cliente.post(f"{API}/paquetes/{guia}/ausencia", json={"repartidor": "Juan"}).status_code == 200
        assert cliente.post(f"{API}/paquetes/{guia}/reanudar", json={"repartidor": "Juan"}).status_code == 200


# ================================================================= BR012 · evidencia obligatoria
class TestCP01EntregaConEvidencia:
    def test_servicio(self, contenedor):
        g = recibir(contenedor)
        a_reparto(contenedor, g)
        p = contenedor.entrega.finalizar_entrega_con_evidencia(g, "Ana López", FIRMA, FOTO, "Juan")
        assert p["estado"] == "ENTREGADO" and p["tiene_evidencia"]
        ev = contenedor.consulta.consultar_evidencia_entrega(g)
        assert (ev["firma"], ev["foto"], ev["receptor"]) == (FIRMA, FOTO, "Ana López")
        assert contenedor.consulta.consultar_linea_de_tiempo(g)["linea_de_tiempo"][-1]["estado"] == "ENTREGADO"
        assert any("Entrega concluida" in n["mensaje"] for n in contenedor.consulta.listar_notificaciones())

    def test_api(self, cliente):
        g = alta_envio(cliente)
        llevar_a_reparto(cliente, g)
        r = cliente.post(f"{API}/paquetes/{g}/entrega",
                         json={"receptor": "Ana López", "firma": FIRMA, "foto": FOTO, "repartidor": "Juan"})
        assert r.status_code == 200 and r.json["estado"] == "ENTREGADO"
        ev = cliente.get(f"{API}/paquetes/{g}/evidencia")
        assert ev.status_code == 200 and ev.json["firma"] == FIRMA and ev.json["foto"] == FOTO
        rastreo = cliente.get(f"{API}/paquetes/{g}/rastreo").json
        assert rastreo["evidencia"]["receptor"] == "Ana López"
        assert cliente.get(f"{API}/paquetes?estado=ENTREGADO").json[0]["guia"] == g


class TestCP02EntregaSinEvidencia:
    def test_servicio(self, contenedor):
        g = recibir(contenedor)
        a_reparto(contenedor, g)
        with pytest.raises(EvidenciaObligatoriaException):
            contenedor.entrega.finalizar_entrega_con_evidencia(g, "Ana López", None, None, "Juan")
        assert contenedor.consulta.consultar_linea_de_tiempo(g)["estado"] == "EN_REPARTO"

    def test_api(self, cliente):
        g = alta_envio(cliente)
        llevar_a_reparto(cliente, g)
        r = cliente.post(f"{API}/paquetes/{g}/entrega", json={"receptor": "Ana López", "firma": None, "foto": None})
        assert r.status_code == 422 and r.json["error"]["codigo"] == "EVIDENCIA_OBLIGATORIA"
        assert cliente.get(f"{API}/paquetes/{g}").json["estado"] == "EN_REPARTO"
        assert cliente.get(f"{API}/paquetes/{g}/evidencia").status_code == 409


class TestCP03EntregarCancelado:
    def test_servicio(self, contenedor):
        g = recibir(contenedor)
        contenedor.entrega.cancelar_envio(g, "Cancelado por el cliente", "Emp")
        with pytest.raises(TransicionEstadoInvalidaException):
            contenedor.entrega.finalizar_entrega_con_evidencia(g, "Ana López", FIRMA, FOTO, "Juan")
        assert contenedor.consulta.consultar_linea_de_tiempo(g)["estado"] == "CANCELADO"

    def test_api(self, cliente):
        g = alta_envio(cliente)
        assert cliente.post(f"{API}/paquetes/{g}/cancelar", json={"motivo": "error"}).json["estado"] == "CANCELADO"
        r = cliente.post(f"{API}/paquetes/{g}/entrega", json={"receptor": "Ana", "firma": FIRMA})
        assert r.status_code == 409 and r.json["error"]["codigo"] == "TRANSICION_INVALIDA"


# ================================================================= BR014 · límite de intentos
class TestCP04PrimeraVisitaAusente:
    def test_servicio(self, contenedor):
        g = recibir(contenedor)
        a_reparto(contenedor, g)
        p = contenedor.entrega.registrar_destinatario_ausente(g, "Juan")
        assert p["estado"] == "SEGUNDO_INTENTO_PENDIENTE" and p["intentos_fallidos"] == 1
        assert not p["requiere_autorizacion_tercer_intento"]

    def test_api(self, cliente):
        g = alta_envio(cliente)
        llevar_a_reparto(cliente, g)
        r = cliente.post(f"{API}/paquetes/{g}/ausencia", json={"repartidor": "Juan"})
        assert r.status_code == 200 and r.json["estado"] == "SEGUNDO_INTENTO_PENDIENTE"
        assert "reagendado" in cliente.get(f"{API}/paquetes/{g}").json["linea_de_tiempo"][-1]["descripcion"]


class TestCP05TerceraVisitaSinAutorizacion:
    def test_servicio(self, contenedor):
        g = recibir(contenedor)
        a_reparto(contenedor, g)
        dos_ausencias(contenedor, g)
        with pytest.raises(TercerIntentoNoAutorizadoException):
            contenedor.entrega.registrar_destinatario_ausente(g, "Juan")
        assert any(n["destino"] == "SUPERVISOR" for n in contenedor.consulta.listar_notificaciones())

    def test_api(self, cliente):
        g = alta_envio(cliente)
        llevar_a_reparto(cliente, g)
        dos_ausencias_api(cliente, g)
        r = cliente.post(f"{API}/paquetes/{g}/ausencia", json={"repartidor": "Juan"})
        assert r.status_code == 409 and r.json["error"]["codigo"] == "TERCER_INTENTO_NO_AUTORIZADO"
        assert cliente.get(f"{API}/notificaciones?destino=SUPERVISOR").json


class TestCP06TerceraVisitaAutorizada:
    def test_servicio(self, contenedor):
        g = recibir(contenedor)
        a_reparto(contenedor, g)
        dos_ausencias(contenedor, g)
        contenedor.entrega.autorizar_tercer_intento(g, "Rosa", "SUPERVISOR")
        p = contenedor.entrega.registrar_destinatario_ausente(g, "Juan")
        assert p["estado"] == "RETENIDO_EN_SUCURSAL" and p["intentos_fallidos"] == 3

    def test_api(self, cliente):
        g = alta_envio(cliente)
        llevar_a_reparto(cliente, g)
        dos_ausencias_api(cliente, g)
        ok = cliente.post(f"{API}/paquetes/{g}/autorizar-reintento",
                          json={"autorizador": "Laura", "rol": "ATENCION_CLIENTE"})
        assert ok.status_code == 200 and ok.json["tercer_intento_autorizado"]
        r = cliente.post(f"{API}/paquetes/{g}/ausencia", json={"repartidor": "Juan"})
        assert r.status_code == 200 and r.json["estado"] == "RETENIDO_EN_SUCURSAL"


# ================================================================= BR005 · cálculo estricto de tarifa
class TestCP07Tarifa150:
    def test_servicio(self, contenedor):
        t = contenedor.cotizacion.cotizar_envio(5, 30, 30, 30, "Monterrey", "Servicio Estándar")
        assert t["total"] == "150.00" and t["moneda"] == "MXN"
        p = contenedor.recepcion.registrar_recepcion_paquete(
            "R1", "Ana", "", "Juárez 1", "Monterrey", "Hidalgo 2", "Monterrey", 5, 30, 30, 30, "ESTANDAR")
        assert p["tarifa"]["total"] == "150.00" and p["estado"] == "RECIBIDO"

    def test_api(self, cliente):
        r = cliente.post(f"{API}/cotizaciones", json=COTIZACION_CP07)
        assert r.status_code == 200 and r.json["texto"] == "$150.00 MXN"
        alta = cliente.post(f"{API}/paquetes", json=DATOS_ENVIO)
        assert alta.status_code == 201 and alta.json["tarifa"]["total"] == "150.00"


class TestCP08ValidacionValueObjects:
    @pytest.mark.parametrize("cambio", [{"peso_kg": -5}, {"peso_kg": 0}, {"largo_cm": 0},
                                        {"ancho_cm": 0}, {"alto_cm": 0}])
    def test_servicio(self, contenedor, cambio):
        datos = {**COTIZACION_CP07, **cambio}
        with pytest.raises(ValorInvalidoException):
            contenedor.cotizacion.cotizar_envio(datos["peso_kg"], datos["largo_cm"], datos["ancho_cm"],
                                                datos["alto_cm"], datos["destino_ciudad"], datos["nivel_servicio"])
        assert contenedor.consulta.listar_paquetes() == []

    @pytest.mark.parametrize("cambio", [{"peso_kg": -5}, {"largo_cm": 0, "ancho_cm": 0, "alto_cm": 0}])
    def test_api(self, cliente, cambio):
        assert cliente.post(f"{API}/cotizaciones", json={**COTIZACION_CP07, **cambio}).status_code == 422
        r = cliente.post(f"{API}/paquetes", json={**DATOS_ENVIO, **cambio})
        assert r.status_code == 422 and r.json["error"]["codigo"] == "VALOR_INVALIDO"
        assert cliente.get(f"{API}/paquetes").json == []


# ================================================================= contrato de la API para los CP
def test_endpoints_de_los_cp_estan_documentados_en_swagger(cliente):
    """Los endpoints usados por CP-01..CP-08 aparecen en OpenAPI y Swagger UI está activo."""
    rutas = cliente.get("/openapi.json").json["paths"]
    for ruta in ("/api/v1/cotizaciones", "/api/v1/paquetes", "/api/v1/paquetes/{guia}/entrega",
                 "/api/v1/paquetes/{guia}/ausencia", "/api/v1/paquetes/{guia}/autorizar-reintento",
                 "/api/v1/paquetes/{guia}/cancelar"):
        assert ruta in rutas
    assert "swagger-ui" in cliente.get("/docs").get_data(as_text=True)
