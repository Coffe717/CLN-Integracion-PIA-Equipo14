"""Aggregates ManifiestoViaje (traslado interurbano) y RutaReparto (jornada del repartidor)."""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.domain import eventos as ev
from src.domain.excepciones import ReglaNegocioException, ValorInvalidoException
from src.domain.valores import Instalacion, ahora


class EstadoManifiesto(str, Enum):
    ABIERTO = "ABIERTO"
    DESPACHADO = "DESPACHADO"
    ARRIBADO = "ARRIBADO"


class ManifiestoViaje:
    def __init__(self, id: str, origen: Instalacion, destino: Instalacion,
                 guias: Optional[List[str]] = None, estado: EstadoManifiesto = EstadoManifiesto.ABIERTO,
                 despachado_en: Optional[datetime] = None, arribado_en: Optional[datetime] = None):
        self.id = id
        self.origen = origen
        self.destino = destino
        self.guias: List[str] = list(guias or [])
        self.estado = EstadoManifiesto(estado)
        self.despachado_en = despachado_en
        self.arribado_en = arribado_en
        self._eventos: list = []

    @classmethod
    def crear(cls, origen: Instalacion, destino: Instalacion, guias: List[str]) -> "ManifiestoViaje":
        if not guias:
            raise ValorInvalidoException("El manifiesto necesita al menos una guía")
        return cls("MAN-" + uuid.uuid4().hex[:8].upper(), origen, destino, list(dict.fromkeys(guias)))

    def despachar(self, momento: Optional[datetime] = None) -> None:
        if self.estado is not EstadoManifiesto.ABIERTO:
            raise ReglaNegocioException("El manifiesto ya fue despachado")
        if not self.guias:
            raise ValorInvalidoException("No se puede despachar un manifiesto vacío")
        self.estado = EstadoManifiesto.DESPACHADO
        self.despachado_en = momento or ahora()
        self._eventos.append(ev.ManifiestoDespachado(self.id, self.despachado_en, {"guias": len(self.guias)}))

    def arribar(self, momento: Optional[datetime] = None) -> None:
        if self.estado is not EstadoManifiesto.DESPACHADO:
            raise ReglaNegocioException("Solo un manifiesto despachado puede arribar")
        self.estado = EstadoManifiesto.ARRIBADO
        self.arribado_en = momento or ahora()
        self._eventos.append(ev.ManifiestoArribado(self.id, self.arribado_en, {}))

    def pull_events(self) -> list:
        eventos, self._eventos = self._eventos, []
        return eventos


class EstadoRuta(str, Enum):
    PLANEADA = "PLANEADA"
    EN_CURSO = "EN_CURSO"
    CERRADA = "CERRADA"


class RutaReparto:
    def __init__(self, id: str, repartidor: str, guias: Optional[List[str]] = None,
                 estado: EstadoRuta = EstadoRuta.PLANEADA, iniciada_en: Optional[datetime] = None,
                 cerrada_en: Optional[datetime] = None):
        self.id = id
        self.repartidor = repartidor
        self.guias: List[str] = list(guias or [])
        self.estado = EstadoRuta(estado)
        self.iniciada_en = iniciada_en
        self.cerrada_en = cerrada_en
        self._eventos: list = []

    @classmethod
    def crear(cls, repartidor: str, guias: List[str]) -> "RutaReparto":
        if not (repartidor or "").strip():
            raise ValorInvalidoException("El repartidor es obligatorio")
        if not guias:
            raise ValorInvalidoException("La ruta necesita al menos una guía")
        return cls("RUT-" + uuid.uuid4().hex[:8].upper(), repartidor.strip(), list(dict.fromkeys(guias)))

    def iniciar(self, momento: Optional[datetime] = None) -> None:
        if self.estado is not EstadoRuta.PLANEADA:
            raise ReglaNegocioException("La ruta ya fue iniciada")
        self.estado = EstadoRuta.EN_CURSO
        self.iniciada_en = momento or ahora()
        self._eventos.append(ev.RutaIniciada(self.id, self.iniciada_en, {"repartidor": self.repartidor}))

    def cerrar(self, momento: Optional[datetime] = None) -> None:
        if self.estado is not EstadoRuta.EN_CURSO:
            raise ReglaNegocioException("Solo una ruta en curso puede cerrarse")
        self.estado = EstadoRuta.CERRADA
        self.cerrada_en = momento or ahora()
        self._eventos.append(ev.RutaCerrada(self.id, self.cerrada_en, {}))

    def pull_events(self) -> list:
        eventos, self._eventos = self._eventos, []
        return eventos
