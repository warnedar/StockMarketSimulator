# stock_market_simulator/batch_runner.py

import subprocess
import sys
import os
import concurrent.futures

def main():
    """
    This script calls 'stock_market_simulator/main.py' multiple times,
    each time with:
      1) A config file path
      2) An output directory name
    so that all results go to 'reports/<output_dir_name>/...'
    """
    name_postfix = "02132025"
    name_prefix = "Strategy_Sweep_8"

    runs = [
        # ("config/configA.txt", f"{name_prefix}_5years_{name_postfix}"),
        # ("config/configB.txt", f"{name_prefix}_10years_{name_postfix}"),
        # ("config/configC.txt", f"{name_prefix}_15years_{name_postfix}"),
        ("config/configD.txt", f"{name_prefix}_20years_{name_postfix}")
        # Add more configs here if desired
    ]

    max_workers = int(sys.argv[1]) if len(sys.argv) >= 2 else (os.cpu_count() or 1)
    per_job = max(1, max_workers // len(runs))

    def run_pair(cfg, out):
        print(f"\n=== Running simulation for config '{cfg}' => '{out}' ===")
        cmd = [sys.executable, "-m", "stock_market_simulator.main", cfg, out, str(per_job)]
        subprocess.run(cmd, check=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(runs)) as executor:
        futures = [executor.submit(run_pair, c, o) for c, o in runs]
        for fut in concurrent.futures.as_completed(futures):
            fut.result()

    print("\nAll simulations completed successfully.")


if __name__ == "__main__":
    main()
