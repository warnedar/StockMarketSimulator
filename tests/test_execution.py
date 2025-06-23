import pytest
from stock_market_simulator.simulation.portfolio import Portfolio, Order
from stock_market_simulator.simulation.execution import execute_orders


def test_execute_orders_market_limit_trailing():
    pf = Portfolio(initial_cash=1000.0)
    # Market buy entire balance at price 10
    pf.orders.append(Order(side="buy", order_type="market"))
    execute_orders(10.0, pf, 0)
    assert pf.shares == pytest.approx(100.0)
    assert pf.cash == pytest.approx(0.0)
    assert pf.orders == []

    # Limit sell - should not trigger at price below limit
    limit = Order(side="sell", order_type="limit", limit_price=15.0)
    pf.orders.append(limit)
    execute_orders(14.0, pf, 1)
    assert pf.shares == pytest.approx(100.0)
    assert pf.cash == pytest.approx(0.0)
    assert limit in pf.orders

    # Price hits limit, sell all shares
    execute_orders(16.0, pf, 2)
    assert pf.shares == pytest.approx(0.0)
    assert pf.cash == pytest.approx(1600.0)
    assert pf.orders == []

    # Buy again with market order at price 16
    pf.orders.append(Order(side="buy", order_type="market"))
    execute_orders(16.0, pf, 3)
    assert pf.shares == pytest.approx(100.0)
    assert pf.cash == pytest.approx(0.0)
    assert pf.orders == []

    # Trailing stop of 10%
    ts_order = Order(side="sell", order_type="trailing_stop", trail_percent=10.0)
    pf.orders.append(ts_order)
    # Initial day sets highest_price
    execute_orders(16.0, pf, 4)
    assert ts_order in pf.orders
    assert pf.shares == pytest.approx(100.0)

    # Price moves up, highest_price increases
    execute_orders(18.0, pf, 5)
    assert ts_order.highest_price == pytest.approx(18.0)
    assert pf.shares == pytest.approx(100.0)

    # Price falls enough to trigger trailing stop
    execute_orders(16.0, pf, 6)
    assert pf.shares == pytest.approx(0.0)
    assert pf.cash == pytest.approx(1600.0)
    assert pf.orders == []

