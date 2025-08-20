# stock_market_simulator/strategies/sma_trading_strategy.py

"""
SMA Trading Strategy

This strategy uses two Simple Moving Averages (SMAs) calculated over 20-day and 50-day windows.
- BUY Condition: When the 20-day SMA exceeds the 50-day SMA and at least 1 day has passed since the last buy,
  buy using 20% of available cash.
- SELL Condition: When the current price exceeds 1.1 times the 20-day SMA and at least 3 days have passed since the last sell,
  sell 50% of current holdings.

The strategy stores its price history and last order days in portfolio.strategy_state.
"""

from stock_market_simulator.simulation.portfolio import Order, Portfolio

def sma_trading_strategy(portfolio: Portfolio, date, price, day_index):
    state = portfolio.strategy_state

    if "sma_trading_history" not in state:
        state["sma_trading_history"] = []
        state["last_buy_day"] = -100
        state["last_sell_day"] = -100

    history = state["sma_trading_history"]
    history.append(price)

    if len(history) < 50:
        # Need at least 50 data points to compute both moving averages.
        return

    sma_20 = sum(history[-20:]) / 20.0
    sma_50 = sum(history[-50:]) / 50.0

    last_buy_day = state.get("last_buy_day", -100)
    last_sell_day = state.get("last_sell_day", -100)
    days_since_buy = day_index - last_buy_day
    days_since_sell = day_index - last_sell_day

    # BUY when the short-term average crosses above the long-term average.  The
    # one-day cooldown avoids rapid flip-flopping if prices oscillate around the
    # crossover point.
    if sma_20 > sma_50 and days_since_buy >= 1:
        quantity_to_buy = (portfolio.cash * 0.20) / price
        if quantity_to_buy > 0:
            order = Order(side='buy', order_type='market', quantity=quantity_to_buy)
            order.placement_day = day_index
            portfolio.orders.append(order)
            state["last_buy_day"] = day_index

    # SELL after a 10% run-up over the 20-day average with a small cooldown to
    # avoid reacting to tiny spikes.
    if price > 1.1 * sma_20 and days_since_sell >= 3:
        quantity_to_sell = portfolio.shares * 0.50
        if quantity_to_sell > 0:
            order = Order(side='sell', order_type='market', quantity=quantity_to_sell)
            order.placement_day = day_index
            portfolio.orders.append(order)
            state["last_sell_day"] = day_index
