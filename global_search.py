import tkinter as tk
from tkinter import ttk, messagebox
import re
import datetime
import printer 
import bill_entry

class GlobalSearchPopup(tk.Toplevel):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.title("Global Power Search (Ctrl+G)")
        self.geometry("900x500")
        self.configure(bg="#0f172a")
        
        # Center the window
        try:
            x = parent.winfo_rootx() + 50
            y = parent.winfo_rooty() + 50
            self.geometry(f"+{x}+{y}")
        except: pass

        self.setup_ui()
        self.bind_keys()
        self.entry_search.focus_set()
        
        # Store found rows for print logic
        self.found_rows = []
        self.run_smart_search()

    def bind_keys(self):
        self.bind("<Escape>", lambda e: self.destroy())
        self.entry_search.bind("<KeyRelease>", self.run_smart_search)
        self.entry_search.bind("<Down>", self.move_selection_down)
        self.entry_search.bind("<Up>", self.move_selection_up)
        self.entry_search.bind("<Return>", self.open_selected_bill)
        
        # Treeview Actions
        self.tree.bind("<Return>", self.open_selected_bill)
        self.tree.bind("<x>", self.settle_selected)      # 'x' to Settle
        self.tree.bind("<Down>", self.move_selection_down)
        self.tree.bind("<Up>", self.move_selection_up)

    def setup_ui(self):
        # Header / Help
        info_frame = tk.Frame(self, bg="#0f172a")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        lbl_help = tk.Label(
            info_frame,
            text="Natural Search: Ash bell > 9000 out | 2026-03-01 to 2026-03-20 | 5000-12000 pending",
            bg="#0f172a", fg="#cbd5e1", font=("Consolas", 9)
        )
        lbl_help.pack(side="left")

        # Search Input
        input_frame = tk.Frame(self, bg="#0f172a", pady=6)
        input_frame.pack(fill="x", padx=10)
        
        tk.Label(input_frame, text="🔍 POWER SEARCH:", bg="#0f172a", fg="#facc15", font=("Segoe UI", 12, "bold")).pack(side="left")
        
        self.entry_search = ttk.Entry(input_frame, font=("Segoe UI", 12))
        self.entry_search.pack(side="left", fill="x", expand=True, padx=10)

        # Results List
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        sc = ttk.Scrollbar(list_frame)
        sc.pack(side="right", fill="y")
        
        cols = ("ID", "Date", "Party", "Description", "Amount", "Status")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", yscrollcommand=sc.set, height=15)
        sc.config(command=self.tree.yview)

        style = ttk.Style()
        style.configure("GlobalSearch.Treeview", font=("Segoe UI", 10), rowheight=28)
        style.configure("GlobalSearch.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0", foreground="#111827")
        self.tree.configure(style="GlobalSearch.Treeview")
        
        self.tree.heading("ID", text="ID"); self.tree.column("ID", width=40, anchor="center")
        self.tree.heading("Date", text="Date"); self.tree.column("Date", width=80, anchor="center")
        self.tree.heading("Party", text="Party Name"); self.tree.column("Party", width=150)
        self.tree.heading("Description", text="Items / Description"); self.tree.column("Description", width=350)
        self.tree.heading("Amount", text="Bill Amt"); self.tree.column("Amount", width=80, anchor="e")
        self.tree.heading("Status", text="Status"); self.tree.column("Status", width=80, anchor="center")
        
        self.tree.pack(fill="both", expand=True)
        
        # --- VISUAL STYLES ---
        self.tree.tag_configure('cleared', foreground="#95a5a6") # Gray text
        self.tree.tag_configure('pending', background="#fff9c4", foreground="#333") # Yellow background

        # Bottom Bar
        btn_frame = tk.Frame(self, bg="#0f172a", pady=6)
        btn_frame.pack(fill="x", side="bottom")
        
        # Action Buttons
        tk.Button(btn_frame, text="✓ SETTLE BILL [x]", bg="#ea580c", fg="white", font=("Segoe UI", 9, "bold"), relief="flat",
                  command=self.settle_selected).pack(side="left", padx=20)
                  
        tk.Button(btn_frame, text="Print Selected", bg="#16a34a", fg="white", relief="flat",
                  command=self.print_selected).pack(side="right", padx=20)

    def _select_index(self, idx):
        children = self.tree.get_children()
        if not children:
            return
        idx = max(0, min(idx, len(children) - 1))
        target = children[idx]
        self.tree.selection_set(target)
        self.tree.focus(target)
        self.tree.see(target)

    def move_selection_down(self, event=None):
        children = self.tree.get_children()
        if not children:
            return "break"
        sel = self.tree.selection()
        if not sel:
            self._select_index(0)
        else:
            current = children.index(sel[0])
            self._select_index(current + 1)
        self.tree.focus_set()
        return "break"

    def move_selection_up(self, event=None):
        children = self.tree.get_children()
        if not children:
            return "break"
        sel = self.tree.selection()
        if not sel:
            self._select_index(0)
        else:
            current = children.index(sel[0])
            self._select_index(current - 1)
        self.tree.focus_set()
        return "break"

    def _normalize_date(self, value):
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y"):
            try:
                return datetime.datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    def _to_amount(self, value):
        try:
            return float(str(value).replace(",", "").strip())
        except Exception:
            return None

    def parse_query(self, query_str):
        query = " ".join(query_str.lower().split())
        working = f" {query} "
        sql_parts = []
        params = []

        date_pat = r"(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4}|\d{2}\.\d{2}\.\d{4})"
        num_pat = r"(\d[\d,]*(?:\.\d+)?)"

        # Date range: 2026-03-01 to 2026-03-20, from X to Y
        date_range_pat = rf"(?:from\s+)?{date_pat}\s+(?:to|till|until|through)\s+{date_pat}"
        for m in re.finditer(date_range_pat, working):
            d1 = self._normalize_date(m.group(1))
            d2 = self._normalize_date(m.group(2))
            if d1 and d2:
                if d1 > d2:
                    d1, d2 = d2, d1
                sql_parts.append("date BETWEEN ? AND ?")
                params.extend([d1, d2])
        working = re.sub(date_range_pat, " ", working)

        # Amount range: between 5000 and 9000, 5000-9000
        between_amt_pat = rf"(?:amount|amt|price|rs|₹)?\s*(?:between)\s*{num_pat}\s*(?:and|to)\s*{num_pat}"
        for m in re.finditer(between_amt_pat, working):
            a1 = self._to_amount(m.group(1))
            a2 = self._to_amount(m.group(2))
            if a1 is not None and a2 is not None:
                low, high = (a1, a2) if a1 <= a2 else (a2, a1)
                sql_parts.append("amount BETWEEN ? AND ?")
                params.extend([low, high])
        working = re.sub(between_amt_pat, " ", working)

        dash_amt_pat = r"\b(\d{3,}(?:,\d{3})*(?:\.\d+)?)\s*-\s*(\d{3,}(?:,\d{3})*(?:\.\d+)?)\b"
        for m in re.finditer(dash_amt_pat, working):
            a1 = self._to_amount(m.group(1))
            a2 = self._to_amount(m.group(2))
            if a1 is not None and a2 is not None:
                low, high = (a1, a2) if a1 <= a2 else (a2, a1)
                sql_parts.append("amount BETWEEN ? AND ?")
                params.extend([low, high])
        working = re.sub(dash_amt_pat, " ", working)

        # Amount comparisons: > 9000, <=5000, above 2000, under 10000
        cmp_pat = rf"(?:amount|amt|price|rs|₹)?\s*(>=|<=|>|<|=)\s*{num_pat}"
        for m in re.finditer(cmp_pat, working):
            op = m.group(1)
            val = self._to_amount(m.group(2))
            if val is not None:
                sql_parts.append(f"amount {op} ?")
                params.append(val)
        working = re.sub(cmp_pat, " ", working)

        words_cmp = [
            (rf"(?:above|over|greater\s+than|more\s+than)\s*{num_pat}", ">"),
            (rf"(?:below|under|less\s+than)\s*{num_pat}", "<")
        ]
        for pattern, op in words_cmp:
            for m in re.finditer(pattern, working):
                val = self._to_amount(m.group(1))
                if val is not None:
                    sql_parts.append(f"amount {op} ?")
                    params.append(val)
            working = re.sub(pattern, " ", working)

        # Flow keywords
        has_out = re.search(r"\b(out|purchase|dr|debit)\b", working)
        has_in = re.search(r"\b(in|sale|cr|credit)\b", working)
        if has_out and not has_in:
            sql_parts.append("flow = ?")
            params.append("OUT")
        elif has_in and not has_out:
            sql_parts.append("flow = ?")
            params.append("IN")
        working = re.sub(r"\b(out|purchase|dr|debit|in|sale|cr|credit)\b", " ", working)

        # Status keywords
        if re.search(r"\b(pending|unpaid|due)\b", working):
            sql_parts.append("status = ?")
            params.append("Pending")
        elif re.search(r"\b(cleared|settled|paid)\b", working):
            sql_parts.append("status = ?")
            params.append("Cleared")
        working = re.sub(r"\b(pending|unpaid|due|cleared|settled|paid)\b", " ", working)

        # Single date(s)
        for m in re.finditer(date_pat, working):
            d = self._normalize_date(m.group(1))
            if d:
                sql_parts.append("date = ?")
                params.append(d)
        working = re.sub(date_pat, " ", working)

        # Remaining words as smart text terms across party + description
        cleaned = re.sub(r"[^a-z0-9\s]", " ", working)
        stop_words = {
            "and", "or", "the", "a", "an", "for", "with", "from", "to", "on",
            "date", "range", "price", "amount", "bill", "bills", "show", "search"
        }
        terms = [t for t in cleaned.split() if t and t not in stop_words and not t.isdigit()]

        for t in terms:
            sql_parts.append("(party_name LIKE ? OR description LIKE ?)")
            params.append(f"%{t}%")
            params.append(f"%{t}%")

        return sql_parts, params

    def run_smart_search(self, event=None):
        query = self.entry_search.get().strip()

        if query:
            where_clauses, params = self.parse_query(query)
            base_sql = "SELECT * FROM transactions"
            if where_clauses:
                base_sql += " WHERE " + " AND ".join(where_clauses)
            base_sql += " ORDER BY id DESC LIMIT 200"
        else:
            params = []
            base_sql = "SELECT * FROM transactions ORDER BY id DESC LIMIT 200"

        try:
            for i in self.tree.get_children(): self.tree.delete(i)
            
            self.db.cursor.execute(base_sql, tuple(params))
            rows = self.db.cursor.fetchall()
            self.found_rows = rows 
            
            for row in rows:
                r_id, r_date, r_party, r_desc, r_flow, r_amt = row[0], row[1], row[2], row[3], row[4], row[5]
                r_stat = row[6] if len(row) > 6 else "Pending"
                if r_stat is None: r_stat = "Pending"
                
                tag = 'cleared' if r_stat == 'Cleared' else 'pending'
                display_stat = "✓" if r_stat == 'Cleared' else "Pending"
                
                self.tree.insert("", "end", values=(r_id, r_date, r_party, r_desc, f"{r_amt:.2f}", display_stat), tags=(tag,))

            children = self.tree.get_children()
            if children:
                self._select_index(0)
                
        except Exception as e:
            print(e) 

    def open_selected_bill(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return "break"

        item_vals = self.tree.item(sel[0])['values']
        sel_id = item_vals[0]

        data = next((r for r in self.found_rows if r[0] == sel_id), None)
        if not data:
            return "break"

        status = data[6] if len(data) > 6 and data[6] else "Pending"
        bill_id = data[0]

        if status == "Cleared":
            self.destroy()
            self.master.show_settled_view(focus_bill_id=bill_id, auto_open_bill=True)
        else:
            self.destroy()
            popup = bill_entry.BillEntryPage(self.master, self.master, self.db, bill_id=bill_id)
            popup.transient(self.master)
            popup.grab_set()

        return "break"

    def print_selected(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        
        item_vals = self.tree.item(sel[0])['values']
        sel_id = item_vals[0]
        
        data = next((r for r in self.found_rows if r[0] == sel_id), None)
        if data:
            printer.generate_invoice(data[1], data[2], data[3], data[5], data[4])

    def settle_selected(self, event=None):
        """Marks the selected bill as Cleared and refreshes the view."""
        sel = self.tree.selection()
        if not sel: return
        
        # Confirm action
        if not messagebox.askyesno("Settle", "Mark selected bill as Paid/Settled?"):
            return

        try:
            for item in sel:
                vals = self.tree.item(item)['values']
                bill_id = vals[0]
                
                # Update DB
                self.db.cursor.execute("UPDATE transactions SET status='Cleared' WHERE id=?", (bill_id,))
            
            self.db.conn.commit()
            
            # Refresh the search to show the new gray status
            self.run_smart_search()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not update status: {e}")