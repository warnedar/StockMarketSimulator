"""Helper script for profiling batch runs.

``cProfile`` can be cumbersome to invoke with complex command lines.  This
module wraps :func:`batch_runner.main` with a small amount of glue that captures
and stores profiling data in ``batch_output.prof``.  The resulting profile can
later be inspected with :mod:`pstats` or visual tools such as ``snakeviz``.
"""

import cProfile
import pstats

from stock_market_simulator.batch_runner import main  # Import the batch runner we want to profile


def run_batch_with_profiling():
    """Execute all batch runs while collecting CPU profiling data."""

    profiler = cProfile.Profile()
    profiler.enable()

    # Delegate to the regular batch runner.  Any output it prints will still
    # appear on the console, making the profiling wrapper transparent to users.
    main()

    profiler.disable()

    # Sort results by total time (descending) and dump them to a file so they
    # can be inspected after the program exits.
    stats = pstats.Stats(profiler).sort_stats(pstats.SortKey.TIME)
    stats.dump_stats("batch_output.prof")
    # Optionally print top 20 lines to console for a quick glance.
    stats.print_stats(20)


if __name__ == "__main__":
    run_batch_with_profiling()
