# stock_market_simulator/simulation/portfolio.py

class Order:
    """Represents a single order placed by a strategy."""

    def __init__(self, side: str, order_type: str,
                 limit_price: float | None = None, stop_price: float | None = None,
                 trail_percent: float | None = None, quantity: float | None = None) -> None:
        """Create a new order.

        Parameters
        ----------
        side:
            ``"buy"`` or ``"sell"``.
        order_type:
            The type of order (``"market"``, ``"limit"``, ``"stop"`` or ``"trailing_stop"``).
        limit_price:
            Price threshold for limit orders.
        stop_price:
            Price threshold for stop orders.
        trail_percent:
            Percent used for trailing stop orders.
        quantity:
            Quantity of shares for the order or ``None`` for all available.
        """

        self.side = side
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trail_percent = trail_percent
        self.quantity = quantity
        self.highest_price: float | None = None
        self.lowest_price: float | None = None
        self.placement_day: int | None = None


class Portfolio:
    """Simple portfolio tracking cash, shares and open orders."""

    def __init__(self, initial_cash: float = 10000.0) -> None:
        """Create a portfolio with a starting cash balance."""

        self.cash: float = initial_cash
        self.shares: float = 0.0
        self.orders: list[Order] = []
        self.initial_value: float = initial_cash
        self.history: list[float] = []
        self.strategy_state: dict = {}

    def total_value(self, price: float) -> float:
        """Return the cash value of the portfolio at ``price``."""

        return self.cash + self.shares * price
