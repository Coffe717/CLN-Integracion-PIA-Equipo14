"""Traducción agregado <-> diccionario JSON para persistir sin acoplar el dominio."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from src.domain.estado import EstadoEnvio
from src.domain.incidencia import Incidencia
from src.domain.manifiesto import ManifiestoViaje, RutaReparto
from src.domain.paquete import EventoRastreo, Paquete
from src.domain.tabulador import CalculadoraTarifa  # noqa: F401  (documenta la dependencia del dominio)
from src.domain.valores import (
    AutorizacionReintento, Contacto, Dimensiones, Dinero, Direccion, EvidenciaRecepcion,
    GuiaRastreo, Instalacion, NivelServicio, Peso, Tarifa, Zona,
)


def _f(valor):
    return valor.isoformat() if valor else None


def _d(texto):
    return datetime.fromisoformat(texto) if texto else None


def paquete_a_dict(p: Paquete) -> dict:
    return {
        "guia": str(p.guia), "remitente_id": p.remitente_id,
        "destinatario": {"nombre": p.destinatario.nombre, "telefono": p.destinatario.telefono},
        "origen": {"calle": p.origen.calle, "ciudad": p.origen.ciudad},
        "destino": {"calle": p.destino.calle, "ciudad": p.destino.ciudad},
        "peso": str(p.peso.kg),
        "dimensiones": [str(p.dimensiones.largo_cm), str(p.dimensiones.ancho_cm), str(p.dimensiones.alto_cm)],
        "nivel": p.nivel.value,
        "tarifa": {"total": str(p.tarifa.total.monto), "peso_facturable": str(p.tarifa.peso_facturable_kg),
                   "zona": p.tarifa.zona.value, "nivel": p.tarifa.nivel.value,
                   "dias": p.tarifa.dias_entrega, "version": p.tarifa.version_tabulador},
        "estado": p.estado.value,
        "historial": [{"estado": h.estado.value, "descripcion": h.descripcion, "fecha": _f(h.ocurrido_en),
                       "instalacion": h.instalacion, "actor": h.actor} for h in p.historial],
        "evidencia": None if p.evidencia is None else {
            "receptor": p.evidencia.receptor, "firma": p.evidencia.firma, "foto": p.evidencia.foto,
            "capturada_en": _f(p.evidencia.capturada_en)},
        "intentos_fallidos": p.intentos_fallidos,
        "autorizacion": None if p.autorizacion is None else {
            "autorizador": p.autorizacion.autorizador, "rol": p.autorizacion.rol,
            "fecha": _f(p.autorizacion.fecha)},
        "motivo_rechazo": p.motivo_rechazo, "contenido": p.contenido,
        "creado_en": _f(p.creado_en), "actualizado_en": _f(p.actualizado_en),
    }


def paquete_desde_dict(d: dict) -> Paquete:
    t = d["tarifa"]
    tarifa = Tarifa(Dinero(Decimal(t["total"])), Decimal(t["peso_facturable"]), Zona(t["zona"]),
                    NivelServicio(t["nivel"]), t["dias"], t.get("version", "v1"))
    evidencia = None
    if d.get("evidencia"):
        e = d["evidencia"]
        evidencia = EvidenciaRecepcion(e["receptor"], e.get("firma"), e.get("foto"), _d(e["capturada_en"]))
    autorizacion = None
    if d.get("autorizacion"):
        a = d["autorizacion"]
        autorizacion = AutorizacionReintento(a["autorizador"], a["rol"], _d(a["fecha"]))
    historial = [EventoRastreo(EstadoEnvio(h["estado"]), h["descripcion"], _d(h["fecha"]),
                               h.get("instalacion", ""), h.get("actor", "")) for h in d["historial"]]
    return Paquete(
        guia=GuiaRastreo(d["guia"]), remitente_id=d["remitente_id"],
        destinatario=Contacto(d["destinatario"]["nombre"], d["destinatario"].get("telefono", "")),
        origen=Direccion(d["origen"]["calle"], d["origen"]["ciudad"]),
        destino=Direccion(d["destino"]["calle"], d["destino"]["ciudad"]),
        peso=Peso(Decimal(d["peso"])), dimensiones=Dimensiones(*[Decimal(x) for x in d["dimensiones"]]),
        nivel=NivelServicio(d["nivel"]), tarifa=tarifa, estado=EstadoEnvio(d["estado"]),
        historial=historial, evidencia=evidencia, intentos_fallidos=d["intentos_fallidos"],
        autorizacion=autorizacion, motivo_rechazo=d.get("motivo_rechazo", ""),
        contenido=d.get("contenido", ""), creado_en=_d(d["creado_en"]), actualizado_en=_d(d["actualizado_en"]),
    )


def incidencia_a_dict(i: Incidencia) -> dict:
    return {"id": i.id, "guia": i.guia, "tipo": i.tipo.value, "descripcion": i.descripcion,
            "reportada_por": i.reportada_por, "estado": i.estado.value, "creada_en": _f(i.creada_en),
            "resuelta_en": _f(i.resuelta_en), "resolucion": i.resolucion, "resuelta_por": i.resuelta_por}


def incidencia_desde_dict(d: dict) -> Incidencia:
    return Incidencia(d["id"], d["guia"], d["tipo"], d["descripcion"], d["reportada_por"], d["estado"],
                      _d(d["creada_en"]), _d(d.get("resuelta_en")), d.get("resolucion", ""),
                      d.get("resuelta_por", ""))


def manifiesto_a_dict(m: ManifiestoViaje) -> dict:
    return {"id": m.id, "origen": [m.origen.clave, m.origen.nombre], "destino": [m.destino.clave, m.destino.nombre],
            "guias": m.guias, "estado": m.estado.value, "despachado_en": _f(m.despachado_en),
            "arribado_en": _f(m.arribado_en)}


def manifiesto_desde_dict(d: dict) -> ManifiestoViaje:
    return ManifiestoViaje(d["id"], Instalacion(*d["origen"]), Instalacion(*d["destino"]), d["guias"],
                           d["estado"], _d(d["despachado_en"]), _d(d["arribado_en"]))


def ruta_a_dict(r: RutaReparto) -> dict:
    return {"id": r.id, "repartidor": r.repartidor, "guias": r.guias, "estado": r.estado.value,
            "iniciada_en": _f(r.iniciada_en), "cerrada_en": _f(r.cerrada_en)}


def ruta_desde_dict(d: dict) -> RutaReparto:
    return RutaReparto(d["id"], d["repartidor"], d["guias"], d["estado"], _d(d["iniciada_en"]),
                       _d(d["cerrada_en"]))
