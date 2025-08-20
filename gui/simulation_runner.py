"""Helper functions for the GUI to run simulations.

The GUI keeps user interaction and plotting logic separate from the core
simulation routines.  This module provides a thin wrapper that prepares the
input data structures expected by :func:`simulation.simulator.run_hybrid_multi_fund`.
"""

import pandas as pd
from datetime import datetime
from stock_market_simulator.simulation.simulator import (
    run_hybrid_multi_fund,
    intersect_all_indexes,
    HybridMultiFundPortfolio,
)


def run_simulation(ticker_info_dict, dfs_dict, start_date_str, years, initial_cash=10000.0):
    """Run a single simulation for the given approach over the specified window.

    Parameters
    ----------
    ticker_info_dict:
        Mapping of ticker symbol to strategy configuration.  The GUI builds this
        from the selected approach in the config file.
    dfs_dict:
        Mapping of ticker symbol to full historical price DataFrames.
    start_date_str:
        Simulation start date (YYYY-MM-DD).
    years:
        Length of the simulation window in years.
    initial_cash:
        Starting cash for the virtual portfolio.

    Returns
    -------
    history:
        List of percent total returns for each simulation day.
    final_index:
        :class:`pandas.DatetimeIndex` corresponding to the simulation dates.
    """

    # Convert start date string to Timestamp and compute end date.
    start_date = pd.to_datetime(start_date_str)
    end_date = start_date + pd.Timedelta(days=years * 365)

    # Filter each ticker's data to the simulation window.
    sim_dfs = {}
    for ticker, df in dfs_dict.items():
        subdf = df.loc[(df.index >= start_date) & (df.index < end_date)]
        sim_dfs[ticker] = subdf

    # Intersect indexes among tickers to ensure the portfolios see the same
    # trading days for all symbols.
    common_idx = intersect_all_indexes(sim_dfs)
    if common_idx.empty:
        raise ValueError("No common trading days in the specified simulation window.")

    # Reindex each DataFrame to the common index, forward filling missing data
    # to handle holidays or other missing observations.
    for ticker in sim_dfs:
        sim_dfs[ticker] = sim_dfs[ticker].reindex(common_idx, method='ffill')

    # Create the portfolio for this approach and run the simulation using the
    # common engine shared with the command line tools.
    portfolio = HybridMultiFundPortfolio(ticker_info_dict, initial_cash=initial_cash)
    history, final_index = run_hybrid_multi_fund(sim_dfs, portfolio)

    return history, final_index
