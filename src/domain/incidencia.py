"""Aggregate Root Incidencia: dirección incorrecta, daño o pérdida (BR003, BR013)."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain import eventos as ev
from src.domain.excepciones import ReglaNegocioException, ResolucionNoPermitidaException, ValorInvalidoException
from src.domain.valores import ahora


class TipoIncidencia(str, Enum):
    DIRECCION_INCORRECTA = "DIRECCION_INCORRECTA"
    DANO = "DANO"
    PERDIDA = "PERDIDA"


class EstadoIncidencia(str, Enum):
    ABIERTA = "ABIERTA"
    RESUELTA = "RESUELTA"


class Incidencia:
    def __init__(self, id: str, guia: str, tipo: TipoIncidencia, descripcion: str,
                 reportada_por: str, estado: EstadoIncidencia = EstadoIncidencia.ABIERTA,
                 creada_en: Optional[datetime] = None, resuelta_en: Optional[datetime] = None,
                 resolucion: str = "", resuelta_por: str = ""):
        self.id = id
        self.guia = guia
        self.tipo = TipoIncidencia(tipo)
        self.descripcion = descripcion
        self.reportada_por = reportada_por
        self.estado = EstadoIncidencia(estado)
        self.asignada_a = "ATENCION_CLIENTE"
        self.creada_en = creada_en or ahora()
        self.resuelta_en = resuelta_en
        self.resolucion = resolucion
        self.resuelta_por = resuelta_por
        self._eventos: list = []

    @classmethod
    def abrir(cls, guia: str, tipo, descripcion: str, reportada_por: str = "",
              momento: Optional[datetime] = None) -> "Incidencia":
        momento = momento or ahora()
        incidencia = cls("INC-" + uuid.uuid4().hex[:8].upper(), guia, TipoIncidencia(tipo),
                         (descripcion or "").strip(), reportada_por, creada_en=momento)
        incidencia._eventos.append(ev.IncidenciaAbierta(guia, momento, {"tipo": incidencia.tipo.value}))
        return incidencia

    def resolver(self, agente: str, rol: str, resolucion: str, momento: Optional[datetime] = None) -> None:
        """Solo Atención al cliente puede resolver (BR003)."""
        if (rol or "").strip().upper() != "ATENCION_CLIENTE":
            raise ResolucionNoPermitidaException(
                "Solo Atención al cliente puede resolver una incidencia")
        if self.estado is EstadoIncidencia.RESUELTA:
            raise ReglaNegocioException("La incidencia ya fue resuelta")
        if not (resolucion or "").strip():
            raise ValorInvalidoException("La resolución es obligatoria")
        momento = momento or ahora()
        self.estado = EstadoIncidencia.RESUELTA
        self.resolucion = resolucion.strip()
        self.resuelta_por = agente
        self.resuelta_en = momento
        self._eventos.append(ev.IncidenciaResuelta(self.guia, momento, {"id": self.id}))

    def pull_events(self) -> list:
        eventos, self._eventos = self._eventos, []
        return eventos
