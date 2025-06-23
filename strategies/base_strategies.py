# stock_market_simulator/strategies/base_strategies.py

"""
Base Strategies for the Stock Market Simulator.

This file defines core trading strategies and maintains a mapping (STRATEGY_MAP)
to be used by the simulation engine. The strategies included are:

  - buy_hold: A simple buy‐and‐hold strategy.
  - advanced_daytrading: A dynamic strategy using trailing stops and limit orders.
  - sma_trading: A strategy based on Simple Moving Averages.
  - momentum_breakout: A short‐term momentum breakout strategy.
  - rsi: A strategy based on the Relative Strength Index (RSI).

Obsolete strategies (advanced_daytrading10 and advanced_daytrading20) have been removed.
"""

from stock_market_simulator.simulation.portfolio import Order, Portfolio
from stock_market_simulator.strategies.sma_trading_strategy import sma_trading_strategy as imported_sma_trading_strategy
from stock_market_simulator.strategies.momentum_breakout_strategy import momentum_breakout_strategy
from stock_market_simulator.strategies.rsi_strategy import rsi_strategy


def buy_hold_strategy(portfolio: Portfolio, date, price: float, day_index: int) -> None:
    """
    Buy-and-hold strategy: Buy everything on the first day and then hold.
    """
    if day_index == 0 and 'initialized' not in portfolio.strategy_state:
        portfolio.strategy_state['initialized'] = True
        order = Order(side='buy', order_type='market', quantity=None)
        order.placement_day = day_index
        portfolio.orders.append(order)


def advanced_daytrading(portfolio: Portfolio, date, price: float, day_index: int) -> None:
    """
    Advanced Day Trading Strategy.

    This strategy uses a trailing stop to protect profits and a limit order
    to re-enter at a discount when a position is lost. It uses three configurable parameters:
      - trailing_stop_pct (default 10.0): The percentage for the trailing stop.
      - limit_buy_discount_pct (default 5.0): The discount for the limit order buy.
      - pending_limit_days (default 30): Days to wait before converting an unfilled limit order into a market order.

    On day 0, the strategy initializes its state and pulls these parameters from
    portfolio.advanced_params (if provided) or uses defaults.
    """
    st = portfolio.strategy_state
    if day_index == 0 and "initialized" not in st:
        st["initialized"] = True
        st["position"] = "none"
        st["pending_limit"] = False
        st["limit_buy_day"] = None
        st["limit_buy_price"] = None
        st["last_sell_price"] = None
        # Initialize advanced parameters from portfolio.advanced_params if available, else use defaults.
        advanced_params = getattr(portfolio, "advanced_params", {})
        st["advanced_params"] = {
            "trailing_stop_pct": advanced_params.get("trailing_stop_pct", 11.0),
            "limit_buy_discount_pct": advanced_params.get("limit_buy_discount_pct", 4.0),
            "pending_limit_days": advanced_params.get("pending_limit_days", 37)
        }
        # Place initial market order to buy.
        o = Order(side='buy', order_type='market', quantity=None)
        o.placement_day = day_index
        portfolio.orders.append(o)
        st["position"] = "waiting_buy"
        return

    have_shares = (portfolio.shares > 0.00001)

    if st.get("position") != "long" and have_shares:
        st["position"] = "long"
        trailing_stop_pct = st["advanced_params"]["trailing_stop_pct"]
        ts = Order(side='sell', order_type='trailing_stop',
                   trail_percent=trailing_stop_pct, quantity=None)
        ts.placement_day = day_index
        portfolio.orders.append(ts)

    if st.get("position") == "long" and not have_shares:
        st["position"] = "none"
        st["last_sell_price"] = price
        limit_buy_discount_pct = st["advanced_params"]["limit_buy_discount_pct"]
        limit_price = price * (1 - limit_buy_discount_pct / 100.0)
        lb = Order(side='buy', order_type='limit', limit_price=limit_price)
        lb.placement_day = day_index
        portfolio.orders.append(lb)
        st["pending_limit"] = True
        st["limit_buy_day"] = day_index
        st["limit_buy_price"] = limit_price

    if st.get("pending_limit"):
        limit_day = st["limit_buy_day"]
        pending_limit_days = st["advanced_params"]["pending_limit_days"]
        if limit_day is not None and (day_index - limit_day) >= pending_limit_days:
            to_cancel = []
            for od in portfolio.orders:
                if od.order_type == 'limit' and od.side == 'buy' and od.placement_day == limit_day:
                    to_cancel.append(od)
            for c in to_cancel:
                portfolio.orders.remove(c)
            mk = Order(side='buy', order_type='market')
            mk.placement_day = day_index
            portfolio.orders.append(mk)
            st["pending_limit"] = False
            st["limit_buy_day"] = None
            st["limit_buy_price"] = None


def sma_trading_strategy(portfolio: Portfolio, date, price: float, day_index: int) -> None:
    """
    Delegates to the imported SMA Trading Strategy.
    """
    imported_sma_trading_strategy(portfolio, date, price, day_index)


def momentum_breakout_strategy_wrapper(portfolio: Portfolio, date, price: float, day_index: int) -> None:
    """
    Delegates to the imported Momentum Breakout Strategy.
    """
    momentum_breakout_strategy(portfolio, date, price, day_index)


def rsi_strategy_wrapper(portfolio: Portfolio, date, price: float, day_index: int) -> None:
    """
    Delegates to the imported RSI Strategy.
    """
    rsi_strategy(portfolio, date, price, day_index)


# Central strategy mapping.
STRATEGY_MAP = {
    "buy_hold": buy_hold_strategy,
    "advanced_daytrading": advanced_daytrading,
    "sma_trading": sma_trading_strategy,
    "momentum_breakout": momentum_breakout_strategy_wrapper,
    "rsi": rsi_strategy_wrapper
}
