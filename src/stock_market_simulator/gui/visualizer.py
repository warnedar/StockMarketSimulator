# stock_market_simulator/gui/visualizer.py

import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import os

from stock_market_simulator.utils.config_parser import parse_config_file
from stock_market_simulator.data.data_fetcher import load_historical_data
from stock_market_simulator.gui.simulation_runner import run_simulation


class SimulatorVisualizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Strategy Sweep Visualizer")
        self.geometry("900x700")

        self.config_file_path = None
        self.config_data = None  # (years, stepsize, approaches)
        self.dfs_cache = {}  # Cache: ticker -> DataFrame

        self.create_widgets()

    def create_widgets(self):
        # Top frame: Config file selection and approach list.
        frame_top = tk.Frame(self)
        frame_top.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        btn_load = tk.Button(frame_top, text="Load Config File", command=self.load_config)
        btn_load.pack(side=tk.LEFT)

        self.lbl_config = tk.Label(frame_top, text="No config file loaded.")
        self.lbl_config.pack(side=tk.LEFT, padx=10)

        # Frame for approaches list.
        frame_approaches = tk.Frame(self)
        frame_approaches.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Label(frame_approaches, text="Select Approaches:").pack(anchor=tk.W)
        self.lst_approaches = tk.Listbox(frame_approaches, selectmode=tk.MULTIPLE, height=6)
        self.lst_approaches.pack(fill=tk.BOTH, expand=True)

        # Frame for simulation parameters.
        frame_params = tk.Frame(self)
        frame_params.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        tk.Label(frame_params, text="Start Date (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W)
        self.entry_start_date = tk.Entry(frame_params)
        self.entry_start_date.grid(row=0, column=1, padx=5)

        tk.Label(frame_params, text="Window (years):").grid(row=1, column=0, sticky=tk.W)
        self.entry_years = tk.Entry(frame_params)
        self.entry_years.grid(row=1, column=1, padx=5)

        tk.Label(frame_params, text="Initial Cash:").grid(row=2, column=0, sticky=tk.W)
        self.entry_cash = tk.Entry(frame_params)
        self.entry_cash.grid(row=2, column=1, padx=5)
        self.entry_cash.insert(0, "10000")

        btn_run = tk.Button(frame_params, text="Run Simulation", command=self.run_simulation)
        btn_run.grid(row=3, column=0, columnspan=2, pady=10)

        # Matplotlib figure embedded in the GUI.
        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def load_config(self):
        file_path = filedialog.askopenfilename(title="Select Config File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.config_file_path = file_path
            try:
                self.config_data = parse_config_file(file_path)
                self.lbl_config.config(text=f"Loaded config: {os.path.basename(file_path)}")
                # Populate approaches listbox.
                self.lst_approaches.delete(0, tk.END)
                _, _, approaches = self.config_data
                for approach_name, ticker_info in approaches:
                    self.lst_approaches.insert(tk.END, approach_name)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {e}")

    def load_data_for_ticker(self, ticker):
        if ticker not in self.dfs_cache:
            try:
                df = load_historical_data(ticker)
                self.dfs_cache[ticker] = df
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load data for {ticker}: {e}")
                return None
        return self.dfs_cache[ticker]

    def run_simulation(self):
        if not self.config_data:
            messagebox.showwarning("Warning", "Please load a config file first.")
            return

        start_date = self.entry_start_date.get().strip()
        window_years_str = self.entry_years.get().strip()
        initial_cash_str = self.entry_cash.get().strip()

        if not start_date or not window_years_str or not initial_cash_str:
            messagebox.showwarning("Warning", "Please fill in all simulation parameters.")
            return

        try:
            window_years = float(window_years_str)
            initial_cash = float(initial_cash_str)
        except ValueError:
            messagebox.showwarning("Warning", "Invalid numerical input for window years or initial cash.")
            return

        selected_indices = self.lst_approaches.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one approach.")
            return

        _, _, approaches = self.config_data
        self.ax.clear()

        for idx in selected_indices:
            approach_name, ticker_info_dict = approaches[idx]
            # Load historical data for each ticker in this approach.
            dfs_dict = {}
            for ticker in ticker_info_dict:
                df = self.load_data_for_ticker(ticker)
                if df is not None:
                    dfs_dict[ticker] = df
            if not dfs_dict:
                continue
            try:
                history, final_index = run_simulation(ticker_info_dict, dfs_dict, start_date, window_years,
                                                      initial_cash)
                self.ax.plot(final_index, history, label=approach_name)
            except Exception as e:
                messagebox.showerror("Simulation Error", f"Approach {approach_name} failed: {e}")

        self.ax.set_title(f"Simulation Starting at {start_date}")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Total Return (%)")
        self.ax.legend()
        self.fig.autofmt_xdate()
        self.canvas.draw()


if __name__ == "__main__":
    app = SimulatorVisualizer()
    app.mainloop()
