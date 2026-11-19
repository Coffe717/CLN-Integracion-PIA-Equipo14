"""Fábrica de la aplicación Flask: API REST + interfaz web + Swagger UI."""
from __future__ import annotations

import logging
import os
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

from src.api.config import Config
from src.api.openapi import construir_openapi
from src.api.rutas import api
from src.application.excepciones import AplicacionException, NoEncontradoException, SolicitudInvalidaException
from src.domain import excepciones as exc
from src.infrastructure.composicion import construir_sql
from src.infrastructure.semilla import sembrar_envios_demo, sembrar_remitentes

CARPETA_ESTATICA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Contrato HTTP: 200/201 éxito · 400 solicitud mal formada · 403 rol no permitido
# 404 no existe · 409 conflicto de estado/regla · 422 dato o regla de validación
HTTP_POR_EXCEPCION = [
    (SolicitudInvalidaException, 400),
    (NoEncontradoException, 404),
    (exc.AutorizacionInvalidaException, 403),
    (exc.ResolucionNoPermitidaException, 403),
    (exc.TransicionEstadoInvalidaException, 409),
    (exc.TercerIntentoNoAutorizadoException, 409),
    (exc.ReglaNegocioException, 409),
    (exc.EvidenciaObligatoriaException, 422),
    (exc.ValorInvalidoException, 422),
    (exc.DominioException, 422),
]

PAGINA_DOCS = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>CargoBox API - Swagger UI</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui.min.css">
</head><body><div id="swagger-ui"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.min.js"></script>
<script>window.ui = SwaggerUIBundle({url: "/openapi.json", dom_id: "#swagger-ui"});</script>
</body></html>"""


def _estado_http(error: Exception) -> int:
    for clase, codigo in HTTP_POR_EXCEPCION:
        if isinstance(error, clase):
            return codigo
    return 500


def create_app(config: Optional[Config] = None, contenedor=None) -> Flask:
    config = config or Config.desde_entorno()
    app = Flask(__name__, static_folder=CARPETA_ESTATICA, static_url_path="/static")
    app.json.ensure_ascii = False
    app.config["UMBRAL_HORAS"] = config.umbral_horas

    if contenedor is None:
        contenedor = construir_sql(config.database_url)
        sembrar_remitentes(contenedor)
        if config.seed_demo:
            sembrar_envios_demo(contenedor)
    app.config["CONTENEDOR"] = contenedor
    app.register_blueprint(api)

    @app.errorhandler(exc.DominioException)
    @app.errorhandler(AplicacionException)
    def _error_negocio(error):
        return jsonify({"error": {"codigo": error.codigo, "mensaje": error.mensaje}}), _estado_http(error)

    @app.errorhandler(404)
    def _no_encontrada(_):
        if request.path.startswith("/api"):
            return jsonify({"error": {"codigo": "RUTA_NO_ENCONTRADA", "mensaje": "El recurso no existe"}}), 404
        return send_from_directory(CARPETA_ESTATICA, "index.html")

    @app.errorhandler(405)
    def _metodo(_):
        return jsonify({"error": {"codigo": "METODO_NO_PERMITIDO", "mensaje": "Método no permitido"}}), 405

    @app.errorhandler(Exception)
    def _inesperado(error):  # pragma: no cover - red de seguridad
        logging.getLogger("cargobox").exception("Error inesperado")
        return jsonify({"error": {"codigo": "ERROR_INTERNO", "mensaje": "Ocurrió un error inesperado"}}), 500

    @app.get("/")
    def inicio():
        return send_from_directory(CARPETA_ESTATICA, "index.html")

    @app.get("/openapi.json")
    def openapi():
        return jsonify(construir_openapi())

    @app.get("/docs")
    def docs():
        return PAGINA_DOCS

    return app
