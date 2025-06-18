# stock_market_simulator/data/data_fetcher.py

import os
import pandas as pd
import yfinance as yf
from datetime import datetime

# In-memory cache to avoid redundant downloads during a single run
_data_cache = {}


def load_historical_data(ticker: str, start_date="1980-01-01", local_data_dir="data/local_csv") -> pd.DataFrame:
    """
    Load historical data for 'ticker' from a local CSV if available;
    otherwise download from Yahoo Finance and store a local copy.

    Additionally, if a CSV exists, this function checks for any new data available
    (after the last date in the CSV) and, if found, appends it to the CSV automatically.

    The function now detects whether the CSV file has a header row or not and adapts accordingly.
    If the loaded CSV is empty, it will re-download data from Yahoo Finance.
    """
    global _data_cache
    if ticker in _data_cache:
        print(f"[CACHE HIT] {ticker} in-memory.")
        return _data_cache[ticker]

    # Ensure the local data directory exists
    if not os.path.exists(local_data_dir):
        os.makedirs(local_data_dir)

    safe_ticker = ticker.replace('^', '_')
    csv_filename = f"{safe_ticker}.csv"
    local_csv_path = os.path.join(local_data_dir, csv_filename)

    df = None

    if os.path.exists(local_csv_path):
        print(f"[LOCAL CSV] Loading {ticker} from {local_csv_path}")
        # Open the file and check the first line.
        with open(local_csv_path, 'r') as f:
            first_line = f.readline()

        # If the first line contains "Date", assume the CSV has a header.
        if "Date" in first_line:
            df = pd.read_csv(
                local_csv_path,
                parse_dates=["Date"],
                index_col="Date"
            )
        else:
            # Otherwise, use the old method (skip first 3 rows, no header in the remaining data).
            df = pd.read_csv(
                local_csv_path,
                skiprows=3,
                header=None,
                names=["Date", "Close", "High", "Low", "Open", "Volume"],
                parse_dates=["Date"],
                index_col="Date"
            )
        df.dropna(inplace=True)
        df.sort_index(inplace=True)

        # If CSV is empty, re-download data.
        if df.empty:
            print(f"[WARNING] CSV for {ticker} is empty. Downloading fresh data from Yahoo Finance.")
            df = yf.download(ticker, start=start_date, progress=False)
            if not df.empty:
                df.to_csv(local_csv_path)
                df = df[['Close']].copy()
                df.dropna(inplace=True)
                df.sort_index(inplace=True)

        # If not empty, check for new data.
        if not df.empty:
            last_date = df.index[-1]
            new_start_date = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            today_str = datetime.today().strftime('%Y-%m-%d')
            if new_start_date < today_str:
                print(f"[UPDATE] Checking for new data for {ticker} from {new_start_date} to {today_str}")
                new_df = yf.download(ticker, start=new_start_date, progress=False)
                if not new_df.empty:
                    new_df = new_df[['Close']].copy()
                    new_df.dropna(inplace=True)
                    new_df.sort_index(inplace=True)
                    df = pd.concat([df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                    df.sort_index(inplace=True)
                    df.to_csv(local_csv_path)
                    print(f"[UPDATE] CSV for {ticker} updated with new data.")
                else:
                    print(f"[UPDATE] No new data available for {ticker} after {last_date.date()}.")
    else:
        print(f"[YAHOO] Downloading {ticker} from {start_date}")
        df = yf.download(ticker, start=start_date, progress=False)
        if not df.empty:
            df.to_csv(local_csv_path)

    if df is None or df.empty:
        raise ValueError(f"No data found for ticker: {ticker}")

    if 'Close' not in df.columns:
        raise ValueError(f"Missing 'Close' in DataFrame for {ticker}")

    # Keep only 'Close', drop NaNs, and sort the DataFrame by date
    df = df[['Close']].copy()
    df.dropna(inplace=True)
    df.sort_index(inplace=True)

    _data_cache[ticker] = df
    return df
