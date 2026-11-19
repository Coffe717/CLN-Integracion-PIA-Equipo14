"""Tabulador de tarifas y servicio de dominio CalculadoraTarifa (BR005).

Regla: peso facturable = max(peso real, peso volumétrico).
Precio = precio base del tramo × factor de zona × factor de nivel de servicio.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple

from src.domain.excepciones import ValorInvalidoException
from src.domain.valores import (
    Dimensiones,
    Dinero,
    NivelServicio,
    Peso,
    Tarifa,
    Zona,
)


@dataclass(frozen=True)
class ReglaTarifa:
    """Entidad interna del agregado TabuladorTarifas: un tramo de peso."""

    limite_kg: Decimal
    precio_base: Decimal


CIUDADES_LOCALES = {
    "monterrey", "apodaca", "san nicolas de los garza", "san nicolas", "guadalupe",
    "san pedro garza garcia", "san pedro", "santa catarina", "escobedo",
    "general escobedo", "juarez", "garcia", "cadereyta",
}
CIUDADES_REGIONALES = {
    "saltillo", "reynosa", "matamoros", "tampico", "victoria", "ciudad victoria",
    "san luis potosi", "monclova", "nuevo laredo", "torreon", "linares", "montemorelos",
}


def _limpiar(ciudad: str) -> str:
    import unicodedata

    base = unicodedata.normalize("NFD", (ciudad or "").strip().lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


class TabuladorTarifas:
    """Aggregate Root versionado con las reglas de precio."""

    def __init__(self, version: str = "v1"):
        self.version = version
        self.reglas: Tuple[ReglaTarifa, ...] = tuple(
            ReglaTarifa(Decimal(limite), Decimal(precio))
            for limite, precio in (
                ("1", "60"), ("3", "90"), ("5", "120"), ("10", "150"),
                ("20", "230"), ("30", "330"), ("70", "520"),
            )
        )
        self.factor_zona = {Zona.LOCAL: Decimal("1.00"), Zona.REGIONAL: Decimal("1.25"), Zona.NACIONAL: Decimal("1.60")}
        self.factor_nivel = {NivelServicio.ESTANDAR: Decimal("1.00"), NivelServicio.EXPRES: Decimal("1.50")}
        self.dias = {
            NivelServicio.ESTANDAR: {Zona.LOCAL: 2, Zona.REGIONAL: 4, Zona.NACIONAL: 6},
            NivelServicio.EXPRES: {Zona.LOCAL: 1, Zona.REGIONAL: 2, Zona.NACIONAL: 3},
        }

    def zona_para(self, ciudad_destino: str) -> Zona:
        ciudad = _limpiar(ciudad_destino)
        if ciudad in CIUDADES_LOCALES:
            return Zona.LOCAL
        if ciudad in CIUDADES_REGIONALES:
            return Zona.REGIONAL
        return Zona.NACIONAL

    def precio_base(self, peso_facturable: Decimal) -> Decimal:
        for regla in self.reglas:
            if peso_facturable <= regla.limite_kg:
                return regla.precio_base
        raise ValorInvalidoException("El peso facturable excede el máximo del tabulador")


class CalculadoraTarifa:
    """Servicio de dominio: cálculo estricto de la tarifa, sin edición manual."""

    def __init__(self, tabulador: TabuladorTarifas | None = None):
        self.tabulador = tabulador or TabuladorTarifas()

    def calcular(self, peso: Peso, dimensiones: Dimensiones, ciudad_destino: str,
                 nivel: NivelServicio) -> Tarifa:
        if not isinstance(peso, Peso) or not isinstance(dimensiones, Dimensiones):
            raise ValorInvalidoException("Peso y dimensiones deben ser Value Objects válidos")
        nivel = NivelServicio.desde(nivel)
        zona = self.tabulador.zona_para(ciudad_destino)
        facturable = max(peso.kg, dimensiones.peso_volumetrico_kg).quantize(
            Decimal("0.01"), ROUND_HALF_UP)
        base = self.tabulador.precio_base(facturable)
        total = (base * self.tabulador.factor_zona[zona] * self.tabulador.factor_nivel[nivel])
        return Tarifa(
            total=Dinero(total),
            peso_facturable_kg=facturable,
            zona=zona,
            nivel=nivel,
            dias_entrega=self.tabulador.dias[nivel][zona],
            version_tabulador=self.tabulador.version,
        )
