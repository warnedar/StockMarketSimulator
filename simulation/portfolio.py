# stock_market_simulator/simulation/portfolio.py

class Order:
    def __init__(self, side, order_type,
                 limit_price=None, stop_price=None,
                 trail_percent=None, quantity=None):
        self.side = side
        self.order_type = order_type
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.trail_percent = trail_percent
        self.quantity = quantity
        self.highest_price = None
        self.lowest_price = None
        self.placement_day = None


class Portfolio:
    def __init__(self, initial_cash=10000.0):
        self.cash = initial_cash
        self.shares = 0.0
        self.orders = []
        self.initial_value = initial_cash
        self.history = []
        self.strategy_state = {}

    def total_value(self, price: float) -> float:
        return self.cash + self.shares * price
