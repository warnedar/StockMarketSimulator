import os
import sys
import csv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.cleanup_cache import _process_dir, EXPECTED_HEADER


def _write_csv(path, header):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerow([1] * len(header))


def test_process_dir_renames_bad_files(tmp_path):
    target = tmp_path / "rename"
    target.mkdir()
    good = target / "good.csv"
    bad = target / "bad.csv"

    _write_csv(good, EXPECTED_HEADER)
    _write_csv(bad, ["Bad", "Header"])

    _process_dir(str(target), delete=False)

    assert good.exists()
    assert not bad.exists()
    assert (target / "bad.csv.bad").exists()


def test_process_dir_deletes_bad_files(tmp_path):
    target = tmp_path / "delete"
    target.mkdir()
    good = target / "good.csv"
    bad = target / "bad.csv"

    _write_csv(good, EXPECTED_HEADER)
    _write_csv(bad, ["Bad", "Header"])

    _process_dir(str(target), delete=True)

    assert good.exists()
    assert not bad.exists()
    assert not (target / "bad.csv.bad").exists()
