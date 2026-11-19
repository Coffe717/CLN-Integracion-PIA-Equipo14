"""Entidad Remitente (cliente que entrega un paquete en sucursal)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Remitente:
    id: str
    nombre: str
    activo: bool = True
    preferente: bool = False
    ciudad: str = ""
