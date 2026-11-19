"""Fábricas de apoyo para las pruebas: llevan un Paquete hasta el estado deseado."""
from src.domain.estado import EstadoEnvio
from src.domain.paquete import Paquete
from src.domain.tabulador import CalculadoraTarifa
from src.domain.valores import (
    AutorizacionReintento, Contacto, Dimensiones, Direccion, EvidenciaRecepcion,
    GuiaRastreo, Instalacion, NivelServicio, Peso,
)

CD = Instalacion("CD Monterrey")


def evidencia(receptor="Ana López", firma="data:image/png;base64,FIRMA", foto="data:image/jpeg;base64,FOTO"):
    return EvidenciaRecepcion(receptor, firma, foto)


def autorizacion(rol="SUPERVISOR"):
    return AutorizacionReintento("Sup. Rosa", rol)


def nuevo_paquete(numero=1, ciudad="Monterrey", nivel=NivelServicio.ESTANDAR) -> Paquete:
    return Paquete.recibir(
        guia=GuiaRastreo(f"CB-{numero:010d}"), remitente_id="CAR-C001",
        destinatario=Contacto("Ana López", "8112345678"),
        origen=Direccion("Av. Juárez 100", "Monterrey"), destino=Direccion("Calle Hidalgo 45", ciudad),
        peso=Peso(5), dimensiones=Dimensiones(30, 30, 30), nivel=nivel,
        calculadora=CalculadoraTarifa(), sucursal=Instalacion("Sucursal Centro"), empleado="Emp 1")


def paquete_en(estado: EstadoEnvio, numero=1) -> Paquete:
    """Devuelve un paquete ya llevado a `estado` usando solo métodos del dominio."""
    p = nuevo_paquete(numero)
    if estado is EstadoEnvio.RECIBIDO:
        return p
    if estado is EstadoEnvio.CANCELADO:
        p.cancelar("prueba")
        return p
    p.clasificar(CD)
    if estado is EstadoEnvio.CLASIFICADO:
        return p
    p.marcar_en_transito("MAN-1")
    if estado is EstadoEnvio.EN_TRANSITO:
        return p
    p.marcar_centro_destino(Instalacion("CD Saltillo"))
    if estado is EstadoEnvio.CENTRO_DESTINO:
        return p
    p.marcar_en_reparto("Juan")
    if estado is EstadoEnvio.EN_REPARTO:
        return p
    if estado is EstadoEnvio.ENTREGADO:
        p.finalizar_entrega(evidencia(), "Juan")
    elif estado is EstadoEnvio.SEGUNDO_INTENTO_PENDIENTE:
        p.registrar_ausencia("Juan")
    elif estado is EstadoEnvio.DIRECCION_INCORRECTA:
        p.pausar_por_direccion_incorrecta("no existe la calle", "Juan")
    elif estado is EstadoEnvio.RETENIDO_POR_INCIDENCIA:
        p.retener_por_incidencia("DANO", "caja rota", "Juan")
    elif estado is EstadoEnvio.RECHAZADO_EN_DEVOLUCION:
        p.registrar_rechazo("no lo pidió", "Juan")
    elif estado is EstadoEnvio.DEVUELTO_A_ORIGEN:
        p.registrar_rechazo("no lo pidió", "Juan")
        p.completar_devolucion(Instalacion("Sucursal Centro"))
    elif estado is EstadoEnvio.RETENIDO_EN_SUCURSAL:
        con_dos_ausencias(p)
        p.autorizar_tercer_intento(autorizacion())
        p.registrar_ausencia("Juan")
    return p


def con_dos_ausencias(p: Paquete) -> Paquete:
    """Deja el paquete EN_REPARTO con 2 intentos fallidos (listo para la 3.ª visita)."""
    p.registrar_ausencia("Juan")
    p.marcar_en_reparto("Juan")
    p.registrar_ausencia("Juan")
    p.marcar_en_reparto("Juan")
    return p
