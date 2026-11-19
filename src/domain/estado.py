"""Máquina de estados del envío (State Machine).

La tabla TRANSICIONES es la única fuente de verdad del ciclo de vida:
cualquier cambio de estado pasa por `MaquinaEstados.transicionar`.
"""
from __future__ import annotations

from enum import Enum

from src.domain.excepciones import TransicionEstadoInvalidaException


class EstadoEnvio(str, Enum):
    RECIBIDO = "RECIBIDO"
    CLASIFICADO = "CLASIFICADO"
    EN_TRANSITO = "EN_TRANSITO"
    CENTRO_DESTINO = "CENTRO_DESTINO"
    EN_REPARTO = "EN_REPARTO"
    ENTREGADO = "ENTREGADO"
    SEGUNDO_INTENTO_PENDIENTE = "SEGUNDO_INTENTO_PENDIENTE"
    RETENIDO_EN_SUCURSAL = "RETENIDO_EN_SUCURSAL"
    DIRECCION_INCORRECTA = "DIRECCION_INCORRECTA"
    RETENIDO_POR_INCIDENCIA = "RETENIDO_POR_INCIDENCIA"
    RECHAZADO_EN_DEVOLUCION = "RECHAZADO_EN_DEVOLUCION"
    DEVUELTO_A_ORIGEN = "DEVUELTO_A_ORIGEN"
    CANCELADO = "CANCELADO"


E = EstadoEnvio

TRANSICIONES = {
    E.RECIBIDO: {E.CLASIFICADO, E.CANCELADO},
    E.CLASIFICADO: {E.EN_TRANSITO},
    E.EN_TRANSITO: {E.CENTRO_DESTINO},
    E.CENTRO_DESTINO: {E.EN_REPARTO},
    E.EN_REPARTO: {
        E.ENTREGADO,
        E.SEGUNDO_INTENTO_PENDIENTE,
        E.RETENIDO_EN_SUCURSAL,
        E.DIRECCION_INCORRECTA,
        E.RETENIDO_POR_INCIDENCIA,
        E.RECHAZADO_EN_DEVOLUCION,
    },
    E.SEGUNDO_INTENTO_PENDIENTE: {E.EN_REPARTO},
    E.DIRECCION_INCORRECTA: {E.EN_REPARTO},
    E.RETENIDO_POR_INCIDENCIA: {E.EN_REPARTO},
    E.RETENIDO_EN_SUCURSAL: {E.EN_REPARTO, E.RECHAZADO_EN_DEVOLUCION},
    E.RECHAZADO_EN_DEVOLUCION: {E.DEVUELTO_A_ORIGEN},
    E.ENTREGADO: set(),
    E.DEVUELTO_A_ORIGEN: set(),
    E.CANCELADO: set(),
}

ESTADOS_TERMINALES = frozenset(e for e, destinos in TRANSICIONES.items() if not destinos)

ETIQUETAS = {
    E.RECIBIDO: "Recibido",
    E.CLASIFICADO: "Clasificado",
    E.EN_TRANSITO: "En tránsito",
    E.CENTRO_DESTINO: "Centro destino",
    E.EN_REPARTO: "En reparto",
    E.ENTREGADO: "Entregado",
    E.SEGUNDO_INTENTO_PENDIENTE: "Segundo intento pendiente",
    E.RETENIDO_EN_SUCURSAL: "Retenido en sucursal",
    E.DIRECCION_INCORRECTA: "Dirección incorrecta (entrega pausada)",
    E.RETENIDO_POR_INCIDENCIA: "Retenido por incidencia",
    E.RECHAZADO_EN_DEVOLUCION: "Rechazado - En proceso de devolución",
    E.DEVUELTO_A_ORIGEN: "Devuelto a origen",
    E.CANCELADO: "Cancelado",
}


class MaquinaEstados:
    def __init__(self, estado: EstadoEnvio = EstadoEnvio.RECIBIDO):
        self._estado = EstadoEnvio(estado)

    @property
    def estado(self) -> EstadoEnvio:
        return self._estado

    def puede(self, destino: EstadoEnvio) -> bool:
        return EstadoEnvio(destino) in TRANSICIONES[self._estado]

    def validar(self, destino: EstadoEnvio) -> None:
        destino = EstadoEnvio(destino)
        if destino not in TRANSICIONES[self._estado]:
            raise TransicionEstadoInvalidaException(
                f"Transición inválida: {ETIQUETAS[self._estado]} → {ETIQUETAS[destino]}"
            )

    def transicionar(self, destino: EstadoEnvio) -> EstadoEnvio:
        self.validar(destino)
        self._estado = EstadoEnvio(destino)
        return self._estado

    @property
    def es_terminal(self) -> bool:
        return self._estado in ESTADOS_TERMINALES
