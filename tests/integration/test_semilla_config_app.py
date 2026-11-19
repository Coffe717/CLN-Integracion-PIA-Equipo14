import os

from src.api.app import create_app
from src.api.config import Config
from src.infrastructure.composicion import construir_memoria
from src.infrastructure.semilla import leer_remitentes_csv, sembrar_envios_demo, sembrar_remitentes


def test_config_desde_entorno(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("SEED_DEMO", "false")
    monkeypatch.setenv("UMBRAL_HORAS", "48")
    monkeypatch.setenv("PORT", "9000")
    c = Config.desde_entorno()
    assert (c.database_url, c.seed_demo, c.umbral_horas, c.port) == ("sqlite:///:memory:", False, 48.0, 9000)


def test_config_por_defecto(monkeypatch):
    for k in ("DATABASE_URL", "SEED_DEMO", "UMBRAL_HORAS", "PORT"):
        monkeypatch.delenv(k, raising=False)
    c = Config.desde_entorno()
    assert c.seed_demo is True and c.umbral_horas == 24.0 and c.database_url.startswith("sqlite:///")


def test_csv_actores():
    remitentes = leer_remitentes_csv()
    assert len(remitentes) == 40 and remitentes[0].id == "CAR-C001"


def test_csv_inexistente_usa_respaldo(tmp_path):
    assert len(leer_remitentes_csv(str(tmp_path / "no.csv"))) == 4


def test_semilla_es_idempotente():
    c = construir_memoria()
    assert sembrar_remitentes(c) == 40 and sembrar_remitentes(c) == 0
    guias = sembrar_envios_demo(c)
    assert len(guias) == 4 and sembrar_envios_demo(c) == []
    estados = {p["estado"] for p in c.consulta.listar_paquetes()}
    assert {"RECIBIDO", "CLASIFICADO", "EN_TRANSITO"} <= estados


def test_semilla_sin_remitentes_activos():
    assert sembrar_envios_demo(construir_memoria()) == []


def test_create_app_con_sqlite_en_memoria_y_demo():
    app = create_app(Config(database_url="sqlite:///:memory:", seed_demo=True))
    r = app.test_client().get("/api/v1/paquetes")
    assert r.status_code == 200 and len(r.json) == 4
