# stock_market_simulator/__init__.py

"""
Stock Market Simulator Package

This package provides modules for:
- Data fetching (local or Yahoo Finance)
- Portfolio, Orders, and Execution logic
- Multiple strategies (e.g., Buy & Hold, Advanced Day Trading)
- Simulation driver
- Configuration parsing
"""
import os

# Include the optional 'src/stock_market_simulator' path so subpackages located
# under `src/` can be imported using the standard package name.
_src_pkg = os.path.join(os.path.dirname(__file__), "src", "stock_market_simulator")
if os.path.isdir(_src_pkg) and _src_pkg not in __path__:
    __path__.append(_src_pkg)

__version__ = "0.1.0"
