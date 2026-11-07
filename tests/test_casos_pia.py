import pytest
from src.domain import Order, CustomerHasDebt

def test_cp01_orden_confirmada_exitosa():
    order = Order(total=100.0, vip=False, status="NEW")
    final_amount = order.confirm(customer_debt=0.0)
    assert order.status == "CONFIRMED"
    assert final_amount == 100.0

def test_cp02_orden_total_cero_lanza_excepcion():
    order = Order(total=0.0, vip=False, status="NEW")
    with pytest.raises(ValueError, match="total must be positive"):
        order.confirm(customer_debt=0.0)

def test_cp03_orden_ya_confirmada_lanza_excepcion():
    order = Order(total=150.0, vip=False, status="CONFIRMED")
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm(customer_debt=0.0)

def test_cp04_cliente_con_deuda_lanza_excepcion():
    order = Order(total=200.0, vip=False, status="NEW")
    with pytest.raises(CustomerHasDebt, match="outstanding debt"):
        order.confirm(customer_debt=50.0)

def test_cp05_tercera_ausencia_o_limite_intentos_simulado():
    order = Order(total=300.0, vip=False, status="NEW")
    order.status = "MAX_ATTEMPTS_REACHED"
    assert order.status == "MAX_ATTEMPTS_REACHED"

def test_cp06_flujo_autorizado_alternativo():
    order = Order(total=400.0, vip=False, status="MAX_ATTEMPTS_REACHED")
    order.status = "NEW"
    final_amount = order.confirm(customer_debt=0.0)
    assert order.status == "CONFIRMED"
    assert final_amount == 400.0

def test_cp07_calculo_tarifa_o_monto_exitoso():
    order = Order(total=1000.0, vip=True, status="NEW")
    final_amount = order.confirm(customer_debt=0.0)
    assert order.discount == 150.0
    assert final_amount == 850.0

def test_cp08_monto_negativo_lanza_excepcion():
    order = Order(total=-100.0, vip=False, status="NEW")
    with pytest.raises(ValueError, match="total must be positive"):
        order.confirm(customer_debt=0.0)

def test_cp09_maquina_estados_transicion_valida():
    order = Order(total=250.0, vip=False, status="NEW")
    assert order.status == "NEW"
    order.confirm()
    assert order.status == "CONFIRMED"