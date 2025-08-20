"""Convenience script for parameter optimisation sweeps.

This module demonstrates how to drive the :mod:`optimization.parameter_sweeper`
utilities.  It sets up a single-ticker approach, defines candidate parameter
ranges and then calls :func:`optimize_full_advanced_daytrading` to exhaustively
search those combinations.  The best results for each simulation window are
reported on the console and summarised in a PDF.

The script is intentionally example-driven.  Users are expected to modify the
lists of candidate values or the strategy mapping to suit their own needs.
"""

import os
import sys
import pandas as pd
import multiprocessing

from stock_market_simulator.data.data_fetcher import load_historical_data
from stock_market_simulator.strategies.base_strategies import STRATEGY_MAP
from stock_market_simulator.optimization.parameter_sweeper import (
    optimize_full_advanced_daytrading,
    metric_cagr,
)
from stock_market_simulator.optimization.report_pdf import create_pdf_report


def main():
    """Run the optimisation sweep and generate a PDF summary."""

    output_name = "optimization_output"
    if len(sys.argv) >= 2:
        output_name = sys.argv[1]

    out_dir = os.path.join("reports", output_name)
    os.makedirs(out_dir, exist_ok=True)

    # Specify the ticker and load historical data.  ``QQQ`` is used as a default
    # because it has a long and liquid price history.
    ticker = "QQQ"
    df = load_historical_data(ticker)

    # Build the ``ticker_info_dict`` expected by the simulator.  We start with a
    # simple buy-and-hold strategy; the optimisation routine will replace the
    # advanced-daytrading parameters for each grid-search candidate.
    ticker_info_dict = {
        ticker: {
            # "strategy": STRATEGY_MAP["advanced_daytrading"],
            "strategy": STRATEGY_MAP["buy_hold"],
            "spread": 0.05,  # example spread (percentage)
            "expense_ratio": 0.2,
        }
    }

    # Preloaded historical data for all tickers in this approach.
    dfs_dict = {ticker: df}

    # Candidate simulation windows and strategy parameters.  These were chosen
    # to provide a reasonably sized search space for demonstration purposes.
    candidate_years = [5, 6, 7, 8, 9, 10]
    trailing_stop_values = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
    limit_buy_discount_values = [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
    pending_limit_days_values = [30, 35, 40, 45, 50, 55, 60]
    initial_cash = 10000.0

    # Optimise using compound annual growth rate (CAGR) as the metric.  ``None``
    # for ``max_workers`` means "use all available cores".
    best_by_year = optimize_full_advanced_daytrading(
        ticker_info_dict,
        dfs_dict,
        candidate_years,
        initial_cash,
        trailing_stop_values,
        limit_buy_discount_values,
        pending_limit_days_values,
        metric_selector=metric_cagr,
        max_workers=None,
    )

    # Present results for each candidate year window.  ``best_by_year`` maps a
    # years value to (best_params, best_avg_metric, all_group_results).
    for years_val, (best_params, best_avg, all_groups) in best_by_year.items():
        print(f"For simulation window = {years_val} years:")
        print(
            f"  Best advanced parameters: Trailing Stop: {best_params[0]}%, "
            f"Limit Discount: {best_params[1]}%, Pending Limit Days: {best_params[2]}"
        )
        print(f"  Highest average metric (e.g. CAGR): {best_avg:.2f}%")
        # Uncomment below to inspect every parameter combination.
        # for params, avg_metric in all_groups.items():
        #     print(f"    {params}: {avg_metric:.2f}%")

    # Generate PDF summary report for easy sharing.
    create_pdf_report(best_by_year, out_dir)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
