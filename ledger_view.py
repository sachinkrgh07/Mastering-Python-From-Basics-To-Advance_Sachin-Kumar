import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from datetime import timedelta
import printer 

class LedgerPage(tk.Frame):
    def __init__(self, parent, controller, db_manager):
        super().__init__(parent)
        self.controller = controller
        self.db = db_manager
        self.configure(bg="#f5f7fb")
        
        # Date defaults (Today)
        self.start_date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        self.end_date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        
        self.setup_ui()
        # Default load: This Month
        self.filter_range("month")
        self.bind_all_keys()
        self.bind("<Destroy>", self.cleanup_shortcuts)

    def bind_all_keys(self):
        self.controller.bind("<Control-f>", self.focus_filter_start)
        self.controller.bind("<Control-p>", self.trigger_print)

    def cleanup_shortcuts(self, event):
        if event.widget == self:
            try:
                self.controller.unbind("<Control-f>")
                self.controller.unbind("<Control-p>")
            except:
                pass

    def focus_filter_start(self, event=None):
        try:
            self.ent_start.focus_set()
            self.ent_start.selection_range(0, tk.END)
        except:
            pass

    def trigger_print(self, event=None):
        try:
            self.print_report()
        except:
            pass

    def setup_ui(self):
        # --- HEADER ---
        header_frame = tk.Frame(self, bg="#1f2937", height=54)
        header_frame.pack(fill="x")
        
        btn_back = tk.Button(header_frame, text="< Menu", bg="#1d4ed8", fg="white", font=("Arial", 9, "bold"),
                             command=self.controller.show_main_menu, relief="flat")
        btn_back.pack(side="left", padx=10, pady=10)
        
        tk.Label(header_frame, text="CASH LEDGER", bg="#1f2937", fg="white", font=("Segoe UI", 14, "bold")).pack(side="left", padx=10)

        # Print Button
        btn_print = tk.Button(header_frame, text="🖨 Print Report", bg="#2563eb", fg="white", 
                              font=("Segoe UI", 9, "bold"), command=self.print_report)
        btn_print.pack(side="right", padx=20, pady=10)

        # --- FILTER BAR ---
        filter_frame = tk.LabelFrame(self, text="Date Range Filters", bg="#f5f7fb", padx=10, pady=5)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Quick Buttons
        btn_frame = tk.Frame(filter_frame, bg="#f5f7fb")
        btn_frame.pack(side="left")
        
        tk.Button(btn_frame, text="Today", command=lambda: self.filter_range("today")).pack(side="left", padx=2)
        tk.Button(btn_frame, text="This Week", command=lambda: self.filter_range("week")).pack(side="left", padx=2)
        tk.Button(btn_frame, text="This Month", command=lambda: self.filter_range("month")).pack(side="left", padx=2)
        tk.Button(btn_frame, text="This Year", command=lambda: self.filter_range("year")).pack(side="left", padx=2)
        tk.Button(btn_frame, text="ALL TIME", bg="#e2e8f0", command=lambda: self.filter_range("all")).pack(side="left", padx=10)

        # Custom Range
        tk.Label(filter_frame, text="From:", bg="#f5f7fb").pack(side="left", padx=(10, 2))
        self.ent_start = tk.Entry(filter_frame, textvariable=self.start_date_var, width=10)
        self.ent_start.pack(side="left", padx=2)

        tk.Label(filter_frame, text="To:", bg="#f5f7fb").pack(side="left", padx=2)
        self.ent_end = tk.Entry(filter_frame, textvariable=self.end_date_var, width=10)
        self.ent_end.pack(side="left", padx=2)

        self.ent_start.bind("<Return>", lambda e: self.ent_end.focus_set())
        self.ent_end.bind("<Return>", lambda e: self.load_data())

        tk.Button(filter_frame, text="Go ➤", bg="#16a34a", fg="white", command=self.load_data).pack(side="left", padx=10)

        # --- BALANCE DISPLAY ---
        bal_frame = tk.Frame(self, bg="#1f2937", height=42)
        bal_frame.pack(fill="x", padx=10)
        
        self.lbl_balance = tk.Label(bal_frame, text="Running Balance: 0.00", font=("Consolas", 14, "bold"), bg="#1f2937", fg="#22c55e")
        self.lbl_balance.pack(side="right", padx=20)
        
        self.lbl_period = tk.Label(bal_frame, text="Showing: All Time", font=("Segoe UI", 10), bg="#1f2937", fg="#cbd5e1")
        self.lbl_period.pack(side="left", padx=20)

        # --- DATA TABLE ---
        table_frame = tk.Frame(self, bg="white", relief="raised")
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

        scroll_y = ttk.Scrollbar(table_frame)
        scroll_y.pack(side="right", fill="y")

        # Added Status Column
        cols = ("ID", "Date", "Particulars", "Type", "Cash In", "Cash Out", "Balance", "Status")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", yscrollcommand=scroll_y.set, height=18)
        scroll_y.config(command=self.tree.yview)

        style = ttk.Style()
        style.configure("Ledger.Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure("Ledger.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0", foreground="#111827")
        self.tree.configure(style="Ledger.Treeview")

        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("Date", width=80, anchor="center")
        self.tree.column("Particulars", width=300, anchor="w")
        self.tree.column("Type", width=50, anchor="center")
        self.tree.column("Cash In", width=80, anchor="e")
        self.tree.column("Cash Out", width=80, anchor="e")
        self.tree.column("Balance", width=100, anchor="e")
        self.tree.column("Status", width=80, anchor="center") # New Status Col

        for col in cols: self.tree.heading(col, text=col)

        self.tree.pack(fill="both", expand=True)
        
        # Visual Tags
        self.tree.tag_configure('oddrow', background="white")
        self.tree.tag_configure('evenrow', background="#f9f9f9")
        self.tree.tag_configure('cleared', foreground="green") # Cleared items text becomes green

    # --- LOGIC ---
    def filter_range(self, mode):
        today = datetime.date.today()
        start = today
        end = today

        if mode == "today":
            pass
        elif mode == "week":
            start = today - timedelta(days=today.weekday()) # Monday
            end = start + timedelta(days=6) # Sunday
        elif mode == "month":
            start = today.replace(day=1)
            # End of month calc
            next_month = today.replace(day=28) + timedelta(days=4)
            end = next_month - timedelta(days=next_month.day)
        elif mode == "year":
            start = today.replace(month=1, day=1)
            end = today.replace(month=12, day=31)
        elif mode == "all":
            start = "1900-01-01" # Arbitrary old date
            end = "2099-12-31"

        # Update boxes
        if isinstance(start, datetime.date):
            self.start_date_var.set(start.strftime("%Y-%m-%d"))
            self.end_date_var.set(end.strftime("%Y-%m-%d"))
        else:
            self.start_date_var.set(start)
            self.end_date_var.set(end)
            
        self.load_data()

    def load_data(self):
        # 1. Clear Table
        for row in self.tree.get_children(): self.tree.delete(row)

        s_date = self.start_date_var.get()
        e_date = self.end_date_var.get()
        self.lbl_period.config(text=f"Period: {s_date} to {e_date}")

        try:
            # CHANGED SQL: Added "AND status IS NOT 'Cleared'"
            sql = "SELECT * FROM transactions WHERE (status IS NOT 'Cleared') AND (date BETWEEN ? AND ?) ORDER BY date ASC, id ASC"
            self.db.cursor.execute(sql, (s_date, e_date))
            rows = self.db.cursor.fetchall()
        except Exception as e:
            rows = []

        # 2. Process & Calculate
        running_bal = 0.0
        
        # We need to know the Opening Balance before this period to make the running balance accurate
        # (Optional advanced feature, for now we assume 0 or calc from fetched)
        # For a simple cash book, we usually just sum what we see. 
        # But for accuracy, we should really sum everything BEFORE start_date.
        
        try:
            self.db.cursor.execute("SELECT SUM(CASE WHEN flow='IN' THEN amount ELSE -amount END) FROM transactions WHERE date < ?", (s_date,))
            res = self.db.cursor.fetchone()[0]
            opening_bal = res if res else 0.0
        except:
            opening_bal = 0.0
            
        running_bal = opening_bal
        
        # Insert Opening Balance Row
        self.tree.insert("", "end", values=("", s_date, ">> OPENING BALANCE <<", "", "", "", f"{opening_bal:.2f}", "-"), tags=('evenrow',))

        count = 0
        for row in rows:
            # unpack safely
            r_id, r_date, r_party, r_desc, r_flow, r_amount = row[0], row[1], row[2], row[3], row[4], row[5]
            # Handle Status column safely
            r_status = row[6] if len(row) > 6 else "Pending"
            if r_status is None: r_status = "Pending"
            
            cash_in = ""
            cash_out = ""
            
            if r_flow == "IN":
                cash_in = f"{r_amount:.2f}"
                running_bal += r_amount
                txn_type = "Rcpt"
            else:
                cash_out = f"{r_amount:.2f}"
                running_bal -= r_amount
                txn_type = "Pymt"

            particulars = f"{r_party} | {r_desc}"
            
            tags = []
            tags.append('evenrow' if count % 2 == 0 else 'oddrow')
            
            display_status = r_status
            if r_status == "Cleared":
                display_status = "✓"
                tags.append('cleared')
            
            self.tree.insert("", "end", values=(
                r_id, r_date, particulars, txn_type, cash_in, cash_out, f"{running_bal:.2f}", display_status
            ), tags=tuple(tags))
            
            count += 1
            
        # Update Balance Label
        color = "#00ff00" if running_bal >= 0 else "#ff5555"
        self.lbl_balance.config(text=f"Closing Bal: {running_bal:.2f}", fg=color)

    def print_report(self):
        # Collect data currently in treeview to send to printer
        # Logic: We scrape the treeview items to print exactly what the user sees
        
        rows_to_print = []
        for child in self.tree.get_children():
            rows_to_print.append(self.tree.item(child)['values'])
            
        if not rows_to_print:
            messagebox.showwarning("Empty", "No data to print.")
            return
            
        printer.generate_ledger_report(rows_to_print, self.start_date_var.get(), self.end_date_var.get())