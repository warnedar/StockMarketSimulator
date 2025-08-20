# run_optimization.py

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
    """Run optimization sweep and generate a PDF summary."""
    output_name = "optimization_output"
    if len(sys.argv) >= 2:
        output_name = sys.argv[1]

    out_dir = os.path.join("reports", output_name)
    os.makedirs(out_dir, exist_ok=True)

    # Specify the ticker and load historical data.
    ticker = "QQQ"  # or any ticker using the advanced_daytrading strategy
    df = load_historical_data(ticker)

    # Create a ticker_info_dict for the advanced_daytrading strategy.
    ticker_info_dict = {
        ticker: {
            # "strategy": STRATEGY_MAP["advanced_daytrading"],
            "strategy": STRATEGY_MAP["buy_hold"],
            "spread": 0.05,  # example spread (percentage)
            "expense_ratio": 0.2
            # Advanced parameters will be overridden in the grid search.
        }
    }

    # Create a dictionary for historical data for all tickers in this approach.
    dfs_dict = {ticker: df}

    # Define candidate simulation window lengths and advanced parameter candidates.
    candidate_years = [5, 6, 7, 8, 9, 10]
    trailing_stop_values = [7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0]
    limit_buy_discount_values = [3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
    pending_limit_days_values = [30, 35, 40, 45,  50, 55, 60]
    initial_cash = 10000.0

    # For example, optimize based on CAGR.
    from stock_market_simulator.optimization.parameter_sweeper import optimize_full_advanced_daytrading, metric_cagr
    best_by_year = optimize_full_advanced_daytrading(
        ticker_info_dict, dfs_dict, candidate_years, initial_cash,
        trailing_stop_values, limit_buy_discount_values, pending_limit_days_values,
        metric_selector=metric_cagr, max_workers=None
    )

    # Print the results for each candidate year.
    for years_val, (best_params, best_avg, all_groups) in best_by_year.items():
        print(f"For simulation window = {years_val} years:")
        print(
            f"  Best advanced parameters: Trailing Stop: {best_params[0]}%, Limit Discount: {best_params[1]}%, Pending Limit Days: {best_params[2]}")
        print(f"  Highest average metric (e.g. CAGR): {best_avg:.2f}%")
        # print("  All group results:")
        # for params, avg_metric in all_groups.items():
        #     print(f"    {params}: {avg_metric:.2f}%")

    # Generate PDF summary report
    create_pdf_report(best_by_year, out_dir)

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
