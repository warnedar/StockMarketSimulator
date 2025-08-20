# stock_market_simulator/optimization/parameter_sweeper.py

"""Grid-search utilities for optimising strategy parameters.

The functions in this module perform exhaustive parameter sweeps for the
``advanced_daytrading`` strategy.  The optimisation is CPU intensive, therefore
the code uses :class:`concurrent.futures.ProcessPoolExecutor` with an
initialisation step that shares large read-only data structures via global
variables.  This avoids repeatedly pickling the historical price DataFrames for
each task.
"""

import itertools
import concurrent.futures
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from stock_market_simulator.simulation.simulator import (
    run_hybrid_multi_fund,
    intersect_all_indexes,
    find_monthly_starts_first_open,
    HybridMultiFundPortfolio,
)

# Shared data loaded once per worker.  These globals are populated by the
# process pool initializer to avoid repeatedly sending large DataFrames to every
# task.
_DFS_DICT = None
_TICKER_INFO_DICT = None


def _init_worker(dfs_dict, ticker_info_dict):
    """Initializer for worker processes."""
    global _DFS_DICT, _TICKER_INFO_DICT
    _DFS_DICT = dfs_dict
    _TICKER_INFO_DICT = ticker_info_dict


def run_advanced_daytrading_simulation(ticker_info_dict, dfs_dict, start_date, years, initial_cash=10000.0,
                                       return_history=False):
    """
    Runs a simulation for the given advanced_daytrading approach over the specified window.

    Parameters:
      ticker_info_dict: dict mapping ticker -> { "strategy": strategy_func, "spread": spread, ... }
      dfs_dict: dict mapping ticker -> DataFrame of historical data.
      start_date: pd.Timestamp indicating the simulation start date.
      years: Simulation window length in years.
      initial_cash: Starting cash.
      return_history: If True, returns the full history list; otherwise returns the final percent return.

    Returns:
      If return_history is False: final percent return.
      If return_history is True: the full history list.
    """
    sim_dfs = {}
    end_date = start_date + pd.Timedelta(days=years * 242)
    for ticker, df in dfs_dict.items():
        subdf = df.loc[(df.index >= start_date) & (df.index < end_date)]
        sim_dfs[ticker] = subdf

    common_idx = intersect_all_indexes(sim_dfs)
    if common_idx.empty:
        raise ValueError("No common trading days in the simulation window.")

    for ticker in sim_dfs:
        sim_dfs[ticker] = sim_dfs[ticker].reindex(common_idx, method='ffill')

    portfolio = HybridMultiFundPortfolio(ticker_info_dict, initial_cash=initial_cash)
    history, _ = run_hybrid_multi_fund(sim_dfs, portfolio)
    if return_history:
        return history
    return history[-1]


# Example metric selector functions:
def metric_final(history, years):
    """Return the final percent return."""
    return history[-1]


def metric_cagr(history, years):
    """Return the compound annual growth rate (CAGR)."""
    final_return = history[-1]
    total_growth = 1.0 + (final_return / 100.0)
    if years <= 0:
        return 0.0
    return (total_growth ** (1 / years) - 1) * 100.0


def metric_highest_peak(history, years):
    """Return the highest peak value during the simulation."""
    return max(history)


def metric_lowest_valley(history, years):
    """Return the lowest valley value during the simulation."""
    return min(history)


def metric_average(history, years):
    """Return the average of the simulation history."""
    return np.mean(history)


def metric_median(history, years):
    """Return the median value of the simulation history."""
    return np.median(history)


def candidate_worker(args):
    """Run a single candidate simulation.

    Args is a tuple:
      (start_date, years, ts_pct, lb_discount, pl_days, initial_cash, metric_selector)
    or the legacy form where ticker_info_dict and dfs_dict are provided.

    Returns:
      (start_date, years, ts_pct, lb_discount, pl_days, metric_value)
    """
    global _DFS_DICT, _TICKER_INFO_DICT

    # Backwards compatibility: allow old task tuples that include the data dicts.
    if len(args) == 9:
        ticker_info_dict, dfs_dict, start_date, years, ts_pct, lb_discount, pl_days, initial_cash, metric_selector = args
    else:
        start_date, years, ts_pct, lb_discount, pl_days, initial_cash, metric_selector = args
        ticker_info_dict = _TICKER_INFO_DICT
        dfs_dict = _DFS_DICT

    modified_ticker_info = {}
    for ticker, info in ticker_info_dict.items():
        new_info = info.copy()
        if info["strategy"].__name__ == "advanced_daytrading":
            new_info["trailing_stop_pct"] = ts_pct
            new_info["limit_buy_discount_pct"] = lb_discount
            new_info["pending_limit_days"] = pl_days
        modified_ticker_info[ticker] = new_info
    try:
        history = run_advanced_daytrading_simulation(modified_ticker_info, dfs_dict, start_date, years, initial_cash,
                                                     return_history=True)
        metric_value = metric_selector(history, years)
        return (start_date, years, ts_pct, lb_discount, pl_days, metric_value)
    except Exception as e:
        return (start_date, years, ts_pct, lb_discount, pl_days, None)


def full_parameter_sweep_advanced_daytrading(ticker_info_dict, dfs_dict, candidate_years, initial_cash,
                                             trailing_stop_values, limit_buy_discount_values, pending_limit_days_values,
                                             metric_selector=metric_final, max_workers=None):
    """
    Performs a grid search over simulation parameters and advanced_daytrading strategy parameters.

    It does the following:
      1. Computes the common trading days among all tickers.
      2. Determines the monthly start dates from that common index.
      3. For each candidate simulation window (years) and for each monthly start date (only if enough data exists),
         and for each combination of advanced parameters (trailing_stop_pct, limit_buy_discount_pct, pending_limit_days),
         runs a simulation and computes the performance metric using metric_selector(history, years).

    Parameters:
      max_workers: Maximum number of worker processes to use (default uses all available).

    Returns:
      results: A list of tuples:
         (start_date, years, trailing_stop_pct, limit_buy_discount_pct, pending_limit_days, metric_value)
    """
    common_idx = intersect_all_indexes(dfs_dict)
    monthly_starts = find_monthly_starts_first_open(common_idx)
    results = []
    last_common_date = common_idx[-1]

    # Build list of candidate tasks.
    tasks = []
    for years_val in candidate_years:
        for start_date in monthly_starts:
            # Preliminary check: ensure simulation window fits within available data.
            if start_date + pd.Timedelta(days=years_val * 365) > last_common_date:
                continue
            for ts_pct, lb_discount, pl_days in itertools.product(
                    trailing_stop_values, limit_buy_discount_values, pending_limit_days_values
            ):
                tasks.append((start_date, years_val, ts_pct, lb_discount, pl_days,
                              initial_cash, metric_selector))

    # Use ProcessPoolExecutor to run tasks in parallel. The historical data and
    # ticker info are loaded once per worker via the initializer to avoid
    # pickling large objects for every task.
    with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=_init_worker,
            initargs=(dfs_dict, ticker_info_dict)) as executor:
        n_workers = max_workers or os.cpu_count() or 1
        chunk_size = max(1, len(tasks) // (n_workers * 4))
        for result in tqdm(
                executor.map(candidate_worker, tasks, chunksize=chunk_size),
                total=len(tasks), desc="Running simulations"):
            results.append(result)

    return results


def optimize_full_advanced_daytrading(ticker_info_dict, dfs_dict, candidate_years, initial_cash,
                                      trailing_stop_values, limit_buy_discount_values, pending_limit_days_values,
                                      metric_selector=metric_final, max_workers=None):
    """
    Optimizes the advanced_daytrading strategy parameters along with the simulation window (years)
    by performing a grid search over:
       - Simulation window lengths (years)
       - Start dates (each monthly start that has enough data)
       - Advanced parameters: trailing_stop_pct, limit_buy_discount_pct, pending_limit_days

    Instead of picking a single best run overall, this function groups results by candidate year span and
    advanced parameters (ignoring the start date), computes the average performance metric across all available
    start dates for each group, and then for each candidate year selects the best advanced parameter combination
    (i.e. the one with the highest average metric value).

    Parameters:
      ticker_info_dict: dict mapping ticker -> { "strategy": strategy_func, "spread": spread, ... }
      dfs_dict: dict mapping ticker -> DataFrame of historical data.
      candidate_years: List of candidate simulation window lengths (in years).
      initial_cash: Starting cash.
      trailing_stop_values: List of candidate trailing stop percentages.
      limit_buy_discount_values: List of candidate limit order discount percentages.
      pending_limit_days_values: List of candidate days to wait before converting a limit order.
      metric_selector: Function that takes (history, years) and returns a performance metric.
      max_workers: Maximum number of parallel workers to use (default uses all available).

    Returns:
      best_by_year: A dictionary mapping each candidate year (window length) to a tuple:
                     (best_params, best_average_metric, all_group_results)
                     where best_params is a tuple (trailing_stop_pct, limit_buy_discount_pct, pending_limit_days)
                     with the highest average metric value for that year span,
                     and all_group_results is a dictionary mapping parameter tuples to their average metric value.
    """
    # Run the full sweep in parallel.
    results = full_parameter_sweep_advanced_daytrading(
        ticker_info_dict, dfs_dict, candidate_years, initial_cash,
        trailing_stop_values, limit_buy_discount_values, pending_limit_days_values,
        metric_selector=metric_selector, max_workers=max_workers
    )

    # Each result is: (start_date, years, ts_pct, lb_discount, pl_days, metric_value)
    # Group by candidate years and advanced parameters (ignore start_date).
    grouped = {}
    for r in results:
        if r[5] is None:
            continue
        # Group key: (years, trailing_stop_pct, limit_buy_discount_pct, pending_limit_days)
        key = (r[1], r[2], r[3], r[4])
        grouped.setdefault(key, []).append(r[5])

    # For each group, compute the average metric.
    groups_by_year = {}
    for key, metrics in grouped.items():
        years_val, ts_pct, lb_discount, pl_days = key
        avg_metric = sum(metrics) / len(metrics)
        groups_by_year.setdefault(years_val, {})[(ts_pct, lb_discount, pl_days)] = avg_metric

    # For each candidate years value, select the advanced parameter set with the best (highest) average metric.
    best_by_year = {}
    for years_val, param_dict in groups_by_year.items():
        best_params, best_avg = max(param_dict.items(), key=lambda x: x[1])
        best_by_year[years_val] = (best_params, best_avg, param_dict)

    return best_by_year

