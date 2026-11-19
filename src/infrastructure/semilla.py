"""Datos de ejemplo: remitentes desde datos/actores.csv y envíos demo en varios estados."""
from __future__ import annotations

import csv
import os
from typing import List

from src.domain.remitente import Remitente

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV_ACTORES = os.path.join(RAIZ, "datos", "actores.csv")

RESPALDO = [
    ("CAR-C001", "Remitente 01", False, True, "Monterrey"),
    ("CAR-C002", "Remitente 02", False, True, "Apodaca"),
    ("CAR-C003", "Remitente 03", True, True, "Monterrey"),
    ("CAR-C004", "Remitente 04 (inactivo)", False, False, "Guadalupe"),
]


def leer_remitentes_csv(ruta: str = CSV_ACTORES) -> List[Remitente]:
    """Carga actores.csv (UTF-8 con BOM). Si no existe usa un respaldo mínimo."""
    if not os.path.exists(ruta):
        return [Remitente(*fila) for fila in RESPALDO]
    with open(ruta, newline="", encoding="utf-8-sig") as archivo:
        return [Remitente(f["actor_id"], f["nombre"], f["activo"] == "1",
                          f["es_preferente"] == "1", f["ciudad"]) for f in csv.DictReader(archivo)]


def sembrar_remitentes(contenedor, ruta: str = CSV_ACTORES) -> int:
    if contenedor.remitentes.listar():
        return 0
    remitentes = leer_remitentes_csv(ruta)
    for remitente in remitentes:
        contenedor.remitentes.guardar(remitente)
    return len(remitentes)


def sembrar_envios_demo(contenedor) -> list:
    """Crea 4 envíos de ejemplo en distintos estados para que el panel no inicie vacío."""
    if contenedor.consulta.listar_paquetes():
        return []
    activos = [r for r in contenedor.remitentes.listar() if r.activo]
    if not activos:
        return []
    datos = [
        ("Ana López", "Av. Constitución 120", "Saltillo", 2, 25, 20, 15, "ESTANDAR"),
        ("Luis Pérez", "Calle Hidalgo 45", "Monterrey", 5, 30, 30, 30, "ESTANDAR"),
        ("María Ruiz", "Blvd. Díaz Ordaz 900", "Guadalajara", 1, 20, 15, 10, "EXPRES"),
        ("Carlos Soto", "Calle Juárez 77", "Apodaca", 8, 40, 30, 25, "ESTANDAR"),
    ]
    guias = []
    for i, (nombre, calle, ciudad, peso, l, a, h, nivel) in enumerate(datos):
        remitente = activos[i % len(activos)]
        paquete = contenedor.recepcion.registrar_recepcion_paquete(
            remitente.id, nombre, "8112345678", "Av. Juárez 100", "Monterrey", calle, ciudad,
            peso, l, a, h, nivel, "Caja demo", "Empleado demo")
        guias.append(paquete["guia"])
    contenedor.logistica.clasificar_paquete(guias[1], "CD Monterrey", "Operador demo")
    contenedor.logistica.clasificar_paquete(guias[2], "CD Monterrey", "Operador demo")
    contenedor.logistica.despachar_manifiesto_viaje("CD Monterrey", "CD Guadalajara", [guias[2]], "Operador demo")
    return guias
