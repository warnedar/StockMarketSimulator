# stock_market_simulator/utils/config_parser.py

import os
from stock_market_simulator.strategies.base_strategies import STRATEGY_MAP


def parse_config_file(config_path):
    """
    Parses a config file of the form:
      years=5
      stepsize=1
      approach=SomeName
          ticker=^GSPC, strategy=buy_hold, spread=1
          ticker=^IXIC, strategy=advanced_daytrading
      ...
    Returns: (years, stepsize, approaches)
      where approaches = [(approach_name, {ticker: {
          "strategy": strategy_func,
          "spread": spread_value (as a percentage),
          "expense_ratio": optional yearly expense ratio (%)
      } }), ...]

    Note: The optional 'spread' parameter is interpreted as a percentage.
          For example, spread=1 means a 1% bid/ask spread.  Another optional
          parameter is 'expense_ratio', representing an annual management fee
          percentage that will be deducted daily from the portfolio.
    """
    years = None
    stepsize = None
    approaches = []

    current_approach_name = None
    current_ticker_dict = {}

    def flush_approach():
        nonlocal current_approach_name, current_ticker_dict, approaches
        if current_approach_name is not None and current_ticker_dict:
            approaches.append((current_approach_name, current_ticker_dict))
        current_approach_name = None
        current_ticker_dict = {}

    with open(config_path, 'r') as f:
        for line in f:
            line_strip = line.strip()
            if not line_strip or line_strip.startswith('#'):
                continue

            # approach=ApproachName
            if line_strip.lower().startswith("approach="):
                flush_approach()
                approach_name = line_strip[len("approach="):].strip()
                current_approach_name = approach_name

            # ticker=^GSPC, strategy=buy_hold, spread=1
            elif line_strip.lower().startswith("ticker="):
                if current_approach_name is None:
                    print(f"Warning: found ticker= line but no approach block open => {line_strip}")
                    continue

                portion = line_strip[len("ticker="):].strip()
                parts = [p.strip() for p in portion.split(',')]
                if len(parts) < 2:
                    print(f"Warning: invalid ticker line => {line_strip}")
                    continue

                ticker_str = parts[0]  # e.g. ^GSPC
                strategy_str = None
                for sp in parts[1:]:
                    if sp.lower().startswith("strategy="):
                        strategy_str = sp[len("strategy="):].strip()
                        break

                if not strategy_str:
                    print(f"Warning: missing 'strategy=' => {line_strip}")
                    continue

                if strategy_str not in STRATEGY_MAP:
                    print(f"Warning: unknown strategy '{strategy_str}' => {line_strip}")
                    continue

                # Optional parameters for this ticker line
                spread_val = 0.0      # bid/ask spread percent
                expense_ratio_val = 0.0  # yearly expense ratio percent
                for sp in parts[1:]:
                    low = sp.lower()
                    if low.startswith("spread="):
                        try:
                            spread_val = float(sp[len("spread="):].strip())
                        except ValueError:
                            print(f"Warning: invalid spread value in line => {line_strip}")
                    elif low.startswith("expense_ratio="):
                        try:
                            expense_ratio_val = float(sp[len("expense_ratio="):].strip())
                        except ValueError:
                            print(f"Warning: invalid expense_ratio in line => {line_strip}")

                # Map the ticker to a dict with strategy, spread, and expense_ratio
                current_ticker_dict[ticker_str] = {
                    "strategy": STRATEGY_MAP[strategy_str],
                    "spread": spread_val,
                    "expense_ratio": expense_ratio_val,
                }

            # maybe years=5 or stepsize=1
            elif '=' in line_strip:
                key, val = line_strip.split('=', 1)
                key = key.strip().lower()
                val = val.strip()
                if key == 'years':
                    years = int(val)
                elif key == 'stepsize':
                    stepsize = int(val)
                else:
                    print(f"Warning: unknown config param => {key}")

            else:
                print(f"Warning: ignoring line => {line_strip}")

    # flush last approach
    flush_approach()

    # final checks
    if years is None or years <= 0:
        raise ValueError("Config missing 'years' or it's <= 0.")

    if stepsize is None or stepsize < 1:
        raise ValueError("Config missing 'stepsize' or it's <1.")

    if not approaches:
        raise ValueError("No approaches defined in config.")

    return years, stepsize, approaches
