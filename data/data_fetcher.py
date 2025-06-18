# stock_market_simulator/data/data_fetcher.py

import os
from datetime import datetime

import pandas as pd
import yfinance as yf
from filelock import FileLock

# In-memory cache to avoid redundant downloads during a single run
_data_cache = {}


def _safe_download(ticker: str, start: str) -> pd.DataFrame:
    """Attempt to download price data with a fallback."""
    try:
        df = yf.download(
            ticker,
            start=start,
            progress=False,
            show_errors=False,
            auto_adjust=False,
        )
    except TypeError as te:
        # Older versions of yfinance do not support the show_errors argument
        if "show_errors" in str(te):
            try:
                df = yf.download(
                    ticker,
                    start=start,
                    progress=False,
                    auto_adjust=False,
                )
            except Exception as e:
                print(f"[WARNING] yf.download failed for {ticker}: {e}")
                df = pd.DataFrame()
        else:
            print(f"[WARNING] yf.download failed for {ticker}: {te}")
            df = pd.DataFrame()
    except Exception as e:
        print(f"[WARNING] yf.download failed for {ticker}: {e}")
        df = pd.DataFrame()

    if df.empty:
        try:
            df = yf.Ticker(ticker).history(start=start, auto_adjust=False)
        except Exception as e:
            print(f"[ERROR] history() failed for {ticker}: {e}")
            df = pd.DataFrame()

    # Ensure the index is timezone naive to avoid comparisons between
    # tz-aware and tz-naive timestamps when concatenating with CSV data.
    if not df.empty and getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_localize(None)

    return df


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

    lock_path = f"{local_csv_path}.lock"
    with FileLock(lock_path):
        # Re-check cache after acquiring the lock in case another thread
        # loaded the data while we were waiting.
        if ticker in _data_cache:
            print(f"[CACHE HIT] {ticker} in-memory (after lock).")
            return _data_cache[ticker]
        if os.path.exists(local_csv_path):
            print(f"[LOCAL CSV] Loading {ticker} from {local_csv_path}")
            # Inspect the first line so we can determine how to read the file.
            with open(local_csv_path, 'r') as f:
                first_line = f.readline().strip()

            if "Date" in first_line:
                # Standard CSV with a header row
                df = pd.read_csv(
                    local_csv_path,
                    parse_dates=["Date"],
                    index_col="Date",
                )
            elif first_line.startswith("Price"):
                # Custom exported format. The first three lines contain
                # column labels like "Price"/"Ticker"/"Date". Determine how
                # many actual columns are present so we can construct the
                # appropriate list of names.
                column_count = len(first_line.split(','))
                if column_count >= 6:
                    names = ["Date", "Close", "High", "Low", "Open", "Volume"]
                else:
                    # Some files only contain a date and closing price
                    names = ["Date", "Close"]
                df = pd.read_csv(
                    local_csv_path,
                    skiprows=3,
                    header=None,
                    names=names,
                    usecols=range(len(names)),
                    parse_dates=["Date"],
                    index_col="Date",
                )
            else:
                # Fallback to the old behaviour of skipping three rows
                df = pd.read_csv(
                    local_csv_path,
                    skiprows=3,
                    header=None,
                    names=["Date", "Close", "High", "Low", "Open", "Volume"],
                    parse_dates=["Date"],
                    index_col="Date",
                )

            # Ensure index from CSV is timezone naive and of datetime type
            if getattr(df.index, "tz", None) is not None:
                df.index = df.index.tz_localize(None)

            # Coerce the index to datetimes to avoid string concatenation issues
            df.index = pd.to_datetime(df.index, errors="coerce")
            df = df[~df.index.isna()]

            df.dropna(subset=["Close"], inplace=True)
            df.sort_index(inplace=True)

            # If CSV is empty, re-download data.
            if df.empty:
                print(f"[WARNING] CSV for {ticker} is empty. Downloading fresh data from Yahoo Finance.")
                df = _safe_download(ticker, start_date)
                if not df.empty:
                    df.to_csv(local_csv_path)
                    df = df[["Close"]].copy()
                    df.dropna(inplace=True)
                    df.sort_index(inplace=True)

            # If not empty, check for new data.
            if not df.empty:
                last_date = pd.to_datetime(df.index[-1], errors="coerce")
                if pd.isna(last_date):
                    print(f"[WARNING] Last date for {ticker} is invalid; skipping update check.")
                    new_start_date = None
                else:
                    new_start_date = (last_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
                today_str = datetime.today().strftime("%Y-%m-%d")
                if new_start_date and new_start_date < today_str:
                    print(f"[UPDATE] Checking for new data for {ticker} from {new_start_date} to {today_str}")
                    new_df = _safe_download(ticker, new_start_date)
                    if not new_df.empty:
                        new_df = new_df[["Close"]].copy()
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
            df = _safe_download(ticker, start_date)
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
