import tkinter as tk
from tkinter import ttk, messagebox
import printer
import bill_entry  # Reuse BillEntryPage for edit mode


class ViewEditPage(tk.Frame):
    def __init__(self, parent, controller, db_manager):
        super().__init__(parent)
        self.controller = controller
        self.db = db_manager
        self.configure(bg="#f5f7fb")
        self.all_rows = []
        self._sort_state = {}

        self.setup_ui()
        self.load_data()
        self.bind_all_keys()
        self.bind("<Destroy>", self.cleanup_shortcuts)
        self.after(100, self.focus_search)

    def bind_all_keys(self):
        self.controller.bind("<e>", self.trigger_edit)
        self.controller.bind("<i>", self.focus_search)
        self.controller.bind("<Control-f>", self.focus_search)
        self.controller.bind("<Control-p>", self.trigger_print)

    def cleanup_shortcuts(self, event):
        if event.widget == self:
            try:
                self.controller.unbind("<e>")
                self.controller.unbind("<i>")
                self.controller.unbind("<Control-f>")
                self.controller.unbind("<Control-p>")
            except:
                pass

    def focus_search(self, event=None):
        try:
            self.entry_search.focus_set()
        except:
            pass

    def trigger_edit(self, event=None):
        try:
            self.open_edit_bill()
        except:
            pass

    def trigger_print(self, event=None):
        try:
            self.open_print_popup()
        except:
            pass

    def setup_ui(self):
        # ── HEADER ──────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#1e3a8a", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Button(
            header, text="< Menu (Esc)", bg="#1d4ed8", fg="white",
            font=("Segoe UI", 10), relief="flat", padx=12, pady=8,
            command=self.controller.show_main_menu
        ).pack(side="left", padx=8, pady=8)

        tk.Label(
            header, text="PENDING BILLS",
            bg="#1e3a8a", fg="white", font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=10)

        btn_frame = tk.Frame(header, bg="#1e3a8a")
        btn_frame.pack(side="right", padx=10, pady=8)

        tk.Button(
            btn_frame, text="Edit [E]", bg="#d97706", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=6,
            command=self.open_edit_bill
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Print [Ctrl+P]", bg="#2563eb", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=6,
            command=self.open_print_popup
        ).pack(side="left", padx=4)

        tk.Button(
            btn_frame, text="Settle [Del]", bg="#15803d", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", padx=10, pady=6,
            command=self.settle_bill
        ).pack(side="left", padx=4)

        # ── SEARCH BAR ──────────────────────────────────────────────────────
        bar = tk.Frame(self, bg="#e2e8f0", pady=8, padx=12)
        bar.pack(fill="x")

        tk.Label(bar, text="Search [i]:", bg="#e2e8f0",
                 font=("Segoe UI", 10)).pack(side="left")
        self.entry_search = ttk.Entry(bar, width=35, font=("Segoe UI", 10))
        self.entry_search.pack(side="left", padx=(4, 20))
        self.entry_search.bind("<KeyRelease>", self.search_data)
        self.entry_search.bind("<Down>", lambda e: self.tree.focus_set())
        self.entry_search.bind("<Return>", lambda e: self.tree.focus_set())

        tk.Label(bar, text="Filter:", bg="#e2e8f0", font=("Segoe UI", 10)).pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(
            bar, textvariable=self.filter_var,
            values=["All", "Sale (IN)", "Purchase (OUT)"],
            width=14, state="readonly", font=("Segoe UI", 10)
        )
        filter_combo.pack(side="left", padx=(4, 20))
        filter_combo.bind("<<ComboboxSelected>>", self.search_data)

        self.lbl_total_dr = tk.Label(bar, text="", bg="#e2e8f0",
                                     font=("Segoe UI", 9, "bold"), fg="#b71c1c")
        self.lbl_total_dr.pack(side="right", padx=6)

        self.lbl_total_cr = tk.Label(bar, text="", bg="#e2e8f0",
                                     font=("Segoe UI", 9, "bold"), fg="#1b5e20")
        self.lbl_total_cr.pack(side="right", padx=6)

        self.lbl_count = tk.Label(bar, text="", bg="#e2e8f0",
                                  font=("Segoe UI", 9), fg="#333")
        self.lbl_count.pack(side="right", padx=10)

        # ── TREEVIEW ────────────────────────────────────────────────────────
        table_frame = tk.Frame(self, bg="white")
        table_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        style = ttk.Style()
        style.configure("Pending.Treeview",
                font=("Segoe UI", 10), rowheight=30, borderwidth=0)
        style.configure("Pending.Treeview.Heading",
                font=("Segoe UI", 10, "bold"), background="#e2e8f0", foreground="#111827")
        style.map("Pending.Treeview",
                  background=[("selected", "#1565c0")],
                  foreground=[("selected", "white")])

        cols = ("ID", "Date", "Party", "Description", "Flow", "Amount")
        self.tree = ttk.Treeview(
            table_frame, columns=cols, show="headings",
            style="Pending.Treeview", selectmode="extended"
        )

        self.tree.column("ID",          width=55,  anchor="center", stretch=False)
        self.tree.column("Date",        width=100, anchor="center", stretch=False)
        self.tree.column("Party",       width=200, anchor="w")
        self.tree.column("Description", width=450, anchor="w")
        self.tree.column("Flow",        width=100, anchor="center", stretch=False)
        self.tree.column("Amount",      width=120, anchor="e",      stretch=False)

        for c in cols:
            self.tree.heading(c, text=c, command=lambda _c=c: self.sort_by(_c))

        self.tree.tag_configure("sale",     foreground="#1a237e")
        self.tree.tag_configure("purchase", foreground="#b71c1c")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.open_edit_bill)
        self.tree.bind("<Return>",   self.open_edit_bill)
        self.tree.bind("<Delete>",   self.settle_bill)
        self.tree.bind("<p>",        self.open_print_popup)
        self.tree.bind("<Control-a>", self.select_all_rows)

        # Status bar
        status = tk.Frame(self, bg="#eef2ff", height=26)
        status.pack(fill="x", side="bottom")
        tk.Label(
            status,
            text="  Double-click or [E] to edit  |  [Del] to settle  |  [Ctrl+P] to print",
            bg="#eef2ff", fg="#475569", font=("Segoe UI", 8), anchor="w"
        ).pack(fill="x", padx=8)

    # ── SORT ─────────────────────────────────────────────────────────────────
    def sort_by(self, col):
        reverse = self._sort_state.get(col, False)
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            data.sort(key=lambda t: float(t[0].replace(",", "")), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for i, (_, k) in enumerate(data):
            self.tree.move(k, "", i)
        self._sort_state[col] = not reverse

    # ── DATA ─────────────────────────────────────────────────────────────────
    def load_data(self):
        self.db.cursor.execute(
            "SELECT id, date, party_name, description, flow, amount "
            "FROM transactions WHERE status='Pending' ORDER BY id DESC"
        )
        self.all_rows = self.db.cursor.fetchall()
        self._populate(self.all_rows)

    def _populate(self, rows):
        for r in self.tree.get_children():
            self.tree.delete(r)

        total_cr = total_dr = 0.0
        for r in rows:
            rid, date, party, desc, flow, amt = r
            flow_label = "IN (Sale)" if flow == "IN" else "OUT (Purch)"
            tag = "sale" if flow == "IN" else "purchase"
            short_desc = desc[:65] + "..." if len(str(desc)) > 65 else desc
            self.tree.insert(
                "", "end",
                values=(rid, date, party, short_desc, flow_label, f"{amt:,.2f}"),
                tags=(tag,)
            )
            if flow == "IN":
                total_cr += amt
            else:
                total_dr += amt

        count = len(rows)
        self.lbl_count.config(text=f"{count} bill{'s' if count != 1 else ''}")
        self.lbl_total_cr.config(text=f"CR {total_cr:,.2f}")
        self.lbl_total_dr.config(text=f"DR {total_dr:,.2f}")

        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self.tree.focus(children[0])

    def search_data(self, event=None):
        q = self.entry_search.get().strip().lower()
        flow_filter = self.filter_var.get()

        filtered = []
        for r in self.all_rows:
            rid, date, party, desc, flow, amt = r
            text_match = (
                q == "" or
                q in str(party).lower() or
                q in str(desc).lower() or
                q in str(rid) or
                q in str(date)
            )
            if flow_filter == "Sale (IN)" and flow != "IN":
                continue
            if flow_filter == "Purchase (OUT)" and flow != "OUT":
                continue
            if text_match:
                filtered.append(r)

        self._populate(filtered)

    def select_all_rows(self, event=None):
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children)
            self.tree.focus(children[0])
        return "break"

    # ── ACTIONS ──────────────────────────────────────────────────────────────
    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a bill first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def _get_selected_ids(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select bill(s) first.")
            return []
        return [self.tree.item(s)["values"][0] for s in sel]

    def open_edit_bill(self, event=None):
        """Open bill_entry.BillEntryPage in edit mode for the selected bill."""
        bid = self._get_selected_id()
        if bid is None:
            return
        popup = bill_entry.BillEntryPage(
            self.controller, self, self.db, bill_id=bid
        )
        popup.transient(self.controller)
        popup.grab_set()

    def settle_bill(self, event=None):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select a bill to settle.")
            return
        ids = [self.tree.item(s)["values"][0] for s in sel]
        count = len(ids)
        if not messagebox.askyesno(
            "Confirm", f"Mark {count} bill{'s' if count > 1 else ''} as Cleared?"
        ):
            return
        for bid in ids:
            self.db.cursor.execute(
                "UPDATE transactions SET status='Cleared' WHERE id=?", (bid,)
            )
        self.db.conn.commit()
        self.load_data()

    def open_print_popup(self, event=None):
        ids = self._get_selected_ids()
        if not ids:
            return

        placeholders = ",".join(["?"] * len(ids))
        self.db.cursor.execute(
            f"SELECT * FROM transactions WHERE id IN ({placeholders}) ORDER BY id",
            tuple(ids)
        )
        rows = self.db.cursor.fetchall()
        if not rows:
            return

        parties = {r[2] for r in rows}
        if len(parties) > 1:
            messagebox.showwarning(
                "Different Customers",
                "Please select bills of the same customer to print together."
            )
            return

        party_name = rows[0][2]
        total_amount = sum(float(r[5]) for r in rows)
        first_id = rows[0][0]
        last_id = rows[-1][0]

        popup = tk.Toplevel(self)
        popup.title("Print Bills")
        popup.geometry("480x260")
        popup.configure(bg="#f5f5f5")
        popup.transient(self.controller)
        popup.grab_set()
        popup.bind("<Escape>", lambda e: popup.destroy())

        tk.Label(popup, text=f"{len(rows)} Bill(s)", font=("Segoe UI", 14, "bold"),
                 bg="#f5f5f5").pack(pady=(20, 4))
        tk.Label(popup, text=f"Party  : {party_name}", font=("Segoe UI", 11),
                 bg="#f5f5f5").pack()
        tk.Label(popup, text=f"Bill IDs: {first_id} - {last_id}", font=("Segoe UI", 10),
                 bg="#f5f5f5", fg="#555").pack()
        tk.Label(popup, text=f"Amount : Rs {total_amount:,.2f}",
                 font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="#1b5e20").pack(pady=4)
        tk.Label(popup, text="Each selected bill will open in print preview.",
                 bg="#f5f5f5", fg="#555").pack()

        def do_print():
            for row in rows:
                printer.generate_invoice(row[1], row[2], row[3], row[5], row[4])
            popup.destroy()

        tk.Button(
            popup, text="Print Selected", bg="#1976d2", fg="white",
            font=("Segoe UI", 11, "bold"), padx=20, pady=8, command=do_print
        ).pack(pady=15)
        tk.Button(popup, text="Cancel", command=popup.destroy).pack()
        popup.bind("<Return>", lambda e: do_print())
