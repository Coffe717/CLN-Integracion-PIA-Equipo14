"""Eventos de dominio: hechos del negocio ya ocurridos (en pasado)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from src.domain.valores import ahora


@dataclass(frozen=True)
class EventoDominio:
    guia: str
    ocurrido_en: datetime = field(default_factory=ahora)
    detalle: Dict[str, Any] = field(default_factory=dict)

    @property
    def nombre(self) -> str:
        return type(self).__name__


class PaqueteRecibido(EventoDominio): pass
class PaqueteClasificado(EventoDominio): pass
class PaqueteEnTransito(EventoDominio): pass
class PaqueteLlegoACentroDestino(EventoDominio): pass
class PaqueteEnReparto(EventoDominio): pass
class PaqueteEntregado(EventoDominio): pass
class PaqueteCancelado(EventoDominio): pass
class SegundoIntentoProgramado(EventoDominio): pass
class TercerIntentoRequiereAutorizacion(EventoDominio): pass
class TercerIntentoAutorizado(EventoDominio): pass
class PaqueteRetenidoEnSucursal(EventoDominio): pass
class EntregaPausada(EventoDominio): pass
class PaqueteRetenidoPorIncidencia(EventoDominio): pass
class PaqueteRechazado(EventoDominio): pass
class DevolucionIniciada(EventoDominio): pass
class DevolucionCompletada(EventoDominio): pass
class DireccionCorregida(EventoDominio): pass
class PaqueteEstancadoDetectado(EventoDominio): pass
class IncidenciaAbierta(EventoDominio): pass
class IncidenciaResuelta(EventoDominio): pass
class ManifiestoDespachado(EventoDominio): pass
class ManifiestoArribado(EventoDominio): pass
class RutaIniciada(EventoDominio): pass
class RutaCerrada(EventoDominio): pass
