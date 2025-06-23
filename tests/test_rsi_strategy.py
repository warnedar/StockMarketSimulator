import os
import sys
import types

import pytest

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

# Create a package alias so modules expecting 'stock_market_simulator' can be imported
pkg = types.ModuleType("stock_market_simulator")
pkg.__path__ = [ROOT_DIR]
sys.modules.setdefault("stock_market_simulator", pkg)

from strategies import rsi_strategy
from simulation.portfolio import Portfolio


def test_compute_rsi_manual():
    prices = [1, 2, 1, 2]
    result = rsi_strategy.compute_rsi(prices, period=3)
    expected = 100 - (100 / (1 + (2 / 1)))  # gains 1+1, loss 1 -> rs=2
    assert abs(result - expected) < 1e-6


def test_rsi_strategy_generates_orders():
    portfolio = Portfolio(initial_cash=1000.0)

    prices_down = list(range(30, 15, -1))  # 30..16 decreasing
    prices_up = list(range(16, 31))        # 16..30 increasing
    prices = prices_down + prices_up

    history = []
    buy_day = None
    sell_day = None

    for day, price in enumerate(prices):
        rsi_strategy.rsi_strategy(portfolio, None, price, day)
        history.append(price)

        if len(history) >= 15:
            current_rsi = rsi_strategy.compute_rsi(history, 14)
        else:
            current_rsi = None

        for order in portfolio.orders:
            if order.side == "buy" and buy_day is None:
                buy_day = order.placement_day
                buy_rsi = current_rsi
                portfolio.shares = 10.0  # simulate execution
            if order.side == "sell" and buy_day is not None and sell_day is None:
                sell_day = order.placement_day
                sell_rsi = current_rsi
        if buy_day is not None and sell_day is not None:
            break

    assert buy_day is not None, "No buy order generated"
    assert sell_day is not None, "No sell order generated"
    assert buy_rsi is not None and buy_rsi < 30
    assert sell_rsi is not None and sell_rsi > 70
