"""Patrón Specification: reglas de negocio componibles con AND / OR / NOT.

Uso:  spec = A() & B() | ~C()   →   spec.is_satisfied_by(candidato)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.domain.estado import ESTADOS_TERMINALES, EstadoEnvio
from src.domain.valores import ahora


class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, candidato) -> bool: ...

    def __and__(self, otra: "Specification") -> "Specification":
        return AndSpecification(self, otra)

    def __or__(self, otra: "Specification") -> "Specification":
        return OrSpecification(self, otra)

    def __invert__(self) -> "Specification":
        return NotSpecification(self)


class AndSpecification(Specification):
    def __init__(self, izq: Specification, der: Specification):
        self.izq, self.der = izq, der

    def is_satisfied_by(self, candidato) -> bool:
        return self.izq.is_satisfied_by(candidato) and self.der.is_satisfied_by(candidato)


class OrSpecification(Specification):
    def __init__(self, izq: Specification, der: Specification):
        self.izq, self.der = izq, der

    def is_satisfied_by(self, candidato) -> bool:
        return self.izq.is_satisfied_by(candidato) or self.der.is_satisfied_by(candidato)


class NotSpecification(Specification):
    def __init__(self, spec: Specification):
        self.spec = spec

    def is_satisfied_by(self, candidato) -> bool:
        return not self.spec.is_satisfied_by(candidato)


# ----------------------------------------------------------------- sobre Paquete
class EstadoEnSpec(Specification):
    def __init__(self, *estados: EstadoEnvio):
        self.estados = set(estados)

    def is_satisfied_by(self, paquete) -> bool:
        return paquete.estado in self.estados


class EsTerminalSpec(Specification):
    def is_satisfied_by(self, paquete) -> bool:
        return paquete.estado in ESTADOS_TERMINALES


class SinActualizacionSpec(Specification):
    """Verdadera si el paquete lleva más de `umbral_horas` sin cambios (BR002)."""

    def __init__(self, umbral_horas: float, momento: Optional[datetime] = None):
        self.umbral_horas = umbral_horas
        self.momento = momento

    def is_satisfied_by(self, paquete) -> bool:
        return paquete.horas_sin_actualizacion(self.momento or ahora()) > self.umbral_horas


class PaqueteEstancadoSpec(Specification):
    """Estancado = NO terminal AND sin actualización > umbral."""

    def __init__(self, umbral_horas: float, momento: Optional[datetime] = None):
        self._spec = ~EsTerminalSpec() & SinActualizacionSpec(umbral_horas, momento)

    def is_satisfied_by(self, paquete) -> bool:
        return self._spec.is_satisfied_by(paquete)


class IntentosAgotadosSpec(Specification):
    def __init__(self, limite: int = 2):
        self.limite = limite

    def is_satisfied_by(self, paquete) -> bool:
        return paquete.intentos_fallidos >= self.limite


class TieneAutorizacionSpec(Specification):
    def is_satisfied_by(self, paquete) -> bool:
        return paquete.autorizacion is not None


class RequiereAutorizacionTercerIntentoSpec(Specification):
    """BR014: intentos agotados AND NOT autorizado."""

    def __init__(self):
        self._spec = IntentosAgotadosSpec() & ~TieneAutorizacionSpec()

    def is_satisfied_by(self, paquete) -> bool:
        return self._spec.is_satisfied_by(paquete)


class PuedeEntregarseSpec(Specification):
    """En reparto AND (con evidencia disponible en el candidato)."""

    def is_satisfied_by(self, paquete) -> bool:
        return EstadoEnSpec(EstadoEnvio.EN_REPARTO).is_satisfied_by(paquete)


# ----------------------------------------------------------------- sobre Remitente
class RemitenteActivoSpec(Specification):
    def is_satisfied_by(self, remitente) -> bool:
        return bool(remitente.activo)


class RemitentePreferenteSpec(Specification):
    def is_satisfied_by(self, remitente) -> bool:
        return bool(remitente.preferente)


class PuedeEnviarSpec(Specification):
    """Un remitente puede registrar envíos si está activo."""

    def __init__(self):
        self._spec = RemitenteActivoSpec()

    def is_satisfied_by(self, remitente) -> bool:
        return self._spec.is_satisfied_by(remitente)
