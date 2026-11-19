"""Aggregate Root `Paquete`: ciclo de vida del envío y sus invariantes.

Los métodos tienen nombre de negocio (finalizar_entrega, registrar_ausencia...)
y son el único camino para cambiar el estado (BR005-BR014).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from src.domain import eventos as ev
from src.domain.estado import ESTADOS_TERMINALES, ETIQUETAS, EstadoEnvio, MaquinaEstados
from src.domain.excepciones import (
    EvidenciaObligatoriaException,
    ReglaNegocioException,
    TercerIntentoNoAutorizadoException,
    ValorInvalidoException,
)
from src.domain.tabulador import CalculadoraTarifa
from src.domain.valores import (
    AutorizacionReintento,
    Contacto,
    Dimensiones,
    Direccion,
    EvidenciaRecepcion,
    GuiaRastreo,
    Instalacion,
    NivelServicio,
    Peso,
    Tarifa,
    ahora,
)

LIMITE_INTENTOS_AUTOMATICOS = 2  # BR014: tras 2 visitas fallidas se exige autorización


@dataclass(frozen=True)
class EventoRastreo:
    """Entidad interna del agregado: una línea del historial de rastreo."""

    estado: EstadoEnvio
    descripcion: str
    ocurrido_en: datetime
    instalacion: str = ""
    actor: str = ""


class Paquete:
    def __init__(self, guia: GuiaRastreo, remitente_id: str, destinatario: Contacto,
                 origen: Direccion, destino: Direccion, peso: Peso, dimensiones: Dimensiones,
                 nivel: NivelServicio, tarifa: Tarifa, estado: EstadoEnvio = EstadoEnvio.RECIBIDO,
                 historial: Optional[List[EventoRastreo]] = None,
                 evidencia: Optional[EvidenciaRecepcion] = None, intentos_fallidos: int = 0,
                 autorizacion: Optional[AutorizacionReintento] = None,
                 motivo_rechazo: str = "", contenido: str = "",
                 creado_en: Optional[datetime] = None, actualizado_en: Optional[datetime] = None):
        self.guia = guia
        self.remitente_id = remitente_id
        self.destinatario = destinatario
        self.origen = origen
        self.destino = destino
        self.peso = peso
        self.dimensiones = dimensiones
        self.nivel = nivel
        self.tarifa = tarifa
        self._maquina = MaquinaEstados(estado)
        self.historial: List[EventoRastreo] = list(historial or [])
        self.evidencia = evidencia
        self.intentos_fallidos = intentos_fallidos
        self.autorizacion = autorizacion
        self.motivo_rechazo = motivo_rechazo
        self.contenido = contenido
        self.creado_en = creado_en or ahora()
        self.actualizado_en = actualizado_en or self.creado_en
        self._eventos: list = []

    # ------------------------------------------------------------ consultas
    @property
    def estado(self) -> EstadoEnvio:
        return self._maquina.estado

    @property
    def es_terminal(self) -> bool:
        return self.estado in ESTADOS_TERMINALES

    @property
    def requiere_autorizacion_tercer_intento(self) -> bool:
        return self.intentos_fallidos >= LIMITE_INTENTOS_AUTOMATICOS and self.autorizacion is None

    def horas_sin_actualizacion(self, momento: Optional[datetime] = None) -> float:
        momento = momento or ahora()
        return (momento - self.actualizado_en).total_seconds() / 3600

    def pull_events(self) -> list:
        eventos, self._eventos = self._eventos, []
        return eventos

    # ------------------------------------------------------------ fábrica
    @classmethod
    def recibir(cls, guia: GuiaRastreo, remitente_id: str, destinatario: Contacto,
                origen: Direccion, destino: Direccion, peso: Peso, dimensiones: Dimensiones,
                nivel: NivelServicio, calculadora: CalculadoraTarifa, sucursal: Instalacion,
                empleado: str = "", contenido: str = "",
                momento: Optional[datetime] = None) -> "Paquete":
        """BR005-BR007: tarifa calculada por el sistema, guía única, estado Recibido."""
        momento = momento or ahora()
        if not (remitente_id or "").strip():
            raise ValorInvalidoException("El remitente es obligatorio")
        tarifa = calculadora.calcular(peso, dimensiones, destino.ciudad, nivel)
        paquete = cls(guia, remitente_id, destinatario, origen, destino, peso, dimensiones,
                      NivelServicio.desde(nivel), tarifa, contenido=contenido,
                      creado_en=momento, actualizado_en=momento)
        paquete._registrar(EstadoEnvio.RECIBIDO, "Paquete recibido en sucursal; guía generada",
                           momento, sucursal.nombre, empleado)
        paquete._eventos.append(ev.PaqueteRecibido(str(guia), momento, {"total": str(tarifa.total)}))
        return paquete

    # ------------------------------------------------------------ operación logística
    def clasificar(self, instalacion: Instalacion, operador: str = "", momento=None) -> None:
        self._cambiar(EstadoEnvio.CLASIFICADO, "Clasificado en centro de distribución",
                      momento, instalacion.nombre, operador, ev.PaqueteClasificado)

    def marcar_en_transito(self, manifiesto_id: str = "", operador: str = "", momento=None) -> None:
        texto = f"En tránsito (manifiesto {manifiesto_id})" if manifiesto_id else "En tránsito"
        self._cambiar(EstadoEnvio.EN_TRANSITO, texto, momento, "", operador,
                      ev.PaqueteEnTransito, {"manifiesto": manifiesto_id})

    def marcar_centro_destino(self, instalacion: Instalacion, operador: str = "", momento=None) -> None:
        self._cambiar(EstadoEnvio.CENTRO_DESTINO, "Llegó al centro de distribución destino",
                      momento, instalacion.nombre, operador, ev.PaqueteLlegoACentroDestino)

    def marcar_en_reparto(self, repartidor: str = "", momento=None) -> None:
        self._cambiar(EstadoEnvio.EN_REPARTO, "En reparto: el repartidor lo cargó en su unidad",
                      momento, "", repartidor, ev.PaqueteEnReparto)

    def cancelar(self, motivo: str = "", actor: str = "", momento=None) -> None:
        self._cambiar(EstadoEnvio.CANCELADO, f"Envío cancelado. {motivo}".strip(), momento, "",
                      actor, ev.PaqueteCancelado)

    # ------------------------------------------------------------ entrega (BR012, BR004)
    def finalizar_entrega(self, evidencia: Optional[EvidenciaRecepcion], repartidor: str = "",
                          momento=None) -> None:
        """BR012: sin evidencia no hay estado Entregado."""
        self._maquina.validar(EstadoEnvio.ENTREGADO)
        if evidencia is None or not isinstance(evidencia, EvidenciaRecepcion):
            raise EvidenciaObligatoriaException(
                "La evidencia de recepción (firma o foto) es obligatoria para entregar")
        self.evidencia = evidencia
        self._cambiar(EstadoEnvio.ENTREGADO, f"Entregado a {evidencia.receptor}; evidencia guardada",
                      momento, "", repartidor, ev.PaqueteEntregado, {"receptor": evidencia.receptor})

    # ------------------------------------------------------------ excepciones (BR014, BR013, BR003)
    def registrar_ausencia(self, repartidor: str = "", momento=None) -> None:
        """BR014: 1.ª ausencia → 2.º intento automático; 3.ª requiere autorización."""
        self._maquina.validar(EstadoEnvio.SEGUNDO_INTENTO_PENDIENTE)  # solo desde EN_REPARTO
        momento = momento or ahora()
        if self.intentos_fallidos >= LIMITE_INTENTOS_AUTOMATICOS:
            if self.autorizacion is None:
                raise TercerIntentoNoAutorizadoException(
                    "El tercer intento requiere autorización de un supervisor o Atención al cliente")
            self.intentos_fallidos += 1
            self._cambiar(EstadoEnvio.RETENIDO_EN_SUCURSAL,
                          "Destinatario ausente en 3.ª visita: retenido en sucursal (autorizado)",
                          momento, "", repartidor, ev.PaqueteRetenidoEnSucursal)
            return
        self.intentos_fallidos += 1
        if self.intentos_fallidos == 1:
            reagenda = momento + timedelta(days=1)
            self._cambiar(EstadoEnvio.SEGUNDO_INTENTO_PENDIENTE,
                          "Destinatario ausente: 2.º intento reagendado para la siguiente jornada",
                          momento, "", repartidor, ev.SegundoIntentoProgramado,
                          {"reagendado_para": reagenda.date().isoformat()})
        else:
            self._cambiar(EstadoEnvio.SEGUNDO_INTENTO_PENDIENTE,
                          "Destinatario ausente otra vez: un 3.er intento requiere autorización",
                          momento, "", repartidor, ev.TercerIntentoRequiereAutorizacion)

    def autorizar_tercer_intento(self, autorizacion: AutorizacionReintento, momento=None) -> None:
        if self.intentos_fallidos < LIMITE_INTENTOS_AUTOMATICOS:
            raise ReglaNegocioException("El paquete aún no requiere autorización de tercer intento")
        self.autorizacion = autorizacion
        momento = momento or ahora()
        self._registrar(self.estado, f"Tercer intento autorizado por {autorizacion.autorizador}",
                        momento, "", autorizacion.autorizador)
        self._eventos.append(ev.TercerIntentoAutorizado(str(self.guia), momento,
                                                        {"autorizador": autorizacion.autorizador}))

    def registrar_rechazo(self, motivo: str, repartidor: str = "", momento=None) -> None:
        """Cancela la entrega e inicia la logística inversa hacia la sucursal de origen."""
        self._maquina.validar(EstadoEnvio.RECHAZADO_EN_DEVOLUCION)
        if not (motivo or "").strip():
            raise ValorInvalidoException("El motivo del rechazo es obligatorio")
        self.motivo_rechazo = motivo.strip()
        self._cambiar(EstadoEnvio.RECHAZADO_EN_DEVOLUCION,
                      f"Rechazado por el destinatario ({self.motivo_rechazo}); regresa a {self.origen.ciudad}",
                      momento, "", repartidor, ev.PaqueteRechazado, {"motivo": self.motivo_rechazo})
        self._eventos.append(ev.DevolucionIniciada(str(self.guia), self.actualizado_en,
                                                   {"hacia": str(self.origen)}))

    def completar_devolucion(self, sucursal: Instalacion, empleado: str = "", momento=None) -> None:
        self._cambiar(EstadoEnvio.DEVUELTO_A_ORIGEN, "Devuelto a la sucursal de origen",
                      momento, sucursal.nombre, empleado, ev.DevolucionCompletada)

    def pausar_por_direccion_incorrecta(self, comentario: str = "", repartidor: str = "",
                                        momento=None) -> None:
        self._cambiar(EstadoEnvio.DIRECCION_INCORRECTA,
                      f"Dirección incorrecta: entrega pausada. {comentario}".strip(),
                      momento, "", repartidor, ev.EntregaPausada, {"comentario": comentario})

    def corregir_direccion(self, nueva: Direccion, agente: str = "", momento=None) -> None:
        if self.estado is not EstadoEnvio.DIRECCION_INCORRECTA:
            raise ReglaNegocioException("Solo se corrige la dirección de una entrega pausada")
        self.destino = nueva
        momento = momento or ahora()
        self._registrar(self.estado, f"Dirección corregida: {nueva}", momento, "", agente)
        self._eventos.append(ev.DireccionCorregida(str(self.guia), momento, {"direccion": str(nueva)}))

    def retener_por_incidencia(self, tipo: str, descripcion: str = "", repartidor: str = "",
                               momento=None) -> None:
        self._cambiar(EstadoEnvio.RETENIDO_POR_INCIDENCIA,
                      f"Incidencia mayor ({tipo}): escalada a Atención al cliente",
                      momento, "", repartidor, ev.PaqueteRetenidoPorIncidencia,
                      {"tipo": tipo, "descripcion": descripcion})

    # ------------------------------------------------------------ internos
    def _registrar(self, estado: EstadoEnvio, descripcion: str, momento: datetime,
                   instalacion: str = "", actor: str = "") -> None:
        self.historial.append(EventoRastreo(estado, descripcion, momento, instalacion, actor))
        self.actualizado_en = momento

    def _cambiar(self, destino: EstadoEnvio, descripcion: str, momento, instalacion: str,
                 actor: str, clase_evento, detalle: Optional[dict] = None) -> None:
        self._maquina.validar(destino)
        momento = momento or ahora()
        self._maquina.transicionar(destino)
        self._registrar(destino, descripcion, momento, instalacion, actor)
        self._eventos.append(clase_evento(str(self.guia), momento, detalle or {}))

    def etiqueta_estado(self) -> str:
        return ETIQUETAS[self.estado]
