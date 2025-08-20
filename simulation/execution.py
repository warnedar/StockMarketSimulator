"""Trade execution engine used by the simulator.

The strategies place orders into a :class:`Portfolio` instance.  On each trading
day the simulator calls :func:`execute_orders` which walks through the pending
orders and executes those whose conditions are met.  The design is intentionally
minimal – it does not attempt to model a full exchange but instead applies a
simple fixed bid/ask spread and supports a handful of order types relevant to
the built-in strategies.
"""

from stock_market_simulator.simulation.portfolio import Portfolio, Order


def execute_orders(current_price, portfolio: Portfolio, day_index):
    """Evaluate and execute any pending orders for the given day.

    Parameters
    ----------
    current_price:
        The market price of the asset on the current day.
    portfolio:
        :class:`Portfolio` holding cash, shares and pending orders.
    day_index:
        Integer index of the current simulation day (used by some strategies for
        timing).  Orders carry their placement day so we can compute how long
        they have been outstanding.

    The function mutates ``portfolio`` in place by adjusting cash/share balances
    and removing orders that were executed.

    Notes
    -----
    ``portfolio.spread`` represents the total bid/ask spread as a percentage
    (e.g. ``1`` for a 1% spread).  The execution price uses half the spread on
    each side:

    * Buy orders pay ``current_price * (1 + spread/200)``
    * Sell orders receive ``current_price * (1 - spread/200)``
    """
    executed = []
    # Retrieve the fixed spread (default 0.0 if not set), interpreted as a
    # percentage.  ``half_spread_fraction`` is the amount added/subtracted from
    # the price depending on order side.
    spread = getattr(portfolio, "spread", 0.0)
    half_spread_fraction = spread / 200.0  # e.g., spread=1 -> 0.005

    for order in portfolio.orders:
        # Determine the effective execution price based on order side.
        if order.side == 'buy':
            effective_price = current_price * (1 + half_spread_fraction)
        else:  # sell
            effective_price = current_price * (1 - half_spread_fraction)

        # MARKET orders execute immediately at the current price adjusted for
        # spread.
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

        # LIMIT orders execute only when the effective price crosses the
        # specified limit.
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

        # STOP orders trigger when the effective price breaches the stop level.
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

        # TRAILING STOP orders dynamically adjust their trigger based on the
        # highest price seen since placement.  They are currently only used for
        # sell orders in the built-in strategies.
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
