# stock_market_simulator/strategies/rsi_strategy.py

"""
RSI Strategy

This strategy uses the 14-day Relative Strength Index (RSI) to generate trading signals.
- BUY Condition: If RSI falls below 30 (oversold), and at least 1 day has passed since the last buy, and no position is held,
  then buy using 25% of available cash.
- SELL Condition: If RSI rises above 70 (overbought), and at least 1 day has passed since the last sell, and a position is held,
  then sell 50% of current holdings.

The strategy maintains its own price history and order timing in portfolio.strategy_state.
"""

from stock_market_simulator.simulation.portfolio import Order, Portfolio

def compute_rsi(prices, period=14):
    """
    Compute the Relative Strength Index (RSI) for a list of prices.

    Requires at least period+1 data points.
    Returns the RSI value (0-100) or None if insufficient data.
    """
    if len(prices) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, period + 1):
        change = prices[-i] - prices[-i-1]
        # Separate positive and negative moves.  This explicit loop avoids
        # dependencies on pandas for clarity and keeps the function fast for the
        # small window sizes typically used with RSI.
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def rsi_strategy(portfolio: Portfolio, date, price, day_index):
    state = portfolio.strategy_state
    if "price_history" not in state:
        state["price_history"] = []
        state["last_buy_day"] = -100
        state["last_sell_day"] = -100
        state["in_position"] = False

    history = state["price_history"]
    history.append(price)

    period = 14
    if len(history) < period + 1:
        return

    rsi = compute_rsi(history, period)
    if rsi is None:
        return

    days_since_buy = day_index - state.get("last_buy_day", -100)
    days_since_sell = day_index - state.get("last_sell_day", -100)

    # BUY Condition: RSI below 30, no current position, and at least 1 day since last buy.
    if rsi < 30 and not state["in_position"] and days_since_buy >= 1:
        qty = (portfolio.cash * 0.25) / price
        if qty > 0:
            order = Order(side="buy", order_type="market", quantity=qty)
            order.placement_day = day_index
            portfolio.orders.append(order)
            state["last_buy_day"] = day_index
            state["in_position"] = True

    # SELL Condition: RSI above 70, in position, and at least 1 day since last sell.
    if rsi > 70 and state["in_position"] and days_since_sell >= 1:
        qty = portfolio.shares * 0.50
        if qty > 0:
            order = Order(side="sell", order_type="market", quantity=qty)
            order.placement_day = day_index
            portfolio.orders.append(order)
            state["last_sell_day"] = day_index
            if portfolio.shares - qty < 1e-6:
                state["in_position"] = False
