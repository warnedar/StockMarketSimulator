# stock_market_simulator/simulation/execution.py

from stock_market_simulator.simulation.portfolio import Portfolio, Order


def execute_orders(current_price, portfolio: Portfolio, day_index):
    """
    Executes any existing orders in the portfolio if their conditions are met.
    Removes executed orders from the portfolio's order list.

    This version takes into account a fixed bid/ask spread stored in portfolio.spread,
    which is now interpreted as a percentage.

    For buy orders, the effective execution price is:
      current_price * (1 + (spread/200))
    For sell orders, it is:
      current_price * (1 - (spread/200))

    This adjustment applies half the spread percentage on either side.
    """
    executed = []
    # Retrieve the fixed spread (default 0.0 if not set), interpreted as a percentage.
    spread = getattr(portfolio, "spread", 0.0)
    half_spread_fraction = spread / 200.0  # e.g., if spread=1 (1%), half is 0.5% expressed as 0.005

    for order in portfolio.orders:
        # Determine the effective execution price based on order side.
        if order.side == 'buy':
            effective_price = current_price * (1 + half_spread_fraction)
        else:  # sell
            effective_price = current_price * (1 - half_spread_fraction)

        # MARKET orders
        if order.order_type == 'market':
            if order.side == 'buy':
                to_buy = (portfolio.cash / effective_price if order.quantity is None
                          else min(order.quantity, portfolio.cash / effective_price))
                if to_buy > 0:
                    portfolio.shares += to_buy
                    portfolio.cash -= to_buy * effective_price
            else:  # sell
                to_sell = (portfolio.shares if order.quantity is None
                           else min(order.quantity, portfolio.shares))
                if to_sell > 0:
                    portfolio.cash += to_sell * effective_price
                    portfolio.shares -= to_sell
            executed.append(order)

        # LIMIT orders
        elif order.order_type == 'limit':
            if order.side == 'buy' and effective_price <= order.limit_price:
                to_buy = (portfolio.cash / effective_price if order.quantity is None
                          else min(order.quantity, portfolio.cash / effective_price))
                if to_buy > 0:
                    portfolio.shares += to_buy
                    portfolio.cash -= to_buy * effective_price
                executed.append(order)
            elif order.side == 'sell' and effective_price >= order.limit_price:
                to_sell = (portfolio.shares if order.quantity is None
                           else min(order.quantity, portfolio.shares))
                if to_sell > 0:
                    portfolio.cash += to_sell * effective_price
                    portfolio.shares -= to_sell
                executed.append(order)

        # STOP orders
        elif order.order_type == 'stop':
            if order.side == 'sell' and effective_price <= order.stop_price:
                to_sell = (portfolio.shares if order.quantity is None
                           else min(order.quantity, portfolio.shares))
                if to_sell > 0:
                    portfolio.cash += to_sell * effective_price
                    portfolio.shares -= to_sell
                executed.append(order)
            elif order.side == 'buy' and effective_price >= order.stop_price:
                to_buy = (portfolio.cash / effective_price if order.quantity is None
                          else min(order.quantity, portfolio.cash / effective_price))
                if to_buy > 0:
                    portfolio.shares += to_buy
                    portfolio.cash -= to_buy * effective_price
                executed.append(order)

        # TRAILING STOP orders
        elif order.order_type == 'trailing_stop':
            if order.side == 'sell':
                if order.highest_price is None:
                    order.highest_price = effective_price
                if effective_price > order.highest_price:
                    order.highest_price = effective_price

                trigger = order.highest_price * (1 - (order.trail_percent or 0) / 100.0)
                if effective_price <= trigger:
                    to_sell = (portfolio.shares if order.quantity is None
                               else min(order.quantity, portfolio.shares))
                    if to_sell > 0:
                        portfolio.cash += to_sell * effective_price
                        portfolio.shares -= to_sell
                    executed.append(order)

    # Remove executed orders from the portfolio.
    for e in executed:
        portfolio.orders.remove(e)
