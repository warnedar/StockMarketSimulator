"""Utilities for summarising optimisation results as a PDF report.

The optimisation sweep produces a nested dictionary of metrics.  This module
turns that data into a human-readable multi-page PDF containing text summaries,
box plots and heatmaps.  ``matplotlib`` is used for rendering and the built-in
``PdfPages`` backend writes the final file.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def _plot_heatmap(pivot_df, title, pdf):
    fig, ax = plt.subplots()
    im = ax.imshow(pivot_df.values, cmap="viridis", aspect="auto", origin="lower")
    ax.set_xticks(range(len(pivot_df.columns)))
    ax.set_xticklabels(pivot_df.columns)
    ax.set_yticks(range(len(pivot_df.index)))
    ax.set_yticklabels(pivot_df.index)
    for i in range(pivot_df.shape[0]):
        for j in range(pivot_df.shape[1]):
            val = pivot_df.values[i, j]
            if pd.notna(val):
                ax.text(j, i, f"{val:.1f}", ha="center", va="center", color="w", fontsize=6)
    ax.set_xlabel("Limit Discount %")
    ax.set_ylabel("Trailing Stop %")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label="Metric")
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


def create_pdf_report(best_by_year, output_dir):
    """Create a PDF summary report for optimization results."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "optimization_summary.pdf")
    with PdfPages(pdf_path) as pdf:
        for years_val, (best_params, best_avg, group_dict) in sorted(best_by_year.items()):
            # Text summary page
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.axis("off")
            text = (
                f"Window: {years_val} years\n"
                f"Best Parameters: TS={best_params[0]}%, "
                f"LD={best_params[1]}%, PLD={best_params[2]}\n"
                f"Average Metric: {best_avg:.2f}%"
            )
            ax.text(0.05, 0.5, text, fontsize=12, va="center")
            pdf.savefig(fig)
            plt.close(fig)

            # Boxplot of all metrics for this year window
            metrics = list(group_dict.values())
            fig, ax = plt.subplots()
            ax.boxplot(metrics)
            ax.set_title(f"Metric Distribution - {years_val}y")
            ax.set_ylabel("Metric")
            pdf.savefig(fig)
            plt.close(fig)

            # Heatmaps per pending_limit_days
            df = pd.DataFrame([
                (ts, lb, pl, metric)
                for (ts, lb, pl), metric in group_dict.items()
            ], columns=["TS", "LD", "PL", "Metric"])
            for pl_val in sorted(df["PL"].unique()):
                pivot = df[df["PL"] == pl_val].pivot(index="TS", columns="LD", values="Metric")
                pivot = pivot.sort_index().sort_index(axis=1)
                _plot_heatmap(pivot, f"{years_val}y - Pending {pl_val} days", pdf)

    print(f"PDF report saved to {pdf_path}")
    return pdf_path
