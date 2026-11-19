"""Excepciones de la capa de aplicación (no son reglas de negocio)."""


class AplicacionException(Exception):
    codigo = "APLICACION"

    def __init__(self, mensaje: str = ""):
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontradoException(AplicacionException):
    codigo = "NO_ENCONTRADO"


class SolicitudInvalidaException(AplicacionException):
    codigo = "SOLICITUD_INVALIDA"
