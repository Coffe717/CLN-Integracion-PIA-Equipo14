"""Acceso a base de datos (SQLite o PostgreSQL) con transacciones tipo Unit of Work.

El SQL se escribe con `?` y se adapta al driver. Se soporta:
  sqlite:///ruta/archivo.db   |   sqlite:///:memory:   |   postgresql://usuario:clave@host:5432/db
"""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, List, Sequence

ESQUEMA = [
    """CREATE TABLE IF NOT EXISTS remitentes (
        id TEXT PRIMARY KEY, nombre TEXT NOT NULL, activo INTEGER NOT NULL,
        preferente INTEGER NOT NULL, ciudad TEXT)""",
    """CREATE TABLE IF NOT EXISTS paquetes (
        guia TEXT PRIMARY KEY, remitente_id TEXT NOT NULL, estado TEXT NOT NULL,
        actualizado_en TEXT NOT NULL, datos TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS incidencias (
        id TEXT PRIMARY KEY, guia TEXT NOT NULL, estado TEXT NOT NULL,
        creada_en TEXT NOT NULL, datos TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS manifiestos (
        id TEXT PRIMARY KEY, estado TEXT NOT NULL, datos TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS rutas (
        id TEXT PRIMARY KEY, estado TEXT NOT NULL, datos TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS notificaciones (
        id TEXT PRIMARY KEY, destino TEXT NOT NULL, mensaje TEXT NOT NULL,
        guia TEXT, creada_en TEXT NOT NULL)""",
]


class Database:
    def __init__(self, url: str = "sqlite:///data/cargobox.db"):
        self.url = url
        self.es_postgres = url.startswith(("postgres://", "postgresql://"))
        self._lock = threading.RLock()
        self._local = threading.local()
        self._compartida = None
        if not self.es_postgres:
            if not url.startswith("sqlite:///"):
                raise ValueError("DATABASE_URL debe iniciar con sqlite:/// o postgresql://")
            self.ruta = url[len("sqlite:///"):] or ":memory:"
            if self.ruta == ":memory:":
                self._compartida = sqlite3.connect(":memory:", check_same_thread=False)
            else:
                carpeta = os.path.dirname(self.ruta)
                if carpeta:
                    os.makedirs(carpeta, exist_ok=True)
        self.inicializar()

    # ------------------------------------------------------------ conexión
    def _abrir(self):
        if self.es_postgres:  # pragma: no cover - requiere un servidor PostgreSQL (Docker Compose)
            import psycopg2  # import perezoso: solo se necesita con PostgreSQL

            return psycopg2.connect(self.url)
        if self._compartida is not None:
            return self._compartida
        return sqlite3.connect(self.ruta)

    def _adaptar(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.es_postgres else sql

    @contextmanager
    def transaccion(self):
        """Abre (o reutiliza) la transacción actual; confirma al salir o hace rollback."""
        profundidad = getattr(self._local, "profundidad", 0)
        if profundidad > 0:
            self._local.profundidad = profundidad + 1
            try:
                yield self._local.conexion
            finally:
                self._local.profundidad -= 1
            return
        with self._lock:
            conexion = self._abrir()
            self._local.conexion = conexion
            self._local.profundidad = 1
            try:
                yield conexion
                conexion.commit()
            except BaseException:
                conexion.rollback()
                raise
            finally:
                self._local.profundidad = 0
                self._local.conexion = None
                if self._compartida is None:
                    conexion.close()

    # ------------------------------------------------------------ operaciones
    def ejecutar(self, sql: str, params: Sequence[Any] = ()) -> None:
        with self.transaccion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(self._adaptar(sql), tuple(params))
            cursor.close()

    def consultar(self, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        with self.transaccion() as conexion:
            cursor = conexion.cursor()
            cursor.execute(self._adaptar(sql), tuple(params))
            columnas = [c[0] for c in cursor.description]
            filas = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
            cursor.close()
            return filas

    def inicializar(self) -> None:
        with self.transaccion():
            for sentencia in ESQUEMA:
                self.ejecutar(sentencia)
