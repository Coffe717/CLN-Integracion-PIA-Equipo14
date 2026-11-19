"""Puertos (interfaces) que la aplicación necesita; la infraestructura los implementa.

Así el dominio y los casos de uso no dependen de la base de datos (DIP).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.incidencia import Incidencia
from src.domain.manifiesto import ManifiestoViaje, RutaReparto
from src.domain.paquete import Paquete
from src.domain.remitente import Remitente
from src.domain.valores import GuiaRastreo


class IPaqueteRepository(ABC):
    @abstractmethod
    def obtener_por_guia(self, guia: str) -> Optional[Paquete]: ...

    @abstractmethod
    def guardar(self, paquete: Paquete) -> None: ...

    @abstractmethod
    def listar(self, estado: Optional[str] = None, remitente_id: Optional[str] = None) -> List[Paquete]: ...


class IRemitenteRepository(ABC):
    @abstractmethod
    def obtener(self, remitente_id: str) -> Optional[Remitente]: ...

    @abstractmethod
    def guardar(self, remitente: Remitente) -> None: ...

    @abstractmethod
    def listar(self) -> List[Remitente]: ...


class IIncidenciaRepository(ABC):
    @abstractmethod
    def obtener(self, incidencia_id: str) -> Optional[Incidencia]: ...

    @abstractmethod
    def guardar(self, incidencia: Incidencia) -> None: ...

    @abstractmethod
    def listar(self, estado: Optional[str] = None, guia: Optional[str] = None) -> List[Incidencia]: ...


class IManifiestoRepository(ABC):
    @abstractmethod
    def obtener(self, manifiesto_id: str) -> Optional[ManifiestoViaje]: ...

    @abstractmethod
    def guardar(self, manifiesto: ManifiestoViaje) -> None: ...


class IRutaRepository(ABC):
    @abstractmethod
    def obtener(self, ruta_id: str) -> Optional[RutaReparto]: ...

    @abstractmethod
    def guardar(self, ruta: RutaReparto) -> None: ...


class INotificador(ABC):
    @abstractmethod
    def notificar(self, destino: str, mensaje: str, guia: str = "") -> None: ...

    @abstractmethod
    def listar(self, destino: Optional[str] = None, limite: int = 50) -> List[dict]: ...


class IGeneradorGuia(ABC):
    @abstractmethod
    def generar(self) -> GuiaRastreo: ...


class IUnitOfWork(ABC):
    """Una transacción atómica por caso de uso (patrón Unit of Work)."""

    @abstractmethod
    def __enter__(self): ...

    @abstractmethod
    def __exit__(self, tipo, valor, tb): ...
