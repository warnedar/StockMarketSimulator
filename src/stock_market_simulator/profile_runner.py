# profile_runner.py

import cProfile
import pstats
from stock_market_simulator.batch_runner import main  # <-- Import the 'main' function from your batch_runner

def run_batch_with_profiling():
    """
    Wraps the batch_runner main() call with cProfile, generating 'batch_output.prof'.
    """
    profiler = cProfile.Profile()
    profiler.enable()

    # Run all the batches
    main()

    profiler.disable()

    # Sort results by total time (descending) and dump them to a file
    stats = pstats.Stats(profiler).sort_stats(pstats.SortKey.TIME)
    stats.dump_stats("batch_output.prof")
    # Optionally print top 20 lines to console
    stats.print_stats(20)

if __name__ == "__main__":
    run_batch_with_profiling()
