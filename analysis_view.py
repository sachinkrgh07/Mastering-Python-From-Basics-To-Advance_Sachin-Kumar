import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import math
import calendar
import os
import sys
import subprocess


class AnalysisPage(tk.Frame):
    def __init__(self, parent, controller, db_manager):
        super().__init__(parent)
        self.controller = controller
        self.db = db_manager
        self.configure(bg="#f5f7fb")

        self.range_var = tk.StringVar(value="This Year")
        self.chart_mode_var = tk.StringVar(value="IN vs OUT (Line)")
        self.agg_var = tk.StringVar(value="Monthly")

        self.metric_labels = {}
        self.daily_rows = []
        self.weekly_rows = []
        self.monthly_rows = []

        self.setup_ui()
        self.load_analysis()

        self.bind_all_keys()
        self.bind("<Destroy>", self.cleanup_shortcuts)

    def bind_all_keys(self):
        self.controller.bind("<Control-r>", self.refresh_analysis)
        self.controller.bind("<Control-f>", self.focus_period)

    def cleanup_shortcuts(self, event):
        if event.widget == self:
            try:
                self.controller.unbind("<Control-r>")
                self.controller.unbind("<Control-f>")
            except:
                pass

    def refresh_analysis(self, event=None):
        self.load_analysis()

    def focus_period(self, event=None):
        try:
            self.cmb_range.focus_set()
        except:
            pass

    def run_project_eda(self):
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "project_analytics_pipeline.py")
        if not os.path.exists(script_path):
            messagebox.showerror("Pipeline Missing", "project_analytics_pipeline.py not found in dmd_fixed folder.")
            return

        source_path = getattr(self.db, "db_path", "")
        if not source_path or not os.path.exists(source_path):
            messagebox.showerror("Database Missing", "Active database path not found.")
            return

        try:
            cmd = [sys.executable, script_path, "--source", source_path]
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            subprocess.Popen(cmd, cwd=os.path.dirname(script_path), creationflags=creation_flags)
            messagebox.showinfo(
                "Pipeline Started",
                "Project EDA pipeline started in background.\nOutputs will be created inside eda_outputs folder.",
            )
        except Exception as exc:
            messagebox.showerror("Launch Failed", f"Could not start pipeline:\n{exc}")

    def setup_ui(self):
        header = tk.Frame(self, bg="#1f2937", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Button(
            header,
            text="< Menu (Esc)",
            bg="#1d4ed8",
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self.controller.show_main_menu,
        ).pack(side="left", padx=10, pady=10)

        tk.Label(
            header,
            text="ACCOUNTS ANALYSIS",
            bg="#1f2937",
            fg="white",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=10)

        tk.Button(
            header,
            text="Refresh [Ctrl+R]",
            bg="#16a34a",
            fg="white",
            relief="flat",
            padx=12,
            pady=6,
            command=self.load_analysis,
        ).pack(side="right", padx=14, pady=10)

        filter_bar = tk.Frame(self, bg="#e2e8f0", padx=12, pady=8)
        filter_bar.pack(fill="x")

        tk.Label(filter_bar, text="Period:", bg="#e2e8f0", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.cmb_range = ttk.Combobox(
            filter_bar,
            textvariable=self.range_var,
            values=["This Month", "Last 90 Days", "This Year", "All Time"],
            state="readonly",
            width=16,
            font=("Segoe UI", 10),
        )
        self.cmb_range.pack(side="left", padx=8)
        self.cmb_range.bind("<<ComboboxSelected>>", lambda e: self.load_analysis())

        tk.Label(filter_bar, text="Graph:", bg="#e2e8f0", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(12, 0))
        self.cmb_chart = ttk.Combobox(
            filter_bar,
            textvariable=self.chart_mode_var,
            values=[
                "IN vs OUT (Line)",
                "IN vs OUT (Bar)",
                "Net Cash (Line)",
                "Cumulative Net (Area)",
                "Pending vs Cleared (Bar)",
            ],
            state="readonly",
            width=22,
            font=("Segoe UI", 10),
        )
        self.cmb_chart.pack(side="left", padx=8)
        self.cmb_chart.bind("<<ComboboxSelected>>", lambda e: self.draw_active_chart())

        tk.Label(filter_bar, text="Aggregation:", bg="#e2e8f0", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(12, 0))
        self.cmb_agg = ttk.Combobox(
            filter_bar,
            textvariable=self.agg_var,
            values=["Daily", "Weekly", "Monthly"],
            state="readonly",
            width=12,
            font=("Segoe UI", 10),
        )
        self.cmb_agg.pack(side="left", padx=8)
        self.cmb_agg.bind("<<ComboboxSelected>>", lambda e: self.load_cashflow_table())

        tk.Button(
            filter_bar,
            text="Run Project EDA",
            bg="#7c3aed",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            command=self.run_project_eda,
        ).pack(side="left", padx=(12, 0))

        tk.Label(
            filter_bar,
            text="Ctrl+R refresh  |  Ctrl+F focus period",
            bg="#e2e8f0",
            fg="#475569",
            font=("Segoe UI", 9),
        ).pack(side="right")

        cards = tk.Frame(self, bg="#f5f7fb")
        cards.pack(fill="x", padx=12, pady=(10, 6))

        metrics = [
            ("Total Bills", "total_bills", "#111827"),
            ("Sales (IN)", "sales_in", "#166534"),
            ("Purchase (OUT)", "purchase_out", "#b91c1c"),
            ("Net Cash", "net_cash", "#0f766e"),
            ("Opening Bal", "opening_bal", "#1d4ed8"),
            ("Closing Bal", "closing_bal", "#7c3aed"),
            ("Collection %", "collection_pct", "#2563eb"),
            ("Pending %", "pending_pct", "#92400e"),
        ]

        for idx, (title, key, color) in enumerate(metrics):
            card = tk.Frame(cards, bg="white", bd=1, relief="solid")
            card.grid(row=0, column=idx, padx=4, pady=4, sticky="nsew")
            cards.grid_columnconfigure(idx, weight=1)

            tk.Label(card, text=title, bg="white", fg="#475569", font=("Segoe UI", 9, "bold")).pack(padx=10, pady=(8, 2), anchor="w")
            lbl = tk.Label(card, text="-", bg="white", fg=color, font=("Segoe UI", 11, "bold"))
            lbl.pack(padx=10, pady=(0, 10), anchor="w")
            self.metric_labels[key] = lbl

        body = tk.Frame(self, bg="#f5f7fb")
        body.pack(fill="both", expand=True, padx=12, pady=(2, 10))

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True)

        self.tab_cashflow = tk.Frame(notebook, bg="#f5f7fb")
        self.tab_trends = tk.Frame(notebook, bg="#f5f7fb")
        self.tab_breakdown = tk.Frame(notebook, bg="#f5f7fb")
        self.tab_advanced = tk.Frame(notebook, bg="#f5f7fb")
        self.tab_regression = tk.Frame(notebook, bg="#f5f7fb")

        notebook.add(self.tab_cashflow, text="Cash Flow")
        notebook.add(self.tab_trends, text="Trends")
        notebook.add(self.tab_breakdown, text="Breakdown")
        notebook.add(self.tab_advanced, text="Advanced")
        notebook.add(self.tab_regression, text="Regression")

        self.setup_cashflow_tab()
        self.setup_trends_tab()
        self.setup_breakdown_tab()
        self.setup_advanced_tab()
        self.setup_regression_tab()

    def setup_regression_tab(self):
        container = tk.Frame(self.tab_regression, bg="#f5f7fb")
        container.pack(fill="both", expand=True, padx=8, pady=8)
        container.grid_columnconfigure(0, weight=2)
        container.grid_columnconfigure(1, weight=3)
        container.grid_rowconfigure(0, weight=1)

        summary = tk.Frame(container, bg="white", bd=1, relief="solid")
        summary.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        tk.Label(summary, text="Regression Analysis (Monthly Net)", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_regression = tk.Text(summary, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_regression.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_regression.config(state="disabled")

        chart = tk.Frame(container, bg="white", bd=1, relief="solid")
        chart.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        tk.Label(chart, text="Actual vs Regression Fit + Forecast", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.regression_canvas = tk.Canvas(chart, bg="white", highlightthickness=0)
        self.regression_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.regression_canvas.bind("<Configure>", lambda e: self.load_regression_analysis())

    def setup_cashflow_tab(self):
        top = tk.Frame(self.tab_cashflow, bg="#f5f7fb")
        top.pack(fill="both", expand=True, padx=8, pady=8)
        top.grid_columnconfigure(0, weight=3)
        top.grid_columnconfigure(1, weight=2)
        top.grid_rowconfigure(0, weight=1)

        chart_card = tk.Frame(top, bg="white", bd=1, relief="solid")
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        tk.Label(chart_card, text="Cash Flow Graph", bg="white", fg="#111827", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

        self.chart_canvas = tk.Canvas(chart_card, bg="white", highlightthickness=0)
        self.chart_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.chart_canvas.bind("<Configure>", lambda e: self.draw_active_chart())

        summary_card = tk.Frame(top, bg="white", bd=1, relief="solid")
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        tk.Label(summary_card, text="Cash Flow Summary", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_cashflow_summary = tk.Text(summary_card, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_cashflow_summary.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_cashflow_summary.config(state="disabled")

        bottom = tk.Frame(self.tab_cashflow, bg="white", bd=1, relief="solid")
        bottom.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tk.Label(bottom, text="Aggregated Cash Flow Table", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))

        table_frame = tk.Frame(bottom, bg="white")
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("Period", "IN", "OUT", "Net")
        self.cashflow_tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c in cols:
            self.cashflow_tree.heading(c, text=c)

        self.cashflow_tree.column("Period", width=130, anchor="center")
        self.cashflow_tree.column("IN", width=140, anchor="e")
        self.cashflow_tree.column("OUT", width=140, anchor="e")
        self.cashflow_tree.column("Net", width=140, anchor="e")

        vs = ttk.Scrollbar(table_frame, orient="vertical", command=self.cashflow_tree.yview)
        self.cashflow_tree.configure(yscrollcommand=vs.set)

        self.cashflow_tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

    def setup_trends_tab(self):
        container = tk.Frame(self.tab_trends, bg="#f5f7fb")
        container.pack(fill="both", expand=True, padx=8, pady=8)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        trend_card = tk.Frame(container, bg="white", bd=1, relief="solid")
        trend_card.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        tk.Label(trend_card, text="Trend Analysis", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_trend_analysis = tk.Text(trend_card, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_trend_analysis.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_trend_analysis.config(state="disabled")

        mom_card = tk.Frame(container, bg="white", bd=1, relief="solid")
        mom_card.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        tk.Label(mom_card, text="Month-over-Month", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_mom = tk.Text(mom_card, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_mom.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_mom.config(state="disabled")

    def setup_breakdown_tab(self):
        container = tk.Frame(self.tab_breakdown, bg="#f5f7fb")
        container.pack(fill="both", expand=True, padx=8, pady=8)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        top_tx = tk.Frame(container, bg="white", bd=1, relief="solid")
        top_tx.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=(0, 4))
        tk.Label(top_tx, text="Top Transactions by Value", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_top_tx = tk.Text(top_tx, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_top_tx.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_top_tx.config(state="disabled")

        day_moves = tk.Frame(container, bg="white", bd=1, relief="solid")
        day_moves.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=(0, 4))
        tk.Label(day_moves, text="Largest Single-Day Cash Moves", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_day_moves = tk.Text(day_moves, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_day_moves.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_day_moves.config(state="disabled")

        freq = tk.Frame(container, bg="white", bd=1, relief="solid")
        freq.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        tk.Label(freq, text="Frequency Distribution of Transaction Sizes", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_freq = tk.Text(freq, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_freq.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_freq.config(state="disabled")

    def setup_advanced_tab(self):
        container = tk.Frame(self.tab_advanced, bg="#f5f7fb")
        container.pack(fill="both", expand=True, padx=8, pady=8)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        burn = tk.Frame(container, bg="white", bd=1, relief="solid")
        burn.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=(0, 4))
        tk.Label(burn, text="Burn Rate + Runway", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_burn = tk.Text(burn, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_burn.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_burn.config(state="disabled")

        anomaly = tk.Frame(container, bg="white", bd=1, relief="solid")
        anomaly.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=(0, 4))
        tk.Label(anomaly, text="Anomaly Detection (>2σ)", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_anomaly = tk.Text(anomaly, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_anomaly.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_anomaly.config(state="disabled")

        compare = tk.Frame(container, bg="white", bd=1, relief="solid")
        compare.grid(row=1, column=0, sticky="nsew", padx=(0, 4), pady=(4, 0))
        tk.Label(compare, text="Period Comparison + Forecast", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_compare_forecast = tk.Text(compare, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_compare_forecast.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_compare_forecast.config(state="disabled")

        liquidity = tk.Frame(container, bg="white", bd=1, relief="solid")
        liquidity.grid(row=1, column=1, sticky="nsew", padx=(4, 0), pady=(4, 0))
        tk.Label(liquidity, text="Liquidity + Source Analysis", bg="white", fg="#111827", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 6))
        self.txt_liquidity_source = tk.Text(liquidity, wrap="word", font=("Consolas", 10), bg="white")
        self.txt_liquidity_source.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt_liquidity_source.config(state="disabled")

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _period_bounds(self):
        mode = self.range_var.get()
        today = datetime.date.today()

        if mode == "This Month":
            start = today.replace(day=1)
            end = today
        elif mode == "Last 90 Days":
            start = today - datetime.timedelta(days=90)
            end = today
        elif mode == "This Year":
            start = today.replace(month=1, day=1)
            end = today
        else:
            return None, None

        return start, end

    def _period_where(self):
        start, end = self._period_bounds()
        if not start or not end:
            return "", (), None, None

        return (
            " WHERE date BETWEEN ? AND ? ",
            (start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")),
            start,
            end,
        )

    def _sql_with_extra(self, extra_condition):
        where_sql, params, _, _ = self._period_where()
        if where_sql:
            return f"{where_sql} AND {extra_condition}", params
        return f" WHERE {extra_condition} ", ()

    def _query_single(self, sql, params=()):
        self.db.cursor.execute(sql, params)
        row = self.db.cursor.fetchone()
        return row if row else (0,)

    def _load_series(self):
        where_sql, params, _, _ = self._period_where()

        self.db.cursor.execute(
            f"""
            SELECT date,
                   COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE 0 END),0) AS in_amt,
                   COALESCE(SUM(CASE WHEN flow='OUT' THEN amount ELSE 0 END),0) AS out_amt,
                   COALESCE(SUM(CASE WHEN status='Pending' THEN amount ELSE 0 END),0) AS pending_amt,
                   COALESCE(SUM(CASE WHEN status='Cleared' THEN amount ELSE 0 END),0) AS cleared_amt
            FROM transactions
            {where_sql}
            GROUP BY date
            ORDER BY date
            """,
            params,
        )
        drows = self.db.cursor.fetchall()
        self.daily_rows = [
            {
                "period": r[0],
                "in": float(r[1] or 0),
                "out": float(r[2] or 0),
                "pending": float(r[3] or 0),
                "cleared": float(r[4] or 0),
            }
            for r in drows
        ]

        self.db.cursor.execute(
            f"""
            SELECT strftime('%Y-W%W', date) AS wk,
                   COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE 0 END),0) AS in_amt,
                   COALESCE(SUM(CASE WHEN flow='OUT' THEN amount ELSE 0 END),0) AS out_amt,
                   COALESCE(SUM(CASE WHEN status='Pending' THEN amount ELSE 0 END),0) AS pending_amt,
                   COALESCE(SUM(CASE WHEN status='Cleared' THEN amount ELSE 0 END),0) AS cleared_amt
            FROM transactions
            {where_sql}
            GROUP BY wk
            ORDER BY wk
            """,
            params,
        )
        wrows = self.db.cursor.fetchall()
        self.weekly_rows = [
            {
                "period": r[0],
                "in": float(r[1] or 0),
                "out": float(r[2] or 0),
                "pending": float(r[3] or 0),
                "cleared": float(r[4] or 0),
            }
            for r in wrows
        ]

        self.db.cursor.execute(
            f"""
            SELECT strftime('%Y-%m', date) AS ym,
                   COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE 0 END),0) AS in_amt,
                   COALESCE(SUM(CASE WHEN flow='OUT' THEN amount ELSE 0 END),0) AS out_amt,
                   COALESCE(SUM(CASE WHEN status='Pending' THEN amount ELSE 0 END),0) AS pending_amt,
                   COALESCE(SUM(CASE WHEN status='Cleared' THEN amount ELSE 0 END),0) AS cleared_amt
            FROM transactions
            {where_sql}
            GROUP BY ym
            ORDER BY ym
            """,
            params,
        )
        mrows = self.db.cursor.fetchall()
        self.monthly_rows = [
            {
                "period": r[0],
                "in": float(r[1] or 0),
                "out": float(r[2] or 0),
                "pending": float(r[3] or 0),
                "cleared": float(r[4] or 0),
            }
            for r in mrows[-12:]
        ]

    def _rolling_avg(self, values, window):
        if not values:
            return []
        result = []
        for i in range(len(values)):
            start = max(0, i - window + 1)
            subset = values[start : i + 1]
            result.append(sum(subset) / len(subset))
        return result

    def load_analysis(self, event=None):
        where_sql, params, start_date, end_date = self._period_where()

        self._load_series()

        total_bills = self._query_single(f"SELECT COUNT(*) FROM transactions {where_sql}", params)[0] or 0
        total_amount = self._query_single(f"SELECT COALESCE(SUM(amount),0) FROM transactions {where_sql}", params)[0] or 0

        in_where, in_params = self._sql_with_extra("flow='IN'")
        out_where, out_params = self._sql_with_extra("flow='OUT'")
        pending_where, pending_params = self._sql_with_extra("status='Pending'")
        cleared_where, cleared_params = self._sql_with_extra("status='Cleared'")

        sales_in = self._query_single(f"SELECT COALESCE(SUM(amount),0) FROM transactions {in_where}", in_params)[0] or 0
        purchase_out = self._query_single(f"SELECT COALESCE(SUM(amount),0) FROM transactions {out_where}", out_params)[0] or 0
        pending_amt = self._query_single(f"SELECT COALESCE(SUM(amount),0) FROM transactions {pending_where}", pending_params)[0] or 0
        cleared_amt = self._query_single(f"SELECT COALESCE(SUM(amount),0) FROM transactions {cleared_where}", cleared_params)[0] or 0

        pending_count = self._query_single(f"SELECT COUNT(*) FROM transactions {pending_where}", pending_params)[0] or 0
        cleared_count = self._query_single(f"SELECT COUNT(*) FROM transactions {cleared_where}", cleared_params)[0] or 0

        net_cash = sales_in - purchase_out

        if start_date:
            opening = self._query_single(
                "SELECT COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE -amount END),0) FROM transactions WHERE date < ?",
                (start_date.strftime("%Y-%m-%d"),),
            )[0] or 0
        else:
            opening = 0

        if end_date:
            closing = self._query_single(
                "SELECT COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE -amount END),0) FROM transactions WHERE date <= ?",
                (end_date.strftime("%Y-%m-%d"),),
            )[0] or 0
        else:
            closing = self._query_single(
                "SELECT COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE -amount END),0) FROM transactions"
            )[0] or 0

        collection_pct = (cleared_count / total_bills * 100) if total_bills else 0
        pending_pct = (pending_amt / total_amount * 100) if total_amount else 0

        self.metric_labels["total_bills"].config(text=f"{int(total_bills)}")
        self.metric_labels["sales_in"].config(text=f"Rs {sales_in:,.2f}")
        self.metric_labels["purchase_out"].config(text=f"Rs {purchase_out:,.2f}")
        self.metric_labels["net_cash"].config(text=f"Rs {net_cash:,.2f}", fg="#166534" if net_cash >= 0 else "#b91c1c")
        self.metric_labels["opening_bal"].config(text=f"Rs {opening:,.2f}")
        self.metric_labels["closing_bal"].config(text=f"Rs {closing:,.2f}")
        self.metric_labels["collection_pct"].config(text=f"{collection_pct:.2f}%")
        self.metric_labels["pending_pct"].config(text=f"{pending_pct:.2f}%")

        self.load_cashflow_summary(opening, closing, sales_in, purchase_out, net_cash)
        self.load_cashflow_table()
        self.load_trend_analysis()
        self.load_breakdown_analysis(where_sql, params)
        self.load_advanced_analysis(where_sql, params, closing, sales_in, purchase_out, start_date, end_date)
        self.load_regression_analysis()
        self.draw_active_chart()

    def load_cashflow_summary(self, opening, closing, sales_in, purchase_out, net_cash):
        text = (
            f"Total Inflows         : Rs {sales_in:,.2f}\n"
            f"Total Outflows        : Rs {purchase_out:,.2f}\n"
            f"Net Movement          : Rs {net_cash:,.2f}\n"
            f"Opening Balance       : Rs {opening:,.2f}\n"
            f"Closing Balance       : Rs {closing:,.2f}\n"
            f"Balance Change        : Rs {(closing - opening):,.2f}\n"
            f"Aggregation View      : {self.agg_var.get()}"
        )
        self._set_text(self.txt_cashflow_summary, text)

    def load_cashflow_table(self):
        for iid in self.cashflow_tree.get_children():
            self.cashflow_tree.delete(iid)

        mode = self.agg_var.get()
        rows = self.monthly_rows if mode == "Monthly" else self.weekly_rows if mode == "Weekly" else self.daily_rows

        for row in rows:
            net = row["in"] - row["out"]
            self.cashflow_tree.insert(
                "",
                "end",
                values=(
                    row["period"],
                    f"{row['in']:,.2f}",
                    f"{row['out']:,.2f}",
                    f"{net:,.2f}",
                ),
            )

    def load_trend_analysis(self):
        if not self.daily_rows:
            self._set_text(self.txt_trend_analysis, "No trend data available for selected period.")
            self._set_text(self.txt_mom, "No month-over-month data available.")
            return

        in_vals = [r["in"] for r in self.daily_rows]
        out_vals = [r["out"] for r in self.daily_rows]
        net_vals = [r["in"] - r["out"] for r in self.daily_rows]

        in_7 = self._rolling_avg(in_vals, 7)[-1]
        out_7 = self._rolling_avg(out_vals, 7)[-1]
        net_7 = self._rolling_avg(net_vals, 7)[-1]

        in_30 = self._rolling_avg(in_vals, 30)[-1]
        out_30 = self._rolling_avg(out_vals, 30)[-1]
        net_30 = self._rolling_avg(net_vals, 30)[-1]

        accel_text = "Stable"
        if len(net_vals) >= 14:
            recent = sum(net_vals[-7:]) / 7
            prev = sum(net_vals[-14:-7]) / 7
            delta = recent - prev
            if delta > 0:
                accel_text = f"Growth accelerating (+{delta:,.2f} per day avg)"
            elif delta < 0:
                accel_text = f"Burn accelerating ({delta:,.2f} per day avg)"

        trend_text = (
            f"7-day Avg IN     : Rs {in_7:,.2f}\n"
            f"7-day Avg OUT    : Rs {out_7:,.2f}\n"
            f"7-day Net Avg    : Rs {net_7:,.2f}\n"
            f"30-day Avg IN    : Rs {in_30:,.2f}\n"
            f"30-day Avg OUT   : Rs {out_30:,.2f}\n"
            f"30-day Net Avg   : Rs {net_30:,.2f}\n"
            f"Trend Signal     : {accel_text}"
        )
        self._set_text(self.txt_trend_analysis, trend_text)

        if len(self.monthly_rows) >= 2:
            curr = self.monthly_rows[-1]
            prev = self.monthly_rows[-2]
            curr_net = curr["in"] - curr["out"]
            prev_net = prev["in"] - prev["out"]
            change = curr_net - prev_net
            change_pct = (change / abs(prev_net) * 100) if prev_net else 0

            mom_text = (
                f"Current Month ({curr['period']}) Net : Rs {curr_net:,.2f}\n"
                f"Previous Month ({prev['period']}) Net: Rs {prev_net:,.2f}\n"
                f"MoM Net Change                 : Rs {change:,.2f}\n"
                f"MoM % Change                   : {change_pct:.2f}%"
            )
        else:
            mom_text = "Need at least 2 months of data for MoM comparison."

        self._set_text(self.txt_mom, mom_text)

    def load_breakdown_analysis(self, where_sql, params):
        self.db.cursor.execute(
            f"""
            SELECT date, party_name, flow, amount, description
            FROM transactions
            {where_sql}
            ORDER BY amount DESC
            LIMIT 10
            """,
            params,
        )
        top_rows = self.db.cursor.fetchall()
        if top_rows:
            lines = [
                f"{r[0]} | {r[1]} | {r[2]} | Rs {float(r[3]):,.2f} | {str(r[4])[:35]}"
                for r in top_rows
            ]
            self._set_text(self.txt_top_tx, "\n".join(lines))
        else:
            self._set_text(self.txt_top_tx, "No transactions in selected period.")

        self.db.cursor.execute(
            f"""
            SELECT date,
                   COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE 0 END),0) AS in_amt,
                   COALESCE(SUM(CASE WHEN flow='OUT' THEN amount ELSE 0 END),0) AS out_amt,
                   COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE -amount END),0) AS net_amt
            FROM transactions
            {where_sql}
            GROUP BY date
            ORDER BY ABS(net_amt) DESC
            LIMIT 8
            """,
            params,
        )
        day_rows = self.db.cursor.fetchall()
        if day_rows:
            lines = [
                f"{r[0]} | IN {float(r[1]):,.2f} | OUT {float(r[2]):,.2f} | NET {float(r[3]):,.2f}"
                for r in day_rows
            ]
            self._set_text(self.txt_day_moves, "\n".join(lines))
        else:
            self._set_text(self.txt_day_moves, "No daily movement data.")

        self.db.cursor.execute(f"SELECT amount FROM transactions {where_sql}", params)
        amounts = [float(r[0] or 0) for r in self.db.cursor.fetchall()]
        bins = [
            (0, 1000),
            (1000, 5000),
            (5000, 10000),
            (10000, 25000),
            (25000, 999999999),
        ]
        freq_lines = []
        for low, high in bins:
            if high >= 999999999:
                cnt = sum(1 for a in amounts if a >= low)
                label = f">= {low:,.0f}"
            else:
                cnt = sum(1 for a in amounts if low <= a < high)
                label = f"{low:,.0f} - {high:,.0f}"
            freq_lines.append(f"{label:<18}: {cnt}")

        self._set_text(self.txt_freq, "\n".join(freq_lines) if freq_lines else "No frequency data.")

    def _linear_forecast(self, values, future_points):
        n = len(values)
        if n < 2:
            return None

        x_sum = sum(range(n))
        y_sum = sum(values)
        xx_sum = sum(i * i for i in range(n))
        xy_sum = sum(i * values[i] for i in range(n))

        den = (n * xx_sum) - (x_sum * x_sum)
        if den == 0:
            return None

        slope = ((n * xy_sum) - (x_sum * y_sum)) / den
        intercept = (y_sum - slope * x_sum) / n

        forecasts = []
        for step in future_points:
            x = (n - 1) + step
            forecasts.append(intercept + slope * x)
        return forecasts

    def _format_month_label(self, ym):
        try:
            y, m = ym.split("-")
            return f"{calendar.month_abbr[int(m)]} {y[2:]}"
        except:
            return ym

    def _monthly_net_regression(self):
        rows = self.monthly_rows or []
        if len(rows) < 3:
            return None

        y_vals = [float(r["in"] - r["out"]) for r in rows]
        n = len(y_vals)
        x_vals = list(range(n))

        x_sum = sum(x_vals)
        y_sum = sum(y_vals)
        xx_sum = sum(i * i for i in x_vals)
        xy_sum = sum(i * y_vals[i] for i in x_vals)
        den = (n * xx_sum) - (x_sum * x_sum)
        if den == 0:
            return None

        slope = ((n * xy_sum) - (x_sum * y_sum)) / den
        intercept = (y_sum - slope * x_sum) / n

        fit_vals = [intercept + slope * i for i in x_vals]
        y_mean = y_sum / n
        ss_tot = sum((v - y_mean) ** 2 for v in y_vals)
        ss_res = sum((y_vals[i] - fit_vals[i]) ** 2 for i in range(n))
        r2 = 1 - (ss_res / ss_tot) if ss_tot else 0

        forecast_steps = [1, 2, 3]
        forecast_vals = [intercept + slope * ((n - 1) + step) for step in forecast_steps]

        last_period = rows[-1]["period"]
        try:
            y, m = map(int, last_period.split("-"))
            future_labels = []
            for step in forecast_steps:
                nm = m + step
                ny = y + (nm - 1) // 12
                nm = ((nm - 1) % 12) + 1
                future_labels.append(f"{ny:04d}-{nm:02d}")
        except:
            future_labels = [f"F+{s}" for s in forecast_steps]

        return {
            "x": x_vals,
            "actual": y_vals,
            "fit": fit_vals,
            "slope": slope,
            "intercept": intercept,
            "r2": r2,
            "forecast": forecast_vals,
            "future_labels": future_labels,
            "labels": [r["period"] for r in rows],
        }

    def load_regression_analysis(self):
        if not hasattr(self, "txt_regression"):
            return

        reg = self._monthly_net_regression()
        if not reg:
            self._set_text(
                self.txt_regression,
                "Need at least 3 months of data to run regression on monthly net cash.",
            )
            self._draw_regression_chart(None)
            return

        slope = reg["slope"]
        r2 = reg["r2"]
        trend = "Upward" if slope > 0 else "Downward" if slope < 0 else "Flat"
        confidence = "Strong" if r2 >= 0.70 else "Moderate" if r2 >= 0.40 else "Weak"

        lines = [
            "Model: Monthly Net Cash ~ Linear(Time)",
            f"Equation: y = {reg['intercept']:,.2f} + ({slope:,.2f} x month_index)",
            f"R^2: {r2:.3f}  ({confidence} explanatory power)",
            f"Trend: {trend}",
            "",
            "3-Month Forecast (Net Cash):",
        ]
        for lbl, val in zip(reg["future_labels"], reg["forecast"]):
            lines.append(f"- {lbl}: Rs {val:,.2f}")

        lines.extend(
            [
                "",
                "Interpretation:",
                "- Positive slope means improving monthly net position.",
                "- Negative slope means weakening monthly net position.",
                "- Higher R^2 means the linear trend explains more of the movement.",
            ]
        )

        self._set_text(self.txt_regression, "\n".join(lines))
        self._draw_regression_chart(reg)

    def _draw_regression_chart(self, reg):
        if not hasattr(self, "regression_canvas"):
            return

        canvas = self.regression_canvas
        canvas.delete("all")

        width = canvas.winfo_width() or 760
        height = canvas.winfo_height() or 360

        if not reg:
            canvas.create_text(
                width / 2,
                height / 2,
                text="Insufficient data for regression",
                fill="#64748b",
                font=("Segoe UI", 12, "bold"),
            )
            return

        labels = reg["labels"] + reg["future_labels"]
        actual = reg["actual"]
        fit_all = reg["fit"] + reg["forecast"]

        left, top, right, bottom = 52, 24, 24, 42
        plot_w = max(120, width - left - right)
        plot_h = max(120, height - top - bottom)

        canvas.create_text(
            left,
            top - 10,
            text="Metric: Monthly Net Cash (Rs, axis in K/L/Cr)",
            anchor="w",
            fill="#475569",
            font=("Segoe UI", 9, "bold"),
        )

        all_vals = actual + fit_all
        min_v = min(all_vals + [0])
        max_v = max(all_vals + [1])
        span = max(1.0, max_v - min_v)

        self._draw_y_ticks(min_v, max_v, left, top, plot_h, canvas=canvas)

        def xy(index, value):
            x_step = plot_w / max(1, len(labels) - 1)
            x = left + index * x_step
            y = top + plot_h - ((value - min_v) / span) * (plot_h - 8)
            return x, y

        self._draw_axes(left, top, plot_w, plot_h, canvas=canvas)

        fit_points = []
        for i, v in enumerate(fit_all):
            x, y = xy(i, v)
            fit_points.extend([x, y])
        if len(fit_points) >= 4:
            canvas.create_line(*fit_points, fill="#2563eb", width=2.0, dash=(4, 3), smooth=True)

        actual_points = []
        for i, v in enumerate(actual):
            x, y = xy(i, v)
            actual_points.extend([x, y])
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#16a34a", outline="")
        if len(actual_points) >= 4:
            canvas.create_line(*actual_points, fill="#16a34a", width=2.2, smooth=True)

        cutoff = len(actual) - 1
        cx, _ = xy(cutoff, min_v)
        canvas.create_line(cx, top, cx, top + plot_h, fill="#cbd5e1", dash=(2, 2))

        x_step = plot_w / max(1, len(labels) - 1)
        for i, lbl in enumerate(labels):
            if len(labels) > 10 and i % 2 == 1:
                continue
            x = left + i * x_step
            canvas.create_text(x, top + plot_h + 14, text=self._format_month_label(lbl), fill="#334155", font=("Segoe UI", 8))

        self._draw_legend(
            [
                ("Actual Net", actual, "#16a34a"),
                ("Regression Fit", fit_all, "#2563eb"),
            ],
            left + plot_w - 170,
            top + 8,
            canvas=canvas,
        )

    def load_advanced_analysis(self, where_sql, params, closing_balance, sales_in, purchase_out, start_date, end_date):
        period_days = 0
        if start_date and end_date:
            period_days = max(1, (end_date - start_date).days + 1)
        elif self.daily_rows:
            period_days = len(self.daily_rows)
        else:
            period_days = 1

        avg_daily_out = purchase_out / period_days if period_days else 0
        active_months = max(1, len(self.monthly_rows))
        avg_monthly_out = purchase_out / active_months
        runway_days = (closing_balance / avg_daily_out) if avg_daily_out > 0 else 0

        burn_text = (
            f"Average Daily Outflow : Rs {avg_daily_out:,.2f}\n"
            f"Average Monthly Outflow: Rs {avg_monthly_out:,.2f}\n"
            f"Estimated Runway       : {runway_days:,.1f} days\n"
            f"Current Cash Position  : Rs {closing_balance:,.2f}"
        )
        self._set_text(self.txt_burn, burn_text)

        self.db.cursor.execute(f"SELECT id, date, party_name, flow, amount FROM transactions {where_sql}", params)
        tx_rows = self.db.cursor.fetchall()
        signed = [float(r[4]) if r[3] == "IN" else -float(r[4]) for r in tx_rows]

        if len(signed) >= 2:
            mean = sum(signed) / len(signed)
            var = sum((x - mean) ** 2 for x in signed) / len(signed)
            std = math.sqrt(var)
            thresh = 2 * std

            anoms = []
            for r, val in zip(tx_rows, signed):
                if abs(val - mean) > thresh:
                    anoms.append((r[1], r[2], r[3], float(r[4]), val - mean))

            if anoms:
                lines = [
                    f"{a[0]} | {a[1]} | {a[2]} | Rs {a[3]:,.2f} | deviation {a[4]:,.2f}"
                    for a in anoms[:12]
                ]
                anomaly_text = "\n".join(lines)
            else:
                anomaly_text = "No anomalies beyond 2σ in selected period."
        else:
            anomaly_text = "Not enough transactions for anomaly detection."

        self._set_text(self.txt_anomaly, anomaly_text)

        if start_date and end_date:
            span_days = max(1, (end_date - start_date).days + 1)
            prev_end = start_date - datetime.timedelta(days=1)
            prev_start = prev_end - datetime.timedelta(days=span_days - 1)

            self.db.cursor.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE 0 END),0),
                       COALESCE(SUM(CASE WHEN flow='OUT' THEN amount ELSE 0 END),0),
                       COUNT(*)
                FROM transactions
                WHERE date BETWEEN ? AND ?
                """,
                (prev_start.strftime("%Y-%m-%d"), prev_end.strftime("%Y-%m-%d")),
            )
            prev_in, prev_out, prev_count = self.db.cursor.fetchone()
            prev_net = float(prev_in or 0) - float(prev_out or 0)
        else:
            prev_in = prev_out = prev_count = prev_net = 0

        curr_net = sales_in - purchase_out
        curr_count = self._query_single(f"SELECT COUNT(*) FROM transactions {where_sql}", params)[0] or 0

        def pct(curr, prev):
            return ((curr - prev) / abs(prev) * 100) if prev else 0

        compare_lines = [
            f"Current vs Previous Equivalent Period",
            f"Bills Count Change : {pct(curr_count, prev_count):.2f}%",
            f"Inflow Change      : {pct(sales_in, prev_in):.2f}%",
            f"Outflow Change     : {pct(purchase_out, prev_out):.2f}%",
            f"Net Cash Change    : {pct(curr_net, prev_net):.2f}%",
            "",
        ]

        cumulative = []
        running = 0
        for row in self.daily_rows:
            running += (row["in"] - row["out"])
            cumulative.append(running)

        lin = self._linear_forecast(cumulative, [30, 60]) if cumulative else None
        last_30_net = [r["in"] - r["out"] for r in self.daily_rows[-30:]]
        ma_net = (sum(last_30_net) / len(last_30_net)) if last_30_net else 0

        if lin:
            compare_lines.append(f"Linear Forecast (+30d): Rs {lin[0]:,.2f}")
            compare_lines.append(f"Linear Forecast (+60d): Rs {lin[1]:,.2f}")
        else:
            compare_lines.append("Linear Forecast: Not enough points")

        compare_lines.append(f"Moving Avg Net/day   : Rs {ma_net:,.2f}")
        compare_lines.append(f"MA Forecast +30 days : Rs {(closing_balance + ma_net * 30):,.2f}")
        compare_lines.append(f"MA Forecast +60 days : Rs {(closing_balance + ma_net * 60):,.2f}")

        self._set_text(self.txt_compare_forecast, "\n".join(compare_lines))

        op_cash_ratio = (sales_in / purchase_out) if purchase_out else 0
        burn_ratio = (purchase_out / sales_in) if sales_in else 0

        self.db.cursor.execute(
            f"""
            SELECT COALESCE(SUM(amount),0)
            FROM (
                SELECT amount
                FROM transactions
                {where_sql}
                AND flow='IN'
                ORDER BY amount DESC
                LIMIT 3
            )
            """
            if where_sql
            else """
            SELECT COALESCE(SUM(amount),0)
            FROM (
                SELECT amount
                FROM transactions
                WHERE flow='IN'
                ORDER BY amount DESC
                LIMIT 3
            )
            """,
            params,
        )
        top3_inflow = float(self.db.cursor.fetchone()[0] or 0)

        inflow_concentration = (top3_inflow / sales_in) if sales_in else 0
        cash_velocity = (curr_count / period_days) if period_days else 0
        net_cash_margin = (curr_net / sales_in * 100) if sales_in else 0

        if op_cash_ratio > 1.10:
            op_tag = "GOOD"
        elif op_cash_ratio >= 0.90:
            op_tag = "WATCH"
        else:
            op_tag = "RISK"

        if burn_ratio < 0.70:
            burn_tag = "GOOD"
        elif burn_ratio <= 0.90:
            burn_tag = "WATCH"
        else:
            burn_tag = "RISK"

        if inflow_concentration < 0.60:
            conc_tag = "GOOD"
        elif inflow_concentration <= 0.70:
            conc_tag = "WATCH"
        else:
            conc_tag = "RISK"

        if cash_velocity >= 1.00:
            vel_tag = "GOOD"
        elif cash_velocity >= 0.40:
            vel_tag = "WATCH"
        else:
            vel_tag = "RISK"

        if net_cash_margin >= 15:
            margin_tag = "GOOD"
        elif net_cash_margin >= 0:
            margin_tag = "WATCH"
        else:
            margin_tag = "RISK"

        self.db.cursor.execute(
            f"""
            SELECT party_name,
                   COALESCE(SUM(CASE WHEN flow='IN' THEN amount ELSE 0 END),0) AS in_amt,
                   COALESCE(SUM(CASE WHEN flow='OUT' THEN amount ELSE 0 END),0) AS out_amt,
                   COUNT(*)
            FROM transactions
            {where_sql}
            GROUP BY party_name
            ORDER BY (in_amt + out_amt) DESC
            LIMIT 6
            """,
            params,
        )
        source_rows = self.db.cursor.fetchall()

        lines = [
            "RATIO BLOCK (with benchmark ranges)",
            "",
            "1) Operating Cash Ratio = Inflows / Outflows",
            f"   Current : {op_cash_ratio:.2f}  [{op_tag}]",
            "   Better  : > 1.10 | Watch: 0.90 - 1.10 | Risk: < 0.90",
            "",
            "2) Cash Burn Ratio = Outflows / Inflows",
            f"   Current : {burn_ratio:.2f}  [{burn_tag}]",
            "   Better  : < 0.70 | Watch: 0.70 - 0.90 | Risk: > 0.90",
            "",
            "3) Inflow Concentration = Top3 Inflows / Total Inflows",
            f"   Current : {inflow_concentration*100:.2f}%  [{conc_tag}]",
            "   Better  : < 60% | Watch: 60% - 70% | Risk: > 70%",
            "",
            "4) Cash Velocity = Total Transactions / Period Days",
            f"   Current : {cash_velocity:.2f} tx/day  [{vel_tag}]",
            "   Better  : >= 1.00 | Watch: 0.40 - 1.00 | Risk: < 0.40",
            "",
            "5) Net Cash Margin (Proxy) = Net Cash / Inflows * 100",
            f"   Current : {net_cash_margin:.2f}%  [{margin_tag}]",
            "   Better  : >= 15% | Watch: 0% - 15% | Risk: < 0%",
            "",
            "Top Cash Sources/Uses by Party:",
        ]
        if source_rows:
            for idx, r in enumerate(source_rows, start=1):
                lines.append(f"{idx}. {r[0]} | IN {float(r[1]):,.2f} | OUT {float(r[2]):,.2f} | TX {int(r[3])}")
        else:
            lines.append("No source data in selected period.")

        self._set_text(self.txt_liquidity_source, "\n".join(lines))

    def draw_active_chart(self):
        if not hasattr(self, "chart_canvas"):
            return

        canvas = self.chart_canvas
        canvas.delete("all")

        width = canvas.winfo_width() or 760
        height = canvas.winfo_height() or 360

        if not self.monthly_rows:
            canvas.create_text(width / 2, height / 2, text="No data for selected period", fill="#64748b", font=("Segoe UI", 12, "bold"))
            return

        mode = self.chart_mode_var.get()
        rows = self.monthly_rows
        labels = [r["period"][5:] for r in rows]

        metric_text = ""
        if mode in ("IN vs OUT (Line)", "IN vs OUT (Bar)", "Pending vs Cleared (Bar)"):
            metric_text = "Metric: Amount (Rs, axis in K/L/Cr)"
        elif mode == "Net Cash (Line)":
            metric_text = "Metric: Net Cash (Rs, axis in K/L/Cr)"
        elif mode == "Cumulative Net (Area)":
            metric_text = "Metric: Cumulative Net (Rs, axis in K/L/Cr)"

        left, top, right, bottom = 52, 24, 24, 42
        plot_w = max(120, width - left - right)
        plot_h = max(120, height - top - bottom)

        if metric_text:
            canvas.create_text(
                left,
                top - 10,
                text=metric_text,
                anchor="w",
                fill="#475569",
                font=("Segoe UI", 9, "bold"),
            )

        if mode == "IN vs OUT (Line)":
            self._draw_line_chart(
                labels,
                [("IN", [r["in"] for r in rows], "#16a34a"), ("OUT", [r["out"] for r in rows], "#dc2626")],
                left,
                top,
                plot_w,
                plot_h,
            )
        elif mode == "IN vs OUT (Bar)":
            self._draw_bar_chart(
                labels,
                [("IN", [r["in"] for r in rows], "#16a34a"), ("OUT", [r["out"] for r in rows], "#dc2626")],
                left,
                top,
                plot_w,
                plot_h,
            )
        elif mode == "Net Cash (Line)":
            self._draw_line_chart(
                labels,
                [("NET", [r["in"] - r["out"] for r in rows], "#2563eb")],
                left,
                top,
                plot_w,
                plot_h,
            )
        elif mode == "Cumulative Net (Area)":
            vals = []
            run = 0
            for r in rows:
                run += (r["in"] - r["out"])
                vals.append(run)
            self._draw_area_chart(labels, vals, "#1d4ed8", left, top, plot_w, plot_h)
        else:
            self._draw_bar_chart(
                labels,
                [("Pending", [r["pending"] for r in rows], "#d97706"), ("Cleared", [r["cleared"] for r in rows], "#0f766e")],
                left,
                top,
                plot_w,
                plot_h,
            )

    def _draw_axes(self, left, top, plot_w, plot_h, canvas=None):
        target = canvas if canvas is not None else self.chart_canvas
        target.create_line(left, top, left, top + plot_h, fill="#94a3b8")
        target.create_line(left, top + plot_h, left + plot_w, top + plot_h, fill="#94a3b8")

    def _format_inr_axis(self, value):
        v = float(value or 0)
        abs_v = abs(v)
        if abs_v >= 10000000:
            return f"Rs {v / 10000000:.2f} Cr"
        if abs_v >= 100000:
            return f"Rs {v / 100000:.2f} L"
        if abs_v >= 1000:
            return f"Rs {v / 1000:.2f} K"
        return f"Rs {v:,.0f}"

    def _draw_y_ticks(self, min_v, max_v, left, top, plot_h, canvas=None):
        target = canvas if canvas is not None else self.chart_canvas
        span = max(1.0, max_v - min_v)
        ticks = [
            max_v,
            min_v + span * 0.75,
            min_v + span * 0.50,
            min_v + span * 0.25,
            min_v,
        ]
        for tick in ticks:
            y = top + plot_h - ((tick - min_v) / span) * (plot_h - 8)
            target.create_line(left - 4, y, left, y, fill="#94a3b8")
            target.create_text(left - 8, y, text=self._format_inr_axis(tick), anchor="e", fill="#475569", font=("Segoe UI", 8))

    def _draw_line_chart(self, labels, series, left, top, plot_w, plot_h):
        canvas = self.chart_canvas
        self._draw_axes(left, top, plot_w, plot_h)

        all_vals = [v for _, vals, _ in series for v in vals]
        min_v = min(all_vals + [0])
        max_v = max(all_vals + [1])
        span = max(1.0, max_v - min_v)

        self._draw_y_ticks(min_v, max_v, left, top, plot_h)

        x_step = plot_w / max(1, len(labels) - 1)
        for _, values, color in series:
            points = []
            for idx, v in enumerate(values):
                x = left + idx * x_step
                y = top + plot_h - ((v - min_v) / span) * (plot_h - 8)
                points.extend([x, y])
            if len(points) >= 4:
                canvas.create_line(*points, fill=color, width=2.2, smooth=True)

        for idx, lbl in enumerate(labels):
            x = left + idx * x_step
            canvas.create_text(x, top + plot_h + 14, text=lbl, fill="#334155", font=("Segoe UI", 8))

        self._draw_legend(series, left + plot_w - 170, top + 8)

    def _draw_bar_chart(self, labels, series, left, top, plot_w, plot_h):
        canvas = self.chart_canvas
        self._draw_axes(left, top, plot_w, plot_h)

        max_v = max([v for _, vals, _ in series for v in vals] + [1])
        self._draw_y_ticks(0, max_v, left, top, plot_h)
        groups = len(labels)
        group_w = plot_w / max(1, groups)
        bar_w = min(24, (group_w * 0.72) / max(1, len(series)))

        for i, lbl in enumerate(labels):
            base = left + i * group_w + group_w * 0.14
            for j, (_, vals, color) in enumerate(series):
                v = vals[i]
                h = (v / max_v) * (plot_h - 8)
                x1 = base + j * (bar_w + 4)
                x2 = x1 + bar_w
                y1 = top + plot_h - h
                y2 = top + plot_h
                canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
            cx = left + i * group_w + group_w / 2
            canvas.create_text(cx, top + plot_h + 14, text=lbl, fill="#334155", font=("Segoe UI", 8))

        self._draw_legend(series, left + plot_w - 170, top + 8)

    def _draw_area_chart(self, labels, values, color, left, top, plot_w, plot_h):
        canvas = self.chart_canvas
        self._draw_axes(left, top, plot_w, plot_h)

        min_v = min(values + [0])
        max_v = max(values + [1])
        span = max(1.0, max_v - min_v)

        self._draw_y_ticks(min_v, max_v, left, top, plot_h)

        x_step = plot_w / max(1, len(labels) - 1)
        line_points = []
        for idx, v in enumerate(values):
            x = left + idx * x_step
            y = top + plot_h - ((v - min_v) / span) * (plot_h - 8)
            line_points.extend([x, y])

        baseline = top + plot_h - ((0 - min_v) / span) * (plot_h - 8)
        if len(line_points) >= 4:
            polygon_points = [left, baseline] + line_points + [left + plot_w, baseline]
            canvas.create_polygon(*polygon_points, fill="#dbeafe", outline="")
            canvas.create_line(*line_points, fill=color, width=2.2, smooth=True)

        for idx, lbl in enumerate(labels):
            x = left + idx * x_step
            canvas.create_text(x, top + plot_h + 14, text=lbl, fill="#334155", font=("Segoe UI", 8))

        self._draw_legend([("CUM NET", values, color)], left + plot_w - 170, top + 8)

    def _draw_legend(self, series, x, y, canvas=None):
        target = canvas if canvas is not None else self.chart_canvas
        offset = 0
        for name, _, color in series:
            target.create_rectangle(x, y + offset, x + 12, y + offset + 12, fill=color, outline="")
            target.create_text(x + 18, y + offset + 6, text=name, anchor="w", fill="#334155", font=("Segoe UI", 9, "bold"))
            offset += 16
