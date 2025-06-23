# stock_market_simulator/data/data_fetcher.py

import os
from datetime import datetime

import pandas as pd
import yfinance as yf
from filelock import FileLock

# Expected column order for all cached CSVs
EXPECTED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]

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

    if not df.empty:
        # Ensure timezone naive index and align to EXPECTED_COLUMNS
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
        df = df.reset_index()
        df = df[[c for c in EXPECTED_COLUMNS if c in df.columns]]
        # Some older versions include "Adj Close"; ignore other columns
        missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
        for c in missing:
            df[c] = pd.NA
        df = df[EXPECTED_COLUMNS]
        df.set_index("Date", inplace=True)

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

    df = pd.DataFrame()

    lock_path = f"{local_csv_path}.lock"
    with FileLock(lock_path):
        # Re-check cache after acquiring the lock in case another thread
        # loaded the data while we were waiting.
        if ticker in _data_cache:
            print(f"[CACHE HIT] {ticker} in-memory (after lock).")
            return _data_cache[ticker]

        if os.path.exists(local_csv_path):
            print(f"[LOCAL CSV] Loading {ticker} from {local_csv_path}")
            header_cols = list(pd.read_csv(local_csv_path, nrows=0).columns)
            if header_cols != EXPECTED_COLUMNS:
                print(f"[WARNING] Unexpected columns in {csv_filename}; redownloading.")
                df = _safe_download(ticker, start_date)
                df.to_csv(local_csv_path, columns=EXPECTED_COLUMNS)
            else:
                df = pd.read_csv(
                    local_csv_path,
                    parse_dates=["Date"],
                    index_col="Date",
                )
                df.index = pd.to_datetime(df.index, errors="coerce")
                df = df[~df.index.isna()]
                df.sort_index(inplace=True)

        if df.empty:
            print(f"[YAHOO] Downloading {ticker} from {start_date}")
            df = _safe_download(ticker, start_date)
            if not df.empty:
                df[EXPECTED_COLUMNS].to_csv(local_csv_path)
        else:
            last_date = df.index[-1]
            new_start_date = (last_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            today_str = datetime.today().strftime("%Y-%m-%d")
            if new_start_date < today_str:
                print(
                    f"[UPDATE] Checking for new data for {ticker} from {new_start_date} to {today_str}"
                )
                new_df = _safe_download(ticker, new_start_date)
                if not new_df.empty:
                    df = pd.concat([df, new_df])
                    df = df[~df.index.duplicated(keep='last')]
                    df.sort_index(inplace=True)
                    df[EXPECTED_COLUMNS].to_csv(local_csv_path)
                    print(f"[UPDATE] CSV for {ticker} updated with new data.")
                else:
                    print(
                        f"[UPDATE] No new data available for {ticker} after {last_date.date()}."
                    )


    if df is None or df.empty:
        raise ValueError(f"No data found for ticker: {ticker}")

    missing_cols = [c for c in EXPECTED_COLUMNS[1:] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns {missing_cols} in DataFrame for {ticker}")

    # Keep only the expected OHLCV columns, drop rows with NaN Close, and sort
    df = df[EXPECTED_COLUMNS[1:]].copy()
    df.dropna(subset=['Close'], inplace=True)
    df.sort_index(inplace=True)

    _data_cache[ticker] = df
    return df
