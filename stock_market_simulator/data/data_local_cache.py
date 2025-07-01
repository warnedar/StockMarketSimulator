# stock_market_simulator/data/data_local_cache.py

"""
Optional module for more advanced local caching mechanisms.

Currently, it's just a placeholder to illustrate how you'd expand
caching beyond a simple in-memory dict. For example, you could
serialize DataFrames to a local SQLite DB or keep them in
a more robust cache solution.
"""

# Example placeholders:
_LOCAL_CACHE = {}

def get_cached_data(ticker: str):
    """
    Retrieve a DataFrame from local cache if it exists.
    """
    # In a real scenario, you'd do disk-based or DB lookups here.
    return _LOCAL_CACHE.get(ticker, None)

def store_cached_data(ticker: str, df):
    """
    Store a DataFrame to local cache, possibly writing to disk or DB.
    """
    _LOCAL_CACHE[ticker] = df
