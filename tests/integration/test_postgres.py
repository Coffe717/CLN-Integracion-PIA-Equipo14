"""Prueba de humo contra PostgreSQL real. Se omite si DATABASE_URL no apunta a Postgres.

Con Docker Compose:  docker compose run --rm tests
"""
import os
import uuid

import pytest

from src.domain.remitente import Remitente
from src.infrastructure.composicion import construir_sql

POSTGRES = os.getenv("DATABASE_URL", "").startswith(("postgres://", "postgresql://"))


@pytest.mark.skipif(not POSTGRES, reason="requiere PostgreSQL (docker compose run --rm tests)")
def test_flujo_basico_en_postgres():
    c = construir_sql(os.environ["DATABASE_URL"])
    rid = "T-" + uuid.uuid4().hex[:8]
    c.remitentes.guardar(Remitente(rid, "Prueba PG", True, False, "Monterrey"))
    p = c.recepcion.registrar_recepcion_paquete(
        rid, "Ana", "8112345678", "Juárez 1", "Monterrey", "Hidalgo 2", "Monterrey",
        5, 30, 30, 30, "ESTANDAR")
    c.logistica.clasificar_paquete(p["guia"], "CD MTY")
    assert c.consulta.consultar_linea_de_tiempo(p["guia"])["estado"] == "CLASIFICADO"
