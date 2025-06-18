# stock_market_simulator/batch_runner.py

import subprocess
import sys

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

    for config_file, out_dir in runs:
        print(f"\n=== Running simulation for config '{config_file}' => '{out_dir}' ===")
        cmd = [sys.executable, "-m", "stock_market_simulator.main", config_file, out_dir]
        subprocess.run(cmd, check=True)

    print("\nAll simulations completed successfully.")


if __name__ == "__main__":
    main()
