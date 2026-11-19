"""Excepciones de dominio (lenguaje ubicuo de CargoBox).

Cada excepción nombra una regla de negocio violada y lleva un `codigo`
estable que la capa API traduce a una respuesta HTTP.
"""


class DominioException(Exception):
    """Base de todas las violaciones de reglas de negocio."""

    codigo = "DOMINIO"

    def __init__(self, mensaje: str = ""):
        super().__init__(mensaje or self.__class__.__name__)
        self.mensaje = mensaje or self.__class__.__name__


class ValorInvalidoException(DominioException):
    """Un Value Object recibió datos inválidos (peso negativo, medidas en cero...)."""

    codigo = "VALOR_INVALIDO"


class EvidenciaObligatoriaException(DominioException):
    """BR012: no se puede entregar sin evidencia de recepción (firma/foto)."""

    codigo = "EVIDENCIA_OBLIGATORIA"


class TransicionEstadoInvalidaException(DominioException):
    """La máquina de estados no permite pasar del estado actual al solicitado."""

    codigo = "TRANSICION_INVALIDA"


class TercerIntentoNoAutorizadoException(DominioException):
    """BR014: el tercer intento de entrega requiere autorización explícita."""

    codigo = "TERCER_INTENTO_NO_AUTORIZADO"


class AutorizacionInvalidaException(DominioException):
    """Quien autoriza no tiene un rol permitido (supervisor / atención al cliente)."""

    codigo = "AUTORIZACION_INVALIDA"


class ResolucionNoPermitidaException(DominioException):
    """BR003: el repartidor no puede resolver incidencias mayores."""

    codigo = "RESOLUCION_NO_PERMITIDA"


class ReglaNegocioException(DominioException):
    """Otra regla de negocio violada (p. ej. incidencia ya resuelta)."""

    codigo = "REGLA_NEGOCIO"
