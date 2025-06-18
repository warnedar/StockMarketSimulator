# stock_market_simulator/main.py

import os
import sys
import shutil
import concurrent.futures
import matplotlib.pyplot as plt
from io import StringIO
from collections import defaultdict

from stock_market_simulator.utils.config_parser import parse_config_file
from stock_market_simulator.data.data_fetcher import load_historical_data
from stock_market_simulator.simulation.simulator import run_configured_sweep


def run_approach(aname, ticker_strat_dict, years, stepsize):
    """Run one simulation approach in a separate process."""
    needed = set(ticker_strat_dict.keys())
    all_dfs = {tk: load_historical_data(tk) for tk in needed}
    return run_configured_sweep(all_dfs, aname, ticker_strat_dict, years, stepsize, 10000.0)

def generate_boxplots(approach_data, output_dir, out_name):
    """
    Generate box-and-whisker plots for each metric across all approaches,
    including the NEW average_annual_return.
    """
    import matplotlib.colors as mcolors

    # Now we have four metrics:
    metrics = {
        'lowest_valley': 'Lowest Valley',
        'highest_peak': 'Highest Peak',
        'final_result': 'Final Result',
        'avg_annual_return': 'Average Annual Return'   # NEW
    }

    colors = list(mcolors.TABLEAU_COLORS.values())

    for metric_key, metric_label in metrics.items():
        data = []
        approaches = []
        approach_colors = {}

        # Gather data for this metric
        for i, (approach_name, (summary, runs_list, _)) in enumerate(approach_data.items()):
            # runs_list => (lv, hv, fr, aar, start_date)
            if metric_key == 'lowest_valley':
                metric_values = [run[0] for run in runs_list]
            elif metric_key == 'highest_peak':
                metric_values = [run[1] for run in runs_list]
            elif metric_key == 'final_result':
                metric_values = [run[2] for run in runs_list]
            elif metric_key == 'avg_annual_return':
                metric_values = [run[3] for run in runs_list]
            else:
                continue

            if metric_values:
                data.append(metric_values)
                approaches.append(approach_name)
                approach_colors[approach_name] = colors[i % len(colors)]

        if not data:
            print(f"No data for metric '{metric_key}'. Skipping plot.")
            continue

        # Determine y-limits
        all_values = [val for sublist in data for val in sublist]
        y_min = min(all_values) * 0.95
        y_max = max(all_values) * 1.05

        # Create the boxplot
        plt.figure(figsize=(10, 6))
        # NOTE: Matplotlib v3.9+ renamed 'labels' to 'tick_labels'
        box = plt.boxplot(data, tick_labels=approaches, patch_artist=True, showfliers=True)

        # Color the boxes
        for patch, approach in zip(box['boxes'], approaches):
            patch.set_facecolor(approach_colors[approach])

        plt.title(f'{metric_label} Across Approaches', fontsize=14)
        plt.xlabel('Approaches', fontsize=12)
        plt.ylabel(metric_label, fontsize=12)
        plt.ylim(y_min, y_max)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        plot_filename = f"{metric_key}_boxplot_{out_name}.png"
        plot_path = os.path.join(output_dir, plot_filename)
        plt.savefig(plot_path)
        plt.close()

        print(f"Saved boxplot for '{metric_key}' to '{plot_path}'.")


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python -m stock_market_simulator.main <config_file> <output_dir_name> [workers]"
        )
        return

    config_path = sys.argv[1]
    out_name = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) >= 4 else (os.cpu_count() or 1)

    base_dir = "reports"
    out_dir = os.path.join(base_dir, out_name)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    buffer = StringIO()

    def myprint(*args, **kwargs):
        print(*args, **kwargs)
        print(*args, file=buffer, **{k:v for k,v in kwargs.items() if k!='file'})

    try:
        years, stepsize, approaches = parse_config_file(config_path)
        approach_data = {}

        max_workers = min(workers, len(approaches)) if approaches else 1
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_map = {executor.submit(run_approach, aname, tdict, years, stepsize): aname for aname, tdict in approaches}
            for fut in concurrent.futures.as_completed(future_map):
                aname = future_map[fut]
                try:
                    summary, runs_list, final_map = fut.result()
                    approach_data[aname] = (summary, runs_list, final_map)
                except Exception as e:
                    myprint(f"Approach {aname} => ERROR: {e}")

        for aname, _ in approaches:
            if aname not in approach_data:
                continue
            summary, runs_list, _ = approach_data[aname]

            myprint(f"=== Approach: {aname} ===")

            lv = summary["lowest_valley"]
            myprint(
                f"lowest_valley => "
                f"min:{lv['min_val']:.2f} (start {lv['min_start_date'].date()}), "
                f"max:{lv['max_val']:.2f} (start {lv['max_start_date'].date()}), "
                f"avg:{lv['avg_val']:.2f}"
            )

            hv = summary["highest_peak"]
            myprint(
                f"highest_peak  => "
                f"min:{hv['min_val']:.2f} (start {hv['min_start_date'].date()}), "
                f"max:{hv['max_val']:.2f} (start {hv['max_start_date'].date()}), "
                f"avg:{hv['avg_val']:.2f}"
            )

            fr = summary["final_result"]
            myprint(
                f"final_result  => "
                f"min:{fr['min_val']:.2f} (start {fr['min_start_date'].date()}), "
                f"max:{fr['max_val']:.2f} (start {fr['max_start_date'].date()}), "
                f"avg:{fr['avg_val']:.2f}"
            )

            aar = summary["avg_annual_return"]
            myprint(
                f"avg_annual_return => "
                f"min:{aar['min_val']:.2f}% (start {aar['min_start_date'].date()}), "
                f"max:{aar['max_val']:.2f}% (start {aar['max_start_date'].date()}), "
                f"avg:{aar['avg_val']:.2f}%\n"
            )

        # If no successful approaches, skip everything else
        if not approach_data:
            myprint("No successful approaches => exit.")
        else:
            # Rank histogram logic (unchanged).
            # Note: You might continue to do rank histogram for final_result only, or skip it for the new metric.
            approach_start_sets = []
            for aname, data_tuple in approach_data.items():
                final_map = data_tuple[2]  # summary, runs_list, final_map
                approach_start_sets.append(set(final_map.keys()))
            common_starts = set.intersection(*approach_start_sets) if approach_start_sets else set()

            if not common_starts:
                myprint("No common starts => skipping rank histogram.")
            else:
                rank_counts = {}
                for aname in approach_data.keys():
                    rank_counts[aname] = defaultdict(int)

                # For each start date in common, rank by final_result (only)
                for sd in common_starts:
                    results = []
                    for aname in approach_data.keys():
                        fm = approach_data[aname][2]
                        val = fm[sd]
                        results.append((aname, val))
                    # Sort descending
                    results.sort(key=lambda x: x[1], reverse=True)
                    for i, (a, _) in enumerate(results):
                        rank_counts[a][i+1] += 1

                import matplotlib.pyplot as plt
                from matplotlib.patches import Patch

                n_approaches = len(approach_data)
                rank_range = range(1, n_approaches + 1)
                bar_data = {r: [rank_counts[ap][r] for ap in approach_data.keys()] for r in rank_range}

                color_map = plt.colormaps['tab10'].resampled(n_approaches)  # Resample the colormap
                approach_colors = {}
                for i, ap in enumerate(approach_data.keys()):
                    approach_colors[ap] = color_map(i)

                fig, ax = plt.subplots(figsize=(8, 5))

                for r in rank_range:
                    y_vals = bar_data[r]
                    bottom = 0
                    for i, ap in enumerate(approach_data.keys()):
                        height = y_vals[i]
                        ax.bar(r, height, bottom=bottom,
                               color=approach_colors[ap], edgecolor='black')
                        bottom += height

                legend_patches = []
                for i, ap in enumerate(approach_data.keys()):
                    patch = Patch(color=approach_colors[ap], label=ap)
                    legend_patches.append(patch)

                ax.legend(handles=legend_patches, bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.set_xticks(list(rank_range))
                ax.set_xlabel("Rank (1=best, N=worst)")
                ax.set_ylabel("Count (# of times approach had this rank)")
                ax.set_title("Rank Histogram Across Common Monthly Starts")
                plt.tight_layout()

                hist_path = os.path.join(out_dir, "histogram.png")
                plt.savefig(hist_path)
                plt.close()

                myprint(f"Histogram saved to {hist_path}")

            # Now generate boxplots (including the new avg_annual_return)
            generate_boxplots(approach_data, out_dir, out_name)

    finally:
        # Save the console buffer to 'report.txt'
        report_path = os.path.join(out_dir, "report.txt")
        with open(report_path, 'w') as outf:
            outf.write(buffer.getvalue())

        # Copy config
        config_copy_path = os.path.join(out_dir, "config.txt")
        shutil.copy(config_path, config_copy_path)

        buffer.close()

if __name__ == "__main__":
    main()
