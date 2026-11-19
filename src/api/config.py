"""Configuración por variables de entorno (12-Factor App): nada de secretos en el código."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(valor: str, defecto: bool) -> bool:
    if valor is None or valor == "":
        return defecto
    return valor.strip().lower() in ("1", "true", "si", "sí", "yes")


@dataclass(frozen=True)
class Config:
    database_url: str = "sqlite:///data/cargobox.db"
    seed_demo: bool = True
    umbral_horas: float = 24.0
    port: int = 8000

    @classmethod
    def desde_entorno(cls) -> "Config":
        return cls(
            database_url=os.getenv("DATABASE_URL", cls.database_url),
            seed_demo=_bool(os.getenv("SEED_DEMO"), cls.seed_demo),
            umbral_horas=float(os.getenv("UMBRAL_HORAS", cls.umbral_horas)),
            port=int(os.getenv("PORT", cls.port)),
        )
