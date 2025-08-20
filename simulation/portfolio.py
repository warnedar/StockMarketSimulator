"""Simplified portfolio and order models used by the simulator.

The goal of the project is educational rather than to emulate a full-featured
brokerage.  The :class:`Portfolio` and :class:`Order` classes therefore expose
only the minimal surface area needed by the strategies.  They can be extended
in the future if more advanced features are required.
"""


class Order:
    """Represents a standing order in the portfolio."""

    def __init__(
        self,
        side,
        order_type,
        limit_price=None,
        stop_price=None,
        trail_percent=None,
        quantity=None,
    ):
        self.side = side
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trail_percent = trail_percent
        self.quantity = quantity
        # Track highest/lowest prices since order placement for trailing stops
        # or other future order types.
        self.highest_price = None
        self.lowest_price = None
        self.placement_day = None


class Portfolio:
    """Holds cash, shares and pending orders for a single ticker."""

    def __init__(self, initial_cash=10000.0):
        self.cash = initial_cash
        self.shares = 0.0
        self.orders = []
        self.initial_value = initial_cash
        self.history = []
        # ``strategy_state`` is a free-form dictionary used by strategies to
        # keep their own state without subclassing Portfolio.
        self.strategy_state = {}

    def total_value(self, price: float) -> float:
        """Return the market value of the portfolio at ``price``."""

        return self.cash + self.shares * price
