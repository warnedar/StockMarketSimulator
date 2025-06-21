# Stock Market Simulator

This repository contains a small trading simulation framework written in Python.  
It allows you to backtest several strategies on historical market data and generate
summary reports or plots.  Historical data is fetched with `yfinance` and cached
locally so repeated runs are fast.

## Features
- **Config driven sweeps** – use `main.py` with a config file to run multiple
  strategies over different time windows and generate a report with plots.
- **Strategies** – buy & hold, SMA trading, momentum breakout, RSI and an
  advanced day trading strategy with trailing stops and limit orders.
- **Data caching** – downloads of historical price data are saved to
  `data/local_csv` and automatically updated when new data is available.
- **Parameter optimization** – `run_optimization.py` can sweep advanced day
  trading parameters to find combinations with the best performance metric.
- **GUI** – a Tkinter interface in `gui/visualizer.py` lets you run simulations
  interactively and view the resulting equity curves.
- **Automatic PDF summaries** – results folders include a single PDF combining
  the config, console log and all generated plots.

## Requirements
Install the Python dependencies via:

```bash
pip install -r requirements.txt
```

The simulator relies on `pandas`, `yfinance`, `matplotlib` and `fpdf`.

## Usage
### Running a sweep
Use `main.py` with a configuration file that defines the approaches and ticker
strategies.  Example:

```bash
python -m stock_market_simulator.main config/configA.txt my_report
```

Each `ticker=` line can optionally include `spread` (bid/ask percentage) and
`expense_ratio` (annual fee percentage).  The expense ratio is deducted daily
during simulation.

Results are written to `reports/my_report/` including plots, a `report.txt`
with detailed statistics and a consolidated `report.pdf`.

### GUI
To explore strategies interactively, launch the visualizer:

```bash
python -m stock_market_simulator.gui.visualizer
```

Select a config file, choose the approaches to simulate and set the start date
and window length.

### Parameter optimization
`run_optimization.py` performs a grid search over advanced day trading
parameters and simulation windows.  Adjust the candidate values in the script
and run:

```bash
python run_optimization.py
```

## Repository Layout
- `config/` – sample configuration files.
- `data/` – historical data loader and local CSV cache.
- `gui/` – Tkinter visualizer for running single simulations.
- `optimization/` – utilities for parameter sweeps.
- `simulation/` – core portfolio and execution logic.
- `strategies/` – trading strategy implementations.

## CSV Cache Format
Historical prices downloaded with `yfinance` are stored under
`data/local_csv` in a simple six column layout:

```
Date,Open,High,Low,Close,Volume
```

If you previously ran the simulator with older versions of the code you may
have CSV files with different headers.  You can safely delete the old files to
force fresh downloads or convert them to the new format before running.

## License
This project is provided for educational purposes and comes with no warranty.
