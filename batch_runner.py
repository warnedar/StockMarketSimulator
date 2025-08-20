"""Utility to run multiple simulation sweeps in parallel processes.

The repository's :mod:`main` module performs a "sweep" of simulations for a
single configuration.  During experimentation it is convenient to launch the
same sweep for several config files.  ``batch_runner`` acts as that thin layer
– it spawns a new Python process for each config/output directory pair while
sharing the available CPU cores between them.

This file demonstrates a number of design choices that might not be obvious at
first glance:

* **Thread pool instead of process pool** – Each job already launches a new
  Python interpreter via :func:`subprocess.run`.  Using a thread pool here keeps
  the orchestration lightweight; the heavy lifting happens in the child
  processes.
* **Per-job worker count** – The simulator itself can run in parallel.  To
  prevent oversubscribing the machine ``batch_runner`` divides the requested
  worker count between all pending runs.
* **Config list** – The ``runs`` list below is intentionally simple so users
  can edit or extend it without touching the surrounding logic.
"""

import subprocess
import sys
import os
import concurrent.futures


def main():
    """Entry point that dispatches each configured run.

    The function iterates over ``runs`` and launches ``stock_market_simulator``'s
    :mod:`main` module with the appropriate arguments.  The results for each
    run are written to ``reports/<output_dir_name>``.
    """

    # These name fragments make it easy to group output folders by experiment.
    name_postfix = "07032025"
    name_prefix = "Strategy_QQQ_2"

    # Each tuple is (config file, output directory name).  Commented entries
    # illustrate how additional sweeps could be added.
    runs = [
        ("config/configQQQ.txt", f"{name_prefix}_5years_{name_postfix}"),
        # ("config/configB.txt", f"{name_prefix}_10years_{name_postfix}"),
        # ("config/configC.txt", f"{name_prefix}_15years_{name_postfix}"),
        # ("config/configD.txt", f"{name_prefix}_20years_{name_postfix}")
    ]

    # Optional command line argument indicates how many worker processes in
    # total are available for all runs.  Each job will get an even slice of
    # these workers.
    if len(sys.argv) >= 2:
        try:
            max_workers = int(sys.argv[1])
        except ValueError:
            print(
                f"Warning: expected integer worker count, got '{sys.argv[1]}'."
                " Using available CPU count."
            )
            max_workers = os.cpu_count() or 1
    else:
        max_workers = os.cpu_count() or 1

    # Avoid allocating zero workers per job (which would make the simulator
    # single-threaded even on capable machines).
    per_job = max(1, max_workers // len(runs))

    def run_pair(cfg, out):
        """Launch a single sweep in a new Python process."""

        print(f"\n=== Running simulation for config '{cfg}' => '{out}' ===")
        cmd = [sys.executable, "-m", "stock_market_simulator.main", cfg, out, str(per_job)]
        subprocess.run(cmd, check=True)

    # Kick off all runs concurrently.  Each task merely spawns another process
    # so threads are sufficient and keep memory usage low.
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(runs)) as executor:
        futures = [executor.submit(run_pair, c, o) for c, o in runs]
        for fut in concurrent.futures.as_completed(futures):
            # ``result()`` will re-raise any exception from ``run_pair``.
            fut.result()

    print("\nAll simulations completed successfully.")


if __name__ == "__main__":
    main()
