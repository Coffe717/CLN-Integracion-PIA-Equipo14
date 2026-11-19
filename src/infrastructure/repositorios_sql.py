"""Repositorios SQL (SQLite/PostgreSQL) que implementan los puertos de aplicación."""
from __future__ import annotations

import json
import uuid
from typing import List, Optional

from src.application.puertos import (
    IGeneradorGuia, IIncidenciaRepository, IManifiestoRepository, INotificador,
    IPaqueteRepository, IRemitenteRepository, IRutaRepository, IUnitOfWork,
)
from src.domain.incidencia import Incidencia
from src.domain.manifiesto import ManifiestoViaje, RutaReparto
from src.domain.paquete import Paquete
from src.domain.remitente import Remitente
from src.domain.valores import GuiaRastreo, ahora
from src.infrastructure import mappers as m
from src.infrastructure.db import Database


class SqlUnitOfWork(IUnitOfWork):
    """Una transacción por caso de uso: commit al salir, rollback ante excepción."""

    def __init__(self, db: Database):
        self._db = db
        self._pila: list = []

    def __enter__(self):
        contexto = self._db.transaccion()
        contexto.__enter__()
        self._pila.append(contexto)
        return self

    def __exit__(self, tipo, valor, tb):
        contexto = self._pila.pop()
        return contexto.__exit__(tipo, valor, tb)


def _reemplazar(db: Database, tabla: str, clave: str, valor_clave: str, columnas: dict) -> None:
    """Upsert portable: DELETE + INSERT dentro de la misma transacción."""
    with db.transaccion():
        db.ejecutar(f"DELETE FROM {tabla} WHERE {clave} = ?", (valor_clave,))
        nombres = ", ".join([clave] + list(columnas))
        marcas = ", ".join("?" for _ in range(len(columnas) + 1))
        db.ejecutar(f"INSERT INTO {tabla} ({nombres}) VALUES ({marcas})",
                    (valor_clave, *columnas.values()))


class SqlPaqueteRepository(IPaqueteRepository):
    def __init__(self, db: Database):
        self._db = db

    def obtener_por_guia(self, guia: str) -> Optional[Paquete]:
        filas = self._db.consultar("SELECT datos FROM paquetes WHERE guia = ?", (guia,))
        return m.paquete_desde_dict(json.loads(filas[0]["datos"])) if filas else None

    def guardar(self, paquete: Paquete) -> None:
        _reemplazar(self._db, "paquetes", "guia", str(paquete.guia), {
            "remitente_id": paquete.remitente_id, "estado": paquete.estado.value,
            "actualizado_en": paquete.actualizado_en.isoformat(),
            "datos": json.dumps(m.paquete_a_dict(paquete))})

    def listar(self, estado=None, remitente_id=None) -> List[Paquete]:
        sql, params = "SELECT datos FROM paquetes WHERE 1 = 1", []
        if estado:
            sql += " AND estado = ?"
            params.append(estado)
        if remitente_id:
            sql += " AND remitente_id = ?"
            params.append(remitente_id)
        sql += " ORDER BY actualizado_en DESC"
        return [m.paquete_desde_dict(json.loads(f["datos"])) for f in self._db.consultar(sql, params)]


class SqlRemitenteRepository(IRemitenteRepository):
    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _a_entidad(f) -> Remitente:
        return Remitente(f["id"], f["nombre"], bool(f["activo"]), bool(f["preferente"]), f["ciudad"] or "")

    def obtener(self, remitente_id: str) -> Optional[Remitente]:
        filas = self._db.consultar("SELECT * FROM remitentes WHERE id = ?", (remitente_id,))
        return self._a_entidad(filas[0]) if filas else None

    def guardar(self, r: Remitente) -> None:
        _reemplazar(self._db, "remitentes", "id", r.id, {
            "nombre": r.nombre, "activo": int(r.activo), "preferente": int(r.preferente), "ciudad": r.ciudad})

    def listar(self) -> List[Remitente]:
        return [self._a_entidad(f) for f in self._db.consultar("SELECT * FROM remitentes ORDER BY id")]


class SqlIncidenciaRepository(IIncidenciaRepository):
    def __init__(self, db: Database):
        self._db = db

    def obtener(self, incidencia_id: str) -> Optional[Incidencia]:
        filas = self._db.consultar("SELECT datos FROM incidencias WHERE id = ?", (incidencia_id,))
        return m.incidencia_desde_dict(json.loads(filas[0]["datos"])) if filas else None

    def guardar(self, i: Incidencia) -> None:
        _reemplazar(self._db, "incidencias", "id", i.id, {
            "guia": i.guia, "estado": i.estado.value, "creada_en": i.creada_en.isoformat(),
            "datos": json.dumps(m.incidencia_a_dict(i))})

    def listar(self, estado=None, guia=None) -> List[Incidencia]:
        sql, params = "SELECT datos FROM incidencias WHERE 1 = 1", []
        if estado:
            sql += " AND estado = ?"
            params.append(estado)
        if guia:
            sql += " AND guia = ?"
            params.append(guia)
        sql += " ORDER BY creada_en DESC"
        return [m.incidencia_desde_dict(json.loads(f["datos"])) for f in self._db.consultar(sql, params)]


class SqlManifiestoRepository(IManifiestoRepository):
    def __init__(self, db: Database):
        self._db = db

    def obtener(self, manifiesto_id: str) -> Optional[ManifiestoViaje]:
        filas = self._db.consultar("SELECT datos FROM manifiestos WHERE id = ?", (manifiesto_id,))
        return m.manifiesto_desde_dict(json.loads(filas[0]["datos"])) if filas else None

    def guardar(self, manifiesto: ManifiestoViaje) -> None:
        _reemplazar(self._db, "manifiestos", "id", manifiesto.id, {
            "estado": manifiesto.estado.value, "datos": json.dumps(m.manifiesto_a_dict(manifiesto))})


class SqlRutaRepository(IRutaRepository):
    def __init__(self, db: Database):
        self._db = db

    def obtener(self, ruta_id: str) -> Optional[RutaReparto]:
        filas = self._db.consultar("SELECT datos FROM rutas WHERE id = ?", (ruta_id,))
        return m.ruta_desde_dict(json.loads(filas[0]["datos"])) if filas else None

    def guardar(self, ruta: RutaReparto) -> None:
        _reemplazar(self._db, "rutas", "id", ruta.id, {
            "estado": ruta.estado.value, "datos": json.dumps(m.ruta_a_dict(ruta))})


class SqlNotificador(INotificador):
    def __init__(self, db: Database):
        self._db = db

    def notificar(self, destino: str, mensaje: str, guia: str = "") -> None:
        self._db.ejecutar(
            "INSERT INTO notificaciones (id, destino, mensaje, guia, creada_en) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, destino, mensaje, guia, ahora().isoformat()))

    def listar(self, destino: Optional[str] = None, limite: int = 50) -> List[dict]:
        sql, params = "SELECT destino, mensaje, guia, creada_en FROM notificaciones", []
        if destino:
            sql += " WHERE destino = ?"
            params.append(destino)
        sql += " ORDER BY creada_en DESC"
        return self._db.consultar(sql, params)[:limite]


class GeneradorGuiaUuid(IGeneradorGuia):
    """Guía única: CB- + 10 caracteres hexadecimales en mayúsculas."""

    def generar(self) -> GuiaRastreo:
        return GuiaRastreo("CB-" + uuid.uuid4().hex[:10].upper())
