import os
import logging

# Default starting cash for simulations
DEFAULT_CASH = 10000.0

# Directories for cached data and reports
LOCAL_DATA_DIR = os.getenv("SIM_DATA_DIR", "data/local_csv")
GUI_DATA_DIR = os.getenv("SIM_GUI_DATA_DIR", "gui/data/local_csv")
REPORTS_DIR = os.getenv("SIM_REPORTS_DIR", "reports")


def init_logging(level: str | int | None = None) -> None:
    """Configure basic logging.

    Parameters
    ----------
    level:
        Logging level name or integer. If ``None``, the ``SIM_LOG_LEVEL``
        environment variable is checked and defaults to ``INFO``.
    """
    if level is None:
        env_level = os.getenv("SIM_LOG_LEVEL", "INFO")
        try:
            level = int(env_level)
        except ValueError:
            level = getattr(logging, env_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")
