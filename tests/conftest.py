import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.app import create_app  # noqa: E402
from src.api.config import Config  # noqa: E402
from src.domain.tabulador import CalculadoraTarifa  # noqa: E402
from src.domain.remitente import Remitente  # noqa: E402
from src.infrastructure.composicion import construir_memoria, construir_sql  # noqa: E402


@pytest.fixture
def calculadora():
    return CalculadoraTarifa()


def _con_remitentes(c):
    c.remitentes.guardar(Remitente("R1", "Remitente Uno", True, False, "Monterrey"))
    c.remitentes.guardar(Remitente("R2", "Remitente Inactivo", False, False, "Apodaca"))
    c.remitentes.guardar(Remitente("R3", "Remitente VIP", True, True, "Monterrey"))
    return c


@pytest.fixture
def memoria():
    return _con_remitentes(construir_memoria())


@pytest.fixture
def sql():
    return _con_remitentes(construir_sql("sqlite:///:memory:"))


@pytest.fixture(params=["memoria", "sql"])
def contenedor(request):
    """Cada prueba de servicios corre con repositorios en memoria y con SQLite."""
    return request.getfixturevalue(request.param)


@pytest.fixture
def cliente(sql):
    app = create_app(Config(database_url="sqlite:///:memory:", seed_demo=False), contenedor=sql)
    return app.test_client()


DATOS_ENVIO = {
    "remitente_id": "R1", "destinatario_nombre": "Ana López", "destinatario_telefono": "8112345678",
    "destino_calle": "Calle Hidalgo 45", "destino_ciudad": "Monterrey", "peso_kg": 5,
    "largo_cm": 30, "ancho_cm": 30, "alto_cm": 30, "nivel_servicio": "ESTANDAR",
}


def alta_envio(cliente, **extra):
    r = cliente.post("/api/v1/paquetes", json={**DATOS_ENVIO, **extra})
    assert r.status_code == 201, r.json
    return r.json["guia"]


def llevar_a_reparto(cliente, guia):
    api = "/api/v1"
    assert cliente.post(f"{api}/paquetes/{guia}/clasificar", json={"instalacion": "CD MTY"}).status_code == 200
    assert cliente.post(f"{api}/manifiestos", json={"origen": "CD MTY", "destino": "CD SLW", "guias": [guia]}).status_code == 201
    assert cliente.post(f"{api}/paquetes/{guia}/arribo", json={"instalacion": "CD SLW"}).status_code == 200
    assert cliente.post(f"{api}/rutas", json={"repartidor": "Juan", "guias": [guia]}).status_code == 201
