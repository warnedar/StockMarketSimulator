# stock_market_simulator/strategies/momentum_breakout_strategy.py

"""
Momentum Breakout Strategy

This strategy monitors the most recent 10-day price window to detect breakout events.
- BUY Condition: If the current price exceeds the highest price of the last 10 days,
  and at least 1 day has passed since the last buy, and no position is currently held,
  then buy using 30% of available cash.
- SELL Condition: If the current price falls below the lowest price of the last 10 days,
  and at least 1 day has passed since the last sell, and a position is held,
  then sell 50% of current holdings.

The strategy maintains its state (price history, last order days, and in_position flag) in portfolio.strategy_state.
"""

from stock_market_simulator.simulation.portfolio import Order, Portfolio

def momentum_breakout_strategy(portfolio: Portfolio, date, price, day_index):
    state = portfolio.strategy_state
    if "price_history" not in state:
        state["price_history"] = []
        state["last_buy_day"] = -100
        state["last_sell_day"] = -100
        state["in_position"] = False

    history = state["price_history"]

    window = 10
    # Use the previous ``window`` days to determine breakout/breakdown levels.
    # We only append the current price after evaluating the conditions so that
    # today's price does not influence the threshold calculations.  This mirrors
    # how many technical traders would operate using yesterday's closing data.
    if len(history) < window:
        history.append(price)
        return

    recent_window = history[-window:]
    highest_recent = max(recent_window)
    lowest_recent = min(recent_window)

    days_since_buy = day_index - state.get("last_buy_day", -100)
    days_since_sell = day_index - state.get("last_sell_day", -100)

    # BUY Condition: Price breaks above recent high, no position, and at least 1 day since last buy.
    if price > highest_recent and not state["in_position"] and days_since_buy >= 1:
        qty = (portfolio.cash * 0.30) / price
        if qty > 0:
            order = Order(side="buy", order_type="market", quantity=qty)
            order.placement_day = day_index
            portfolio.orders.append(order)
            state["last_buy_day"] = day_index
            state["in_position"] = True

    # SELL Condition: Price falls below recent low, in position, and at least 1 day since last sell.
    if price < lowest_recent and state["in_position"] and days_since_sell >= 1:
        qty = portfolio.shares * 0.50
        if qty > 0:
            order = Order(side="sell", order_type="market", quantity=qty)
            order.placement_day = day_index
            portfolio.orders.append(order)
            state["last_sell_day"] = day_index
            if portfolio.shares - qty < 1e-6:
                state["in_position"] = False

    # Append the current price after evaluation so future windows include it
    history.append(price)
