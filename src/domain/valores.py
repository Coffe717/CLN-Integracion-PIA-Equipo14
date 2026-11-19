"""Value Objects del dominio CargoBox.

Todos son inmutables (frozen) y se validan al construirse: un VO inválido
nunca llega a existir (ValorInvalidoException).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Optional

from src.domain.excepciones import (
    AutorizacionInvalidaException,
    ValorInvalidoException,
)

PESO_MAXIMO_KG = Decimal("70")
MEDIDA_MAXIMA_CM = Decimal("200")
DIVISOR_VOLUMETRICO = Decimal("5000")
ROLES_AUTORIZADORES = ("SUPERVISOR", "ATENCION_CLIENTE")


def ahora() -> datetime:
    return datetime.now(timezone.utc)


def a_decimal(valor, campo: str) -> Decimal:
    if isinstance(valor, bool) or valor is None:
        raise ValorInvalidoException(f"{campo} debe ser un número")
    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        raise ValorInvalidoException(f"{campo} debe ser un número") from None
    if not numero.is_finite():
        raise ValorInvalidoException(f"{campo} debe ser un número finito")
    return numero


def _texto(valor, campo: str) -> str:
    texto = (valor or "").strip() if isinstance(valor, str) else ""
    if not texto:
        raise ValorInvalidoException(f"{campo} es obligatorio")
    return texto


def _sin_acentos(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto)
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


class NivelServicio(str, Enum):
    ESTANDAR = "ESTANDAR"
    EXPRES = "EXPRES"

    @classmethod
    def desde(cls, valor) -> "NivelServicio":
        if isinstance(valor, cls):
            return valor
        if not isinstance(valor, str):
            raise ValorInvalidoException("Nivel de servicio inválido")
        limpio = _sin_acentos(valor).upper().replace("SERVICIO", "").strip()
        if limpio in ("ESTANDAR", "STANDARD"):
            return cls.ESTANDAR
        if limpio in ("EXPRES", "EXPRESS"):
            return cls.EXPRES
        raise ValorInvalidoException(f"Nivel de servicio desconocido: {valor}")


class Zona(str, Enum):
    LOCAL = "LOCAL"
    REGIONAL = "REGIONAL"
    NACIONAL = "NACIONAL"


@dataclass(frozen=True)
class Peso:
    kg: Decimal

    def __post_init__(self):
        kg = a_decimal(self.kg, "El peso")
        if kg <= 0:
            raise ValorInvalidoException("El peso debe ser mayor a 0 kg")
        if kg > PESO_MAXIMO_KG:
            raise ValorInvalidoException(f"El peso excede el máximo de {PESO_MAXIMO_KG} kg")
        object.__setattr__(self, "kg", kg)


@dataclass(frozen=True)
class Dimensiones:
    largo_cm: Decimal
    ancho_cm: Decimal
    alto_cm: Decimal

    def __post_init__(self):
        for campo in ("largo_cm", "ancho_cm", "alto_cm"):
            valor = a_decimal(getattr(self, campo), f"La medida {campo}")
            if valor <= 0:
                raise ValorInvalidoException(f"La medida {campo} debe ser mayor a 0 cm")
            if valor > MEDIDA_MAXIMA_CM:
                raise ValorInvalidoException(f"La medida {campo} excede {MEDIDA_MAXIMA_CM} cm")
            object.__setattr__(self, campo, valor)

    @property
    def volumen_cm3(self) -> Decimal:
        return self.largo_cm * self.ancho_cm * self.alto_cm

    @property
    def peso_volumetrico_kg(self) -> Decimal:
        return self.volumen_cm3 / DIVISOR_VOLUMETRICO


@dataclass(frozen=True)
class Dinero:
    monto: Decimal
    moneda: str = "MXN"

    def __post_init__(self):
        monto = a_decimal(self.monto, "El monto")
        if monto < 0:
            raise ValorInvalidoException("El monto no puede ser negativo")
        object.__setattr__(self, "monto", monto.quantize(Decimal("0.01"), ROUND_HALF_UP))

    def __str__(self) -> str:
        return f"${self.monto:,.2f} {self.moneda}"


@dataclass(frozen=True)
class Tarifa:
    """Resultado inmutable del cálculo: el precio no se modifica a mano (BR005)."""

    total: Dinero
    peso_facturable_kg: Decimal
    zona: Zona
    nivel: NivelServicio
    dias_entrega: int
    version_tabulador: str = "v1"


@dataclass(frozen=True)
class Direccion:
    calle: str
    ciudad: str

    def __post_init__(self):
        object.__setattr__(self, "calle", _texto(self.calle, "La calle y número"))
        object.__setattr__(self, "ciudad", _texto(self.ciudad, "La ciudad"))

    def __str__(self) -> str:
        return f"{self.calle}, {self.ciudad}"


_TEL = re.compile(r"^[0-9+\-\s()]{7,20}$")


@dataclass(frozen=True)
class Contacto:
    nombre: str
    telefono: str = ""

    def __post_init__(self):
        object.__setattr__(self, "nombre", _texto(self.nombre, "El nombre del contacto"))
        tel = (self.telefono or "").strip()
        if tel and not _TEL.match(tel):
            raise ValorInvalidoException("El teléfono no tiene un formato válido")
        object.__setattr__(self, "telefono", tel)


_GUIA = re.compile(r"^CB-[A-Z0-9]{10}$")


@dataclass(frozen=True)
class GuiaRastreo:
    codigo: str

    def __post_init__(self):
        codigo = (self.codigo or "").strip().upper() if isinstance(self.codigo, str) else ""
        if not _GUIA.match(codigo):
            raise ValorInvalidoException("La guía debe tener el formato CB-XXXXXXXXXX")
        object.__setattr__(self, "codigo", codigo)

    def __str__(self) -> str:
        return self.codigo


@dataclass(frozen=True)
class Instalacion:
    clave: str
    nombre: str = ""

    def __post_init__(self):
        object.__setattr__(self, "clave", _texto(self.clave, "La instalación"))
        object.__setattr__(self, "nombre", (self.nombre or self.clave).strip())


@dataclass(frozen=True)
class EvidenciaRecepcion:
    """Firma digital y/o fotografía de quien recibe (BR012, BR004)."""

    receptor: str
    firma: Optional[str] = None
    foto: Optional[str] = None
    capturada_en: datetime = None  # type: ignore[assignment]

    def __post_init__(self):
        object.__setattr__(self, "receptor", _texto(self.receptor, "El nombre de quien recibe"))
        firma = self.firma.strip() if isinstance(self.firma, str) and self.firma.strip() else None
        foto = self.foto.strip() if isinstance(self.foto, str) and self.foto.strip() else None
        if not (firma or foto):
            raise ValorInvalidoException("La evidencia necesita firma o fotografía")
        object.__setattr__(self, "firma", firma)
        object.__setattr__(self, "foto", foto)
        if self.capturada_en is None:
            object.__setattr__(self, "capturada_en", ahora())


@dataclass(frozen=True)
class AutorizacionReintento:
    """Autorización explícita para un tercer intento (BR014)."""

    autorizador: str
    rol: str
    fecha: datetime = None  # type: ignore[assignment]

    def __post_init__(self):
        object.__setattr__(self, "autorizador", _texto(self.autorizador, "El autorizador"))
        rol = (self.rol or "").strip().upper() if isinstance(self.rol, str) else ""
        if rol not in ROLES_AUTORIZADORES:
            raise AutorizacionInvalidaException(
                "Solo un supervisor o Atención al cliente puede autorizar un tercer intento"
            )
        object.__setattr__(self, "rol", rol)
        if self.fecha is None:
            object.__setattr__(self, "fecha", ahora())
