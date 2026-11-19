from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.domain.excepciones import AutorizacionInvalidaException, ValorInvalidoException
from src.domain.tabulador import CalculadoraTarifa, TabuladorTarifas
from src.domain.valores import (
    AutorizacionReintento, Contacto, Dimensiones, Dinero, Direccion, EvidenciaRecepcion,
    GuiaRastreo, Instalacion, NivelServicio, Peso, Zona, a_decimal,
)


class TestValueObjects:
    @pytest.mark.parametrize("valor", [None, True, "abc", float("nan")])
    def test_a_decimal_rechaza_no_numericos(self, valor):
        with pytest.raises(ValorInvalidoException):
            a_decimal(valor, "x")

    def test_peso_maximo(self):
        with pytest.raises(ValorInvalidoException):
            Peso(71)
        assert Peso("2.5").kg == Decimal("2.5")

    def test_dimension_excede_maximo(self):
        with pytest.raises(ValorInvalidoException):
            Dimensiones(201, 10, 10)

    def test_volumen_y_peso_volumetrico(self):
        d = Dimensiones(50, 40, 25)
        assert d.volumen_cm3 == Decimal(50000)
        assert d.peso_volumetrico_kg == Decimal(10)

    def test_dinero_redondea_y_rechaza_negativos(self):
        assert Dinero("10.005").monto == Decimal("10.01")
        assert str(Dinero(1234.5)) == "$1,234.50 MXN"
        with pytest.raises(ValorInvalidoException):
            Dinero(-1)

    @pytest.mark.parametrize("calle,ciudad", [("", "MTY"), ("Calle 1", ""), (None, "MTY")])
    def test_direccion_obligatoria(self, calle, ciudad):
        with pytest.raises(ValorInvalidoException):
            Direccion(calle, ciudad)

    def test_direccion_str(self):
        assert str(Direccion(" Calle 1 ", " Monterrey ")) == "Calle 1, Monterrey"

    def test_contacto(self):
        assert Contacto("Ana", " 81 1234 5678 ").telefono == "81 1234 5678"
        with pytest.raises(ValorInvalidoException):
            Contacto("")
        with pytest.raises(ValorInvalidoException):
            Contacto("Ana", "abc")

    def test_guia_formato(self):
        assert str(GuiaRastreo(" cb-abcdef1234 ")) == "CB-ABCDEF1234"
        for malo in ["", "XX-123", "CB-123", None]:
            with pytest.raises(ValorInvalidoException):
                GuiaRastreo(malo)

    def test_instalacion(self):
        assert Instalacion("CD MTY").nombre == "CD MTY"
        with pytest.raises(ValorInvalidoException):
            Instalacion("")

    def test_evidencia_requiere_receptor_y_firma_o_foto(self):
        assert EvidenciaRecepcion("Ana", firma="F").foto is None
        assert EvidenciaRecepcion("Ana", foto="P").firma is None
        assert EvidenciaRecepcion("Ana", "F", "P", datetime(2026, 1, 1, tzinfo=timezone.utc)).capturada_en.year == 2026
        with pytest.raises(ValorInvalidoException):
            EvidenciaRecepcion("Ana")
        with pytest.raises(ValorInvalidoException):
            EvidenciaRecepcion("", firma="F")

    def test_autorizacion_solo_roles_permitidos(self):
        assert AutorizacionReintento("Rosa", "supervisor").rol == "SUPERVISOR"
        with pytest.raises(AutorizacionInvalidaException):
            AutorizacionReintento("Pedro", "REPARTIDOR")
        with pytest.raises(AutorizacionInvalidaException):
            AutorizacionReintento("Pedro", None)

    @pytest.mark.parametrize("texto,esperado", [
        ("Servicio Estándar", NivelServicio.ESTANDAR), ("estandar", NivelServicio.ESTANDAR),
        ("Exprés", NivelServicio.EXPRES), ("EXPRESS", NivelServicio.EXPRES),
        (NivelServicio.EXPRES, NivelServicio.EXPRES)])
    def test_nivel_servicio_desde(self, texto, esperado):
        assert NivelServicio.desde(texto) is esperado

    @pytest.mark.parametrize("malo", ["premium", None, 3])
    def test_nivel_servicio_invalido(self, malo):
        with pytest.raises(ValorInvalidoException):
            NivelServicio.desde(malo)


class TestCalculadoraTarifa:
    def test_peso_volumetrico_manda_si_es_mayor(self):
        t = CalculadoraTarifa().calcular(Peso(1), Dimensiones(50, 40, 25), "Monterrey", NivelServicio.ESTANDAR)
        assert t.peso_facturable_kg == Decimal("10.00")
        assert t.total.monto == Decimal("150.00")

    @pytest.mark.parametrize("ciudad,zona,total", [
        ("Monterrey", Zona.LOCAL, "150.00"), ("Saltillo", Zona.REGIONAL, "187.50"),
        ("Guadalajara", Zona.NACIONAL, "240.00"), ("  san nicolás  ", Zona.LOCAL, "150.00")])
    def test_zonas(self, ciudad, zona, total):
        t = CalculadoraTarifa().calcular(Peso(8), Dimensiones(10, 10, 10), ciudad, NivelServicio.ESTANDAR)
        assert (t.zona, str(t.total.monto)) == (zona, total)

    def test_expres_cuesta_mas_y_llega_antes(self):
        calc = CalculadoraTarifa()
        est = calc.calcular(Peso(2), Dimensiones(10, 10, 10), "Monterrey", NivelServicio.ESTANDAR)
        exp = calc.calcular(Peso(2), Dimensiones(10, 10, 10), "Monterrey", NivelServicio.EXPRES)
        assert exp.total.monto > est.total.monto and exp.dias_entrega < est.dias_entrega
        assert est.version_tabulador == "v1"

    def test_tarifa_es_inmutable(self):
        t = CalculadoraTarifa().calcular(Peso(2), Dimensiones(10, 10, 10), "Monterrey", NivelServicio.ESTANDAR)
        with pytest.raises(Exception):
            t.total = Dinero(1)

    def test_rechaza_argumentos_que_no_son_value_objects(self):
        with pytest.raises(ValorInvalidoException):
            CalculadoraTarifa().calcular(5, Dimensiones(1, 1, 1), "Monterrey", NivelServicio.ESTANDAR)

    def test_peso_facturable_fuera_del_tabulador(self):
        with pytest.raises(ValorInvalidoException):
            TabuladorTarifas().precio_base(Decimal("71"))
