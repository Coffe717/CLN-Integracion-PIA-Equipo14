"""Publicador de eventos de dominio en proceso (Observer) y manejadores."""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable, Dict, List

from src.application.puertos import INotificador
from src.domain import eventos as ev
from src.domain.eventos import EventoDominio

log = logging.getLogger("cargobox.eventos")


class PublicadorEventos:
    def __init__(self):
        self._manejadores: Dict[type, List[Callable[[EventoDominio], None]]] = defaultdict(list)
        self.historial: List[EventoDominio] = []

    def suscribir(self, tipo: type, manejador: Callable[[EventoDominio], None]) -> None:
        self._manejadores[tipo].append(manejador)

    def publicar(self, evento: EventoDominio) -> None:
        self.historial.append(evento)
        log.info("evento %s guia=%s", evento.nombre, evento.guia)
        for manejador in self._manejadores.get(type(evento), []):
            manejador(evento)

    def publicar_todos(self, eventos) -> None:
        for evento in eventos:
            self.publicar(evento)


class ManejadorNotificaciones:
    """Convierte eventos del negocio en avisos para Atención al cliente / Supervisor."""

    def __init__(self, notificador: INotificador):
        self.notificador = notificador

    def registrar_en(self, publicador: PublicadorEventos) -> None:
        publicador.suscribir(ev.EntregaPausada, self._direccion_incorrecta)
        publicador.suscribir(ev.PaqueteRetenidoPorIncidencia, self._incidencia_mayor)
        publicador.suscribir(ev.TercerIntentoRequiereAutorizacion, self._tercer_intento)
        publicador.suscribir(ev.PaqueteEstancadoDetectado, self._estancado)
        publicador.suscribir(ev.DevolucionIniciada, self._devolucion)
        publicador.suscribir(ev.PaqueteEntregado, self._entregado)

    def _direccion_incorrecta(self, e):
        self.notificador.notificar("ATENCION_CLIENTE", "Ticket: dirección incorrecta, corregir y reintentar", e.guia)

    def _incidencia_mayor(self, e):
        self.notificador.notificar("ATENCION_CLIENTE",
                                   f"Ticket: incidencia mayor ({e.detalle.get('tipo', '')}) por evaluar", e.guia)

    def _tercer_intento(self, e):
        self.notificador.notificar("SUPERVISOR", "Dos intentos fallidos: un tercer intento requiere autorización", e.guia)

    def _estancado(self, e):
        self.notificador.notificar("SUPERVISOR",
                                   f"Paquete estancado {e.detalle.get('horas', '?')} h en {e.detalle.get('estado', '')}", e.guia)

    def _devolucion(self, e):
        self.notificador.notificar("ATENCION_CLIENTE", "Paquete rechazado: devolución a sucursal de origen iniciada", e.guia)

    def _entregado(self, e):
        self.notificador.notificar("ATENCION_CLIENTE",
                                   f"Entrega concluida con evidencia (recibió {e.detalle.get('receptor', '')})", e.guia)
