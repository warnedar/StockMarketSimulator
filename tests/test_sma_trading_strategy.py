import os
import sys
import types

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

# Alias package name used inside the strategy files
pkg = types.ModuleType("stock_market_simulator")
pkg.__path__ = [project_root]
sys.modules.setdefault("stock_market_simulator", pkg)

from simulation.portfolio import Portfolio
from strategies.sma_trading_strategy import sma_trading_strategy


def _feed_prices(prices, portfolio):
    for day_index, price in enumerate(prices):
        sma_trading_strategy(portfolio, None, price, day_index)


def test_buy_order_added_when_sma20_exceeds_sma50():
    pf = Portfolio(initial_cash=1000.0)
    prices = [1.0] * 50
    _feed_prices(prices, pf)

    assert pf.orders == []

    sma_trading_strategy(pf, None, 2.0, 50)
    assert len(pf.orders) == 1
    order = pf.orders[0]
    assert order.side == "buy"
    assert order.order_type == "market"
    expected_qty = (pf.cash * 0.20) / 2.0
    assert order.quantity == expected_qty


def test_sell_condition_when_price_above_1_1_times_sma20():
    pf = Portfolio(initial_cash=1000.0)
    prices = [1.0] * 50
    _feed_prices(prices, pf)
    pf.cash = 0.0
    pf.shares = 10.0

    sma_trading_strategy(pf, None, 2.0, 50)
    assert len(pf.orders) == 1
    order = pf.orders[0]
    assert order.side == "sell"
    assert order.order_type == "market"
    expected_qty = pf.shares * 0.50
    # quantity is computed before the order is appended, using current shares
    assert order.quantity == expected_qty
