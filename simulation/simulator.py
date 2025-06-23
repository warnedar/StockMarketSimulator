# stock_market_simulator/simulation/simulator.py

import pandas as pd
from pandas import DataFrame, DatetimeIndex
from stock_market_simulator.simulation.portfolio import Portfolio
from stock_market_simulator.simulation.execution import execute_orders

class HybridMultiFundPortfolio:
    """
    Combines multiple sub-portfolios (one per ticker),
    each with its own strategy and slice of the total cash.
    """
    def __init__(self, ticker_info_dict: dict[str, dict], initial_cash: float = 10000.0) -> None:
        # ticker_info_dict is a mapping: ticker -> { "strategy": strategy_func, "spread": spread (as percentage),
        #     optionally "trailing_stop_pct", "limit_buy_discount_pct", "pending_limit_days" }
        self.initial_cash = initial_cash
        self.tickers = list(ticker_info_dict.keys())
        self.sub_portfolios = []
        sub_cash = initial_cash / len(self.tickers)
        self.strategies_for_tickers = {}
        for tkSym in self.tickers:
            pf = Portfolio(sub_cash)
            # Set the fixed bid/ask spread for this ticker.
            pf.spread = ticker_info_dict[tkSym].get("spread", 0.0)
            # Optional yearly expense ratio percentage.
            pf.expense_ratio = ticker_info_dict[tkSym].get("expense_ratio", 0.0)
            # If strategy is advanced_daytrading, attach advanced parameters (if provided) to the portfolio.
            if ticker_info_dict[tkSym]["strategy"].__name__ == "advanced_daytrading":
                advanced_params = {}
                if "trailing_stop_pct" in ticker_info_dict[tkSym]:
                    advanced_params["trailing_stop_pct"] = ticker_info_dict[tkSym]["trailing_stop_pct"]
                if "limit_buy_discount_pct" in ticker_info_dict[tkSym]:
                    advanced_params["limit_buy_discount_pct"] = ticker_info_dict[tkSym]["limit_buy_discount_pct"]
                if "pending_limit_days" in ticker_info_dict[tkSym]:
                    advanced_params["pending_limit_days"] = ticker_info_dict[tkSym]["pending_limit_days"]
                pf.advanced_params = advanced_params
            self.sub_portfolios.append((tkSym, pf))
            self.strategies_for_tickers[tkSym] = ticker_info_dict[tkSym]["strategy"]
        self.history: list[float] = []

    def total_value(self, day_prices: dict[str, float]) -> float:
        """
        Computes total portfolio value given a dict of day_prices.
        """
        tv = 0.0
        for (sym, pf) in self.sub_portfolios:
            px = day_prices.get(sym, 0.0)
            tv += pf.total_value(px)
        return tv

def run_hybrid_multi_fund(dfs_dict: dict[str, DataFrame], hybrid_pf: HybridMultiFundPortfolio) -> tuple[list[float], DatetimeIndex]:
    """Run a day-by-day simulation for ``hybrid_pf`` using ``dfs_dict``.

    Parameters
    ----------
    dfs_dict:
        Mapping of ticker symbols to price DataFrames. Each DataFrame must
        contain a ``'Close'`` column.
    hybrid_pf:
        The :class:`HybridMultiFundPortfolio` to operate on.

    Returns
    -------
    tuple[list[float], :class:`pandas.DatetimeIndex`]
        History of percent gains and the index used for simulation.
    """
    tickers = hybrid_pf.tickers
    main_tk = tickers[0]
    final_index = dfs_dict[main_tk].index
    hybrid_pf.history = []

    for day_i, dt in enumerate(final_index):
        day_prices = {}
        for tkSym in tickers:
            val = dfs_dict[tkSym].loc[dt, 'Close']
            if isinstance(val, pd.Series):
                val = val.iloc[0]
            cprice = float(val)
            day_prices[tkSym] = cprice

        # Execute pending orders and run strategy for each sub-portfolio.
        for (sym, pf) in hybrid_pf.sub_portfolios:
            cur_price = day_prices[sym]
            execute_orders(cur_price, pf, day_i)
            strategy_func = hybrid_pf.strategies_for_tickers[sym]
            strategy_func(pf, dt, cur_price, day_i)
            # Deduct daily expense ratio fee
            daily_fee = pf.total_value(cur_price) * (pf.expense_ratio / 100.0) / 365.0
            pf.cash -= daily_fee

        tv = hybrid_pf.total_value(day_prices)
        pct = ((tv - hybrid_pf.initial_cash) / hybrid_pf.initial_cash) * 100
        hybrid_pf.history.append(pct)

    return hybrid_pf.history, final_index

def intersect_all_indexes(dfs_dict: dict[str, DataFrame]) -> DatetimeIndex:
    """Intersect indexes among all DataFrames to ensure alignment."""
    all_idx = [df.index for df in dfs_dict.values()]
    if not all_idx:
        raise ValueError("No DataFrames to intersect!")
    common = all_idx[0]
    for idx in all_idx[1:]:
        common = common.intersection(idx)
    return common.sort_values()

def find_monthly_starts_first_open(common_idx: DatetimeIndex) -> list[pd.Timestamp]:
    """Return the first open date of each month within ``common_idx``."""
    by_ym = {}
    for dt in common_idx:
        ym = (dt.year, dt.month)
        if ym not in by_ym:
            by_ym[ym] = dt
    keys = sorted(by_ym.keys())
    monthly_starts = [by_ym[k] for k in keys]
    return monthly_starts

def run_configured_sweep(dfs_dict: dict[str, DataFrame], approach_name: str, ticker_info_dict: dict[str, dict], years: int, stepsize: int, initial_cash: float = 10000.0) -> tuple[dict, list, dict]:
    """Run multiple subrange simulations and compute performance metrics."""
    common_idx = intersect_all_indexes(dfs_dict)
    if common_idx.empty:
        raise ValueError(f"No intersection for approach {approach_name}.")

    all_monthly_starts = find_monthly_starts_first_open(common_idx)
    selected_starts = all_monthly_starts[::stepsize]

    delta_days = pd.Timedelta(days=years * 365)
    results_list = []
    final_map = {}

    for start_date in selected_starts:
        end_date = start_date + delta_days
        if end_date > common_idx[-1]:
            continue

        final_subindex = common_idx[(common_idx >= start_date) & (common_idx < end_date)]
        if len(final_subindex) == 0:
            continue

        sim_dfs = {}
        for tk, df_ticker in dfs_dict.items():
            subdf = df_ticker.loc[(df_ticker.index >= start_date) & (df_ticker.index < end_date)]
            subdf = subdf.reindex(final_subindex, method='ffill')
            sim_dfs[tk] = subdf

        pf = HybridMultiFundPortfolio(ticker_info_dict, initial_cash=initial_cash)
        hist, _ = run_hybrid_multi_fund(sim_dfs, pf)
        if not hist:
            continue

        lv = min(hist)
        hv = max(hist)
        fr = hist[-1]
        total_growth = 1.0 + (fr / 100.0)
        cagr = (total_growth ** (1 / years) - 1) * 100.0 if years > 0 else 0.0
        results_list.append((lv, hv, fr, cagr, start_date))
        final_map[start_date] = fr

    if not results_list:
        raise ValueError(f"No valid runs for approach '{approach_name}' (years={years}).")

    lows = [x[0] for x in results_list]
    highs = [x[1] for x in results_list]
    finals = [x[2] for x in results_list]
    aars = [x[3] for x in results_list]

    def avg(arr):
        return sum(arr) / len(arr) if arr else None

    summary = {
        "lowest_valley": {"min_val": min(lows), "min_start_date": next(x for x in results_list if x[0] == min(lows))[4],
                           "max_val": max(lows), "max_start_date": next(x for x in results_list if x[0] == max(lows))[4],
                           "avg_val": avg(lows)},
        "highest_peak": {"min_val": min(highs), "min_start_date": next(x for x in results_list if x[1] == min(highs))[4],
                         "max_val": max(highs), "max_start_date": next(x for x in results_list if x[1] == max(highs))[4],
                         "avg_val": avg(highs)},
        "final_result": {"min_val": min(finals), "min_start_date": next(x for x in results_list if x[2] == min(finals))[4],
                         "max_val": max(finals), "max_start_date": next(x for x in results_list if x[2] == max(finals))[4],
                         "avg_val": avg(finals)},
        "avg_annual_return": {"min_val": min(aars), "min_start_date": next(x for x in results_list if x[3] == min(aars))[4],
                              "max_val": max(aars), "max_start_date": next(x for x in results_list if x[3] == max(aars))[4],
                              "avg_val": avg(aars)}
    }

    return summary, results_list, final_map
