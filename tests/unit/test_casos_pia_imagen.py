"""Casos de prueba CP-01 a CP-08 tomados de la imagen del PIA.

Trazabilidad: cada clase indica la regla de negocio (BR) y el tipo de prueba
(Éxito / Error / Límite) tal como aparece en la tabla.
"""
from decimal import Decimal

import pytest

from src.domain import eventos as ev
from src.domain.estado import EstadoEnvio
from src.domain.excepciones import (
    EvidenciaObligatoriaException,
    TercerIntentoNoAutorizadoException,
    TransicionEstadoInvalidaException,
    ValorInvalidoException,
)
from src.domain.tabulador import CalculadoraTarifa
from src.domain.valores import Dimensiones, NivelServicio, Peso
from tests.helpers import autorizacion, con_dos_ausencias, evidencia, paquete_en

pytestmark = pytest.mark.cp


class TestBR012EvidenciaObligatoria:
    def test_cp01_exito_repartidor_adjunta_firma_y_foto(self):
        """CP-01 (Éxito): firma y foto → estado Entregado y evidencia guardada."""
        paquete = paquete_en(EstadoEnvio.EN_REPARTO)
        paquete.finalizar_entrega(evidencia(firma="FIRMA-B64", foto="FOTO-B64"), "Juan")

        assert paquete.estado is EstadoEnvio.ENTREGADO
        assert paquete.evidencia is not None
        assert paquete.evidencia.firma == "FIRMA-B64"
        assert paquete.evidencia.foto == "FOTO-B64"
        assert any(isinstance(e, ev.PaqueteEntregado) for e in paquete.pull_events())

    def test_cp02_error_finalizar_sin_evidencia_nula(self):
        """CP-02 (Error): evidencia nula → EvidenciaObligatoriaException; sigue En reparto."""
        paquete = paquete_en(EstadoEnvio.EN_REPARTO)
        with pytest.raises(EvidenciaObligatoriaException):
            paquete.finalizar_entrega(None, "Juan")
        assert paquete.estado is EstadoEnvio.EN_REPARTO
        assert paquete.evidencia is None

    def test_cp03_limite_entregar_paquete_cancelado(self):
        """CP-03 (Límite): entregar un paquete cancelado → transición de estado inválida."""
        paquete = paquete_en(EstadoEnvio.CANCELADO)
        with pytest.raises(TransicionEstadoInvalidaException):
            paquete.finalizar_entrega(evidencia(), "Juan")
        assert paquete.estado is EstadoEnvio.CANCELADO


class TestBR014LimiteIntentos:
    def test_cp04_exito_primera_visita_ausente_reagenda(self):
        """CP-04 (Éxito): 1.ª visita ausente → Segundo intento pendiente (reagendado)."""
        paquete = paquete_en(EstadoEnvio.EN_REPARTO)
        paquete.registrar_ausencia("Juan")

        assert paquete.estado is EstadoEnvio.SEGUNDO_INTENTO_PENDIENTE
        assert paquete.intentos_fallidos == 1
        eventos = paquete.pull_events()
        assert any(isinstance(e, ev.SegundoIntentoProgramado) for e in eventos)

    def test_cp05_error_tercera_visita_sin_autorizacion(self):
        """CP-05 (Error): 3.ª visita ausente sin autorización → TercerIntentoNoAutorizadoException."""
        paquete = con_dos_ausencias(paquete_en(EstadoEnvio.EN_REPARTO))
        assert paquete.requiere_autorizacion_tercer_intento
        with pytest.raises(TercerIntentoNoAutorizadoException):
            paquete.registrar_ausencia("Juan")
        assert paquete.estado is EstadoEnvio.EN_REPARTO
        assert paquete.intentos_fallidos == 2

    @pytest.mark.parametrize("rol", ["SUPERVISOR", "ATENCION_CLIENTE"])
    def test_cp06_limite_tercera_visita_con_autorizacion(self, rol):
        """CP-06 (Límite): 3.ª visita ausente con autorización → Retenido en sucursal."""
        paquete = con_dos_ausencias(paquete_en(EstadoEnvio.EN_REPARTO))
        paquete.autorizar_tercer_intento(autorizacion(rol))
        paquete.registrar_ausencia("Juan")

        assert paquete.estado is EstadoEnvio.RETENIDO_EN_SUCURSAL
        assert paquete.intentos_fallidos == 3
        assert any(isinstance(e, ev.PaqueteRetenidoEnSucursal) for e in paquete.pull_events())


class TestBR005CalculoEstrictoTarifa:
    def test_cp07_exito_5kg_30x30x30_servicio_estandar(self):
        """CP-07 (Éxito): 5 kg, 30x30x30 cm, Servicio Estándar → $150 MXN."""
        tarifa = CalculadoraTarifa().calcular(Peso(5), Dimensiones(30, 30, 30), "Monterrey",
                                              NivelServicio.desde("Servicio Estándar"))
        assert tarifa.total.monto == Decimal("150.00")
        assert tarifa.total.moneda == "MXN"
        assert str(tarifa.total) == "$150.00 MXN"

    @pytest.mark.parametrize("peso", [-5, 0])
    def test_cp08_error_peso_negativo_o_cero(self, peso):
        """CP-08 (Error): peso negativo (-5 kg) → excepción de validación del Value Object."""
        with pytest.raises(ValorInvalidoException):
            Peso(peso)

    @pytest.mark.parametrize("medidas", [(0, 30, 30), (30, 0, 30), (30, 30, 0), (0, 0, 0), (-1, 30, 30)])
    def test_cp08_error_dimensiones_en_cero(self, medidas):
        """CP-08 (Error): dimensiones en cero → excepción de validación del Value Object."""
        with pytest.raises(ValorInvalidoException):
            Dimensiones(*medidas)
