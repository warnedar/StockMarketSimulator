import os
import sys
from datetime import datetime as dt

import pandas as pd


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data import data_fetcher


def _make_df():
    dates = pd.date_range("2020-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "Open": [1, 2, 3],
            "High": [1, 2, 3],
            "Low": [1, 2, 3],
            "Close": [1, 2, 3],
            "Volume": [100, 200, 300],
        },
        index=dates,
    )
    df.index.name = "Date"
    return df


def test_download_creates_csv(tmp_path, monkeypatch):
    data_fetcher._data_cache.clear()

    df = _make_df()
    calls = []

    def fake_download(ticker, start):
        calls.append((ticker, start))
        return df.copy()

    monkeypatch.setattr(data_fetcher, "_safe_download", fake_download)

    result = data_fetcher.load_historical_data(
        "TEST", start_date="2020-01-01", local_data_dir=str(tmp_path)
    )

    assert len(calls) == 1
    csv_path = tmp_path / "TEST.csv"
    assert csv_path.exists()
    header = list(pd.read_csv(csv_path, nrows=0).columns)
    assert header == data_fetcher.EXPECTED_COLUMNS
    assert list(result.columns) == [c for c in data_fetcher.EXPECTED_COLUMNS if c != "Date"]


def test_uses_local_csv_without_downloading(tmp_path, monkeypatch):
    data_fetcher._data_cache.clear()

    df = _make_df()

    # Initial download to create the CSV
    monkeypatch.setattr(data_fetcher, "_safe_download", lambda t, s: df.copy())
    data_fetcher.load_historical_data(
        "TEST", start_date="2020-01-01", local_data_dir=str(tmp_path)
    )

    # Clear cache to force reading from disk
    data_fetcher._data_cache.clear()

    class DummyDateTime:
        @staticmethod
        def today():
            return dt(2020, 1, 4)

    monkeypatch.setattr(data_fetcher, "datetime", DummyDateTime)

    def fail_download(*args, **kwargs):
        raise AssertionError("_safe_download should not be called")

    monkeypatch.setattr(data_fetcher, "_safe_download", fail_download)

    result = data_fetcher.load_historical_data(
        "TEST", start_date="2020-01-01", local_data_dir=str(tmp_path)
    )

    csv_path = tmp_path / "TEST.csv"
    assert csv_path.exists()
    assert list(result.columns) == [c for c in data_fetcher.EXPECTED_COLUMNS if c != "Date"]
