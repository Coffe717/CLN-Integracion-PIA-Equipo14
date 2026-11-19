"""Composition root: arma los servicios con las implementaciones de infraestructura."""
from __future__ import annotations

from dataclasses import dataclass

from src.application.eventos import ManejadorNotificaciones, PublicadorEventos
from src.application.servicios import (
    ConsultaRastreoService, CotizacionService, EntregaService, IncidenciaService,
    MonitoreoService, OperacionLogisticaService, RecepcionService,
)
from src.domain.tabulador import CalculadoraTarifa
from src.infrastructure import memoria as mem
from src.infrastructure import repositorios_sql as sql
from src.infrastructure.db import Database


@dataclass
class Contenedor:
    cotizacion: CotizacionService
    recepcion: RecepcionService
    logistica: OperacionLogisticaService
    entrega: EntregaService
    incidencias: IncidenciaService
    monitoreo: MonitoreoService
    consulta: ConsultaRastreoService
    remitentes: object
    publicador: PublicadorEventos
    db: object = None


def _armar(paquetes, remitentes, incidencias, manifiestos, rutas, notificador, generador, uow, db=None):
    calculadora = CalculadoraTarifa()
    publicador = PublicadorEventos()
    ManejadorNotificaciones(notificador).registrar_en(publicador)
    return Contenedor(
        cotizacion=CotizacionService(calculadora),
        recepcion=RecepcionService(paquetes, remitentes, calculadora, generador, uow, publicador),
        logistica=OperacionLogisticaService(paquetes, manifiestos, uow, publicador),
        entrega=EntregaService(paquetes, rutas, uow, publicador),
        incidencias=IncidenciaService(paquetes, incidencias, uow, publicador),
        monitoreo=MonitoreoService(paquetes, uow, publicador),
        consulta=ConsultaRastreoService(paquetes, incidencias, remitentes, notificador),
        remitentes=remitentes, publicador=publicador, db=db,
    )


def construir_sql(database_url: str) -> Contenedor:
    db = Database(database_url)
    return _armar(sql.SqlPaqueteRepository(db), sql.SqlRemitenteRepository(db),
                  sql.SqlIncidenciaRepository(db), sql.SqlManifiestoRepository(db),
                  sql.SqlRutaRepository(db), sql.SqlNotificador(db), sql.GeneradorGuiaUuid(),
                  sql.SqlUnitOfWork(db), db)


def construir_memoria() -> Contenedor:
    almacen = mem.AlmacenMemoria()
    return _armar(mem.MemoriaPaqueteRepository(almacen), mem.MemoriaRemitenteRepository(almacen),
                  mem.MemoriaIncidenciaRepository(almacen), mem.MemoriaManifiestoRepository(almacen),
                  mem.MemoriaRutaRepository(almacen), mem.MemoriaNotificador(almacen),
                  mem.GeneradorGuiaSecuencial(), mem.MemoriaUnitOfWork(almacen))
