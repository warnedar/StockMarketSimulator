"""Utility for removing stale cached CSV files.

This script checks files under ``data/local_csv`` and ``gui/data/local_csv``.
If a file's header line does not exactly match::

    Date,Open,High,Low,Close,Volume

it will be renamed with a ``.bad`` extension or deleted when ``--delete`` is
supplied.
"""

import argparse
import csv
import os
from typing import Iterable

from config import LOCAL_DATA_DIR, GUI_DATA_DIR

EXPECTED_HEADER = ["Date", "Open", "High", "Low", "Close", "Volume"]


def _process_dir(directory: str, delete: bool) -> None:
    if not os.path.isdir(directory):
        return
    for fname in os.listdir(directory):
        if not fname.endswith(".csv"):
            continue
        path = os.path.join(directory, fname)
        try:
            with open(path, newline="") as f:
                reader = csv.reader(f)
                header = next(reader, [])
        except Exception as e:
            print(f"[ERROR] Could not read {path}: {e}")
            continue

        if header != EXPECTED_HEADER:
            if delete:
                os.remove(path)
                print(f"[DELETE] {path}")
            else:
                new_path = path + ".bad"
                os.rename(path, new_path)
                print(f"[RENAME] {path} -> {new_path}")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Remove or rename cached CSVs with unexpected headers"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete bad files instead of renaming with .bad",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    for directory in (LOCAL_DATA_DIR, GUI_DATA_DIR):
        _process_dir(directory, delete=args.delete)


if __name__ == "__main__":
    main()
