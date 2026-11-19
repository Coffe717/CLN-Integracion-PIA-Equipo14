"""Conversión de agregados a diccionarios serializables (DTOs de salida)."""
from __future__ import annotations

from typing import Optional

from src.domain.estado import ETIQUETAS
from src.domain.incidencia import Incidencia
from src.domain.paquete import Paquete
from src.domain.valores import EvidenciaRecepcion, Tarifa


def _fecha(valor) -> Optional[str]:
    return valor.isoformat() if valor else None


def tarifa_a_dto(t: Tarifa) -> dict:
    return {
        "total": str(t.total.monto),
        "moneda": t.total.moneda,
        "texto": str(t.total),
        "peso_facturable_kg": str(t.peso_facturable_kg),
        "zona": t.zona.value,
        "nivel_servicio": t.nivel.value,
        "dias_entrega": t.dias_entrega,
        "version_tabulador": t.version_tabulador,
    }


def evidencia_a_dto(e: Optional[EvidenciaRecepcion], con_imagenes: bool = False) -> Optional[dict]:
    if e is None:
        return None
    dto = {"receptor": e.receptor, "tiene_firma": bool(e.firma), "tiene_foto": bool(e.foto),
           "capturada_en": _fecha(e.capturada_en)}
    if con_imagenes:
        dto.update({"firma": e.firma, "foto": e.foto})
    return dto


def paquete_a_dto(p: Paquete) -> dict:
    return {
        "guia": str(p.guia),
        "estado": p.estado.value,
        "estado_etiqueta": ETIQUETAS[p.estado],
        "remitente_id": p.remitente_id,
        "destinatario": {"nombre": p.destinatario.nombre, "telefono": p.destinatario.telefono},
        "origen": {"calle": p.origen.calle, "ciudad": p.origen.ciudad},
        "destino": {"calle": p.destino.calle, "ciudad": p.destino.ciudad},
        "peso_kg": str(p.peso.kg),
        "dimensiones": {"largo_cm": str(p.dimensiones.largo_cm), "ancho_cm": str(p.dimensiones.ancho_cm),
                        "alto_cm": str(p.dimensiones.alto_cm)},
        "nivel_servicio": p.nivel.value,
        "contenido": p.contenido,
        "tarifa": tarifa_a_dto(p.tarifa),
        "intentos_fallidos": p.intentos_fallidos,
        "requiere_autorizacion_tercer_intento": p.requiere_autorizacion_tercer_intento,
        "tercer_intento_autorizado": p.autorizacion is not None,
        "tiene_evidencia": p.evidencia is not None,
        "motivo_rechazo": p.motivo_rechazo,
        "creado_en": _fecha(p.creado_en),
        "actualizado_en": _fecha(p.actualizado_en),
    }


def incidencia_a_dto(i: Incidencia) -> dict:
    return {
        "id": i.id, "guia": i.guia, "tipo": i.tipo.value, "estado": i.estado.value,
        "descripcion": i.descripcion, "reportada_por": i.reportada_por, "asignada_a": i.asignada_a,
        "creada_en": _fecha(i.creada_en), "resuelta_en": _fecha(i.resuelta_en),
        "resolucion": i.resolucion, "resuelta_por": i.resuelta_por,
    }


def linea_de_tiempo(p: Paquete) -> list:
    return [
        {"estado": h.estado.value, "etiqueta": ETIQUETAS[h.estado], "descripcion": h.descripcion,
         "instalacion": h.instalacion, "actor": h.actor, "fecha": _fecha(h.ocurrido_en)}
        for h in p.historial
    ]
