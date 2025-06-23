from stock_market_simulator.strategies.momentum_breakout_strategy import momentum_breakout_strategy
from stock_market_simulator.simulation.portfolio import Portfolio


def test_buy_order_on_breakout():
    pf = Portfolio(initial_cash=1000)
    # Feed at least 10 days of prices without any breakout
    for i in range(10):
        momentum_breakout_strategy(pf, None, 10 + i, i)

    assert pf.orders == []

    # Current price exceeds recent 10-day high
    momentum_breakout_strategy(pf, None, 25, 10)

    assert len(pf.orders) == 1
    assert pf.orders[0].side == "buy"


def test_sell_order_on_breakdown():
    pf = Portfolio(initial_cash=1000)
    for i in range(10):
        momentum_breakout_strategy(pf, None, 10, i)

    # Breakout to trigger buy
    momentum_breakout_strategy(pf, None, 15, 10)
    pf.orders.clear()
    pf.shares = 1.0
    pf.strategy_state["in_position"] = True

    # Price drops below recent low to trigger sell
    momentum_breakout_strategy(pf, None, 5, 11)

    assert len(pf.orders) == 1
    assert pf.orders[0].side == "sell"
