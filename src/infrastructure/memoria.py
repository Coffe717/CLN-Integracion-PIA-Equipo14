"""Implementaciones en memoria de los puertos (pruebas unitarias y modo demo ligero)."""
from __future__ import annotations

import copy
import itertools
from typing import List, Optional

from src.application.puertos import (
    IIncidenciaRepository, IManifiestoRepository, INotificador, IPaqueteRepository,
    IRemitenteRepository, IRutaRepository, IUnitOfWork,
)
from src.domain.valores import ahora


class AlmacenMemoria:
    """Contenedor de datos compartido por los repositorios y la Unit of Work."""

    def __init__(self):
        self.paquetes, self.remitentes, self.incidencias = {}, {}, {}
        self.manifiestos, self.rutas, self.notificaciones = {}, {}, []

    def snapshot(self):
        return copy.deepcopy((self.paquetes, self.remitentes, self.incidencias,
                              self.manifiestos, self.rutas, self.notificaciones))

    def restaurar(self, instantanea):
        (self.paquetes, self.remitentes, self.incidencias,
         self.manifiestos, self.rutas, self.notificaciones) = instantanea


class MemoriaUnitOfWork(IUnitOfWork):
    """Rollback real: si el caso de uso falla se restaura el estado anterior."""

    def __init__(self, almacen: AlmacenMemoria):
        self._almacen = almacen
        self._pila: list = []

    def __enter__(self):
        self._pila.append(self._almacen.snapshot())
        return self

    def __exit__(self, tipo, valor, tb):
        instantanea = self._pila.pop()
        if tipo is not None:
            self._almacen.restaurar(instantanea)
        return False


class _RepoMemoria:
    def __init__(self, almacen: AlmacenMemoria):
        self._a = almacen


class MemoriaPaqueteRepository(_RepoMemoria, IPaqueteRepository):
    def obtener_por_guia(self, guia: str) -> Optional[object]:
        return copy.deepcopy(self._a.paquetes.get(guia))

    def guardar(self, paquete) -> None:
        self._a.paquetes[str(paquete.guia)] = copy.deepcopy(paquete)

    def listar(self, estado=None, remitente_id=None) -> List:
        resultado = [copy.deepcopy(p) for p in self._a.paquetes.values()
                     if (not estado or p.estado.value == estado)
                     and (not remitente_id or p.remitente_id == remitente_id)]
        return sorted(resultado, key=lambda p: p.actualizado_en, reverse=True)


class MemoriaRemitenteRepository(_RepoMemoria, IRemitenteRepository):
    def obtener(self, remitente_id: str):
        return copy.deepcopy(self._a.remitentes.get(remitente_id))

    def guardar(self, remitente) -> None:
        self._a.remitentes[remitente.id] = copy.deepcopy(remitente)

    def listar(self) -> List:
        return [copy.deepcopy(r) for _, r in sorted(self._a.remitentes.items())]


class MemoriaIncidenciaRepository(_RepoMemoria, IIncidenciaRepository):
    def obtener(self, incidencia_id: str):
        return copy.deepcopy(self._a.incidencias.get(incidencia_id))

    def guardar(self, incidencia) -> None:
        self._a.incidencias[incidencia.id] = copy.deepcopy(incidencia)

    def listar(self, estado=None, guia=None) -> List:
        resultado = [copy.deepcopy(i) for i in self._a.incidencias.values()
                     if (not estado or i.estado.value == estado) and (not guia or i.guia == guia)]
        return sorted(resultado, key=lambda i: i.creada_en, reverse=True)


class MemoriaManifiestoRepository(_RepoMemoria, IManifiestoRepository):
    def obtener(self, manifiesto_id: str):
        return copy.deepcopy(self._a.manifiestos.get(manifiesto_id))

    def guardar(self, manifiesto) -> None:
        self._a.manifiestos[manifiesto.id] = copy.deepcopy(manifiesto)


class MemoriaRutaRepository(_RepoMemoria, IRutaRepository):
    def obtener(self, ruta_id: str):
        return copy.deepcopy(self._a.rutas.get(ruta_id))

    def guardar(self, ruta) -> None:
        self._a.rutas[ruta.id] = copy.deepcopy(ruta)


class MemoriaNotificador(_RepoMemoria, INotificador):
    def notificar(self, destino: str, mensaje: str, guia: str = "") -> None:
        self._a.notificaciones.append({"destino": destino, "mensaje": mensaje, "guia": guia,
                                       "creada_en": ahora().isoformat()})

    def listar(self, destino: Optional[str] = None, limite: int = 50) -> List[dict]:
        datos = [n for n in reversed(self._a.notificaciones) if not destino or n["destino"] == destino]
        return datos[:limite]


class GeneradorGuiaSecuencial:
    """Generador determinista para pruebas: CB-0000000001, CB-0000000002..."""

    def __init__(self, inicio: int = 1):
        self._contador = itertools.count(inicio)

    def generar(self):
        from src.domain.valores import GuiaRastreo

        return GuiaRastreo(f"CB-{next(self._contador):010d}")
