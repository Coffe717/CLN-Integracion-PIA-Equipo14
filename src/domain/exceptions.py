class DomainException(Exception):
    """Excepción base para reglas de negocio de CargoBox"""
    pass

class EvidenciaObligatoriaException(DomainException):
    """Se dispara cuando se intenta entregar un paquete sin evidencia digital (BR012)"""
    pass

class TransicionEstadoInvalidaException(DomainException):
    """Se dispara al intentar cambiar a un estado no permitido por la máquina de estados"""
    pass

class TercerIntentoNoAutorizadoException(DomainException):
    """Se dispara en la 3ra ausencia si no cuenta con autorización explícita (BR014)"""
    pass

class ValorInvalidoException(DomainException):
    """Se dispara cuando dimensiones o peso rompen las invariantes del Value Object"""
    pass