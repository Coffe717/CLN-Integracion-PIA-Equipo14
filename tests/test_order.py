import pytest
from src.domain import Order, CustomerHasDebt

def test_vip_discount():
    o = Order(100, vip=True)
    assert o.confirm() == 85
    assert o.status == "CONFIRMED"

def test_regular_no_discount():
    assert Order(100).confirm() == 100

def test_customer_debt():
    with pytest.raises(CustomerHasDebt):
        Order(100).confirm(customer_debt=50)

@pytest.mark.parametrize("total", [0, -1])
def test_invalid_total(total):
    with pytest.raises(ValueError):
        Order(total).confirm()

def test_vip_discount_200():
    # Arrange: preparar un pedido de 200 con cliente VIP
    o = Order(200, vip=True)
    # Act + Assert: debe aplicar 15% (descuenta 30) y retornar 170
    assert o.confirm() == 170
    assert o.status == "CONFIRMED"

def test_regular_no_discount():
    # Arrange: preparar un pedido de 200 con cliente regular
    o = Order(200, vip=False)
    # Act + Assert: no hay descuento, retorna los mismos 200
    assert o.confirm() == 200
    assert o.status == "CONFIRMED"

def test_cannot_confirm_twice():
    order = Order(100)
    order.confirm()
    with pytest.raises(ValueError, match="already confirmed"):
        order.confirm()