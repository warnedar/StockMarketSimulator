# stock_market_simulator/gui/simulation_runner.py

import pandas as pd
from datetime import datetime
from config import DEFAULT_CASH
from stock_market_simulator.simulation.simulator import (
    run_hybrid_multi_fund,
    intersect_all_indexes,
    HybridMultiFundPortfolio,
)


def run_simulation(
    ticker_info_dict,
    dfs_dict,
    start_date_str,
    years,
    initial_cash: float = DEFAULT_CASH,
):
    """
    Run a single simulation for the given approach over the specified window.

    Parameters:
      ticker_info_dict: dict mapping ticker -> { "strategy": strategy_func, "spread": spread (as percentage) }
      dfs_dict: dict mapping ticker -> DataFrame of historical data.
      start_date_str: Simulation start date (YYYY-MM-DD).
      years: Simulation window (years).
      initial_cash: Starting cash.

    Returns:
      history: List of percent total returns for each simulation day.
      final_index: DateTimeIndex corresponding to simulation dates.
    """
    # Convert start date string to Timestamp and compute end date.
    start_date = pd.to_datetime(start_date_str)
    end_date = start_date + pd.Timedelta(days=years * 365)

    # Filter each ticker's data to the simulation window.
    sim_dfs = {}
    for ticker, df in dfs_dict.items():
        subdf = df.loc[(df.index >= start_date) & (df.index < end_date)]
        sim_dfs[ticker] = subdf

    # Intersect indexes among tickers.
    common_idx = intersect_all_indexes(sim_dfs)
    if common_idx.empty:
        raise ValueError("No common trading days in the specified simulation window.")

    # Reindex each DataFrame to the common index.
    for ticker in sim_dfs:
        sim_dfs[ticker] = sim_dfs[ticker].reindex(common_idx, method='ffill')

    # Create the portfolio for this approach.
    portfolio = HybridMultiFundPortfolio(ticker_info_dict, initial_cash=initial_cash)

    # Run the simulation using your common simulation engine.
    history, final_index = run_hybrid_multi_fund(sim_dfs, portfolio)

    return history, final_index
