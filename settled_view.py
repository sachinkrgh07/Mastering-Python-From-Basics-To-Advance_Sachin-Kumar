import tkinter as tk
from tkinter import ttk, messagebox
import printer 

class SettledViewPage(tk.Frame):
    def __init__(self, parent, controller, db_manager, focus_bill_id=None, auto_open_bill=False):
        super().__init__(parent)
        self.controller = controller
        self.db = db_manager
        self.focus_bill_id = focus_bill_id
        self.auto_open_bill = auto_open_bill
        self.configure(bg="#f5f7fb")
        
        self.setup_ui()
        self.load_data()
        
        self.bind_all_keys()
        self.bind("<Destroy>", self.cleanup_shortcuts)
        self.after(100, self.focus_search)
        self.after(150, self._focus_requested_bill)

    def bind_all_keys(self):
        self.controller.bind("<i>", self.focus_search)
        self.controller.bind("<Control-f>", self.focus_search)
        self.controller.bind("<Control-p>", self.trigger_print_popup)
        self.controller.bind("<Alt-r>", self.trigger_revert)

    def cleanup_shortcuts(self, event):
        if event.widget == self:
            try:
                self.controller.unbind("<i>")
                self.controller.unbind("<Control-f>")
                self.controller.unbind("<Control-p>")
                self.controller.unbind("<Alt-r>")
            except: pass

    def focus_search(self, event=None):
        try: self.entry_search.focus_set()
        except: pass
    def trigger_print_popup(self, event=None):
        try: self.open_print_popup()
        except: pass
    def trigger_revert(self, event=None):
        try: self.revert_status()
        except: pass

    def setup_ui(self):
        header_frame = tk.Frame(self, bg="#334155", height=60)
        header_frame.pack(fill="x")
        tk.Button(header_frame, text="< Menu (Esc)", bg="#1d4ed8", fg="white", relief="flat", command=self.controller.show_main_menu).pack(side="left", padx=10)
        tk.Label(header_frame, text="ARCHIVE (Settled)", bg="#334155", fg="white", font=("Segoe UI", 16, "bold")).pack(side="left")
        tk.Button(header_frame, text="🖨 Print (Ctrl+P)", bg="#2563eb", fg="white", relief="flat", command=self.open_print_popup).pack(side="right", padx=20)

        search_frame = tk.Frame(self, bg="#e2e8f0", pady=10)
        search_frame.pack(fill="x")
        tk.Label(search_frame, text="Search [i]:", bg="#e2e8f0").pack(side="left", padx=10)
        self.entry_search = ttk.Entry(search_frame, width=40); self.entry_search.pack(side="left")
        self.entry_search.bind("<KeyRelease>", self.search_data)
        self.entry_search.bind("<Down>", lambda e: self.tree.focus_set())

        action_frame = tk.Frame(self, bg="#f5f7fb", pady=5)
        action_frame.pack(fill="x", padx=10)
        tk.Button(action_frame, text="↺ REVERT [Alt+R]", bg="#d97706", fg="white", relief="flat", command=self.revert_status).pack(side="right")

        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        sc = ttk.Scrollbar(list_frame)
        sc.pack(side="right", fill="y")
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Date", "Party", "Amount"), show="headings", yscrollcommand=sc.set)
        sc.config(command=self.tree.yview)
        style = ttk.Style()
        style.configure("Archive.Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure("Archive.Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0", foreground="#111827")
        self.tree.configure(style="Archive.Treeview")
        for c in ("ID", "Date", "Party", "Amount"): self.tree.heading(c, text=c)
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure('cleared', foreground="gray")
        self.tree.bind("<Double-1>", self.open_selected_bill)
        self.tree.bind("<Return>", self.open_selected_bill)
        self.tree.bind("<Delete>", lambda e: self.revert_status())
        self.tree.bind("<r>", lambda e: self.revert_status())
        self.tree.bind("<p>", lambda e: self.open_print_popup())
        self.tree.bind("<Control-a>", self.select_all_rows)

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        self.db.cursor.execute("SELECT * FROM transactions WHERE status='Cleared' ORDER BY id DESC")
        for r in self.db.cursor.fetchall():
            self.tree.insert("", "end", values=(r[0], r[1], r[2], f"{r[5]:.2f}"), tags=('cleared',))

    def search_data(self, event):
        q = self.entry_search.get()
        self.db.cursor.execute("SELECT * FROM transactions WHERE status='Cleared' AND party_name LIKE ? ORDER BY id DESC", ('%'+q+'%',))
        rows = self.db.cursor.fetchall()
        for r in self.tree.get_children(): self.tree.delete(r)
        for r in rows: self.tree.insert("", "end", values=(r[0], r[1], r[2], f"{r[5]:.2f}"), tags=('cleared',))

    def _focus_requested_bill(self):
        if not self.focus_bill_id:
            return

        target = None
        for iid in self.tree.get_children():
            vals = self.tree.item(iid)['values']
            if vals and vals[0] == self.focus_bill_id:
                target = iid
                break

        if target:
            self.tree.selection_set(target)
            self.tree.focus(target)
            self.tree.see(target)
            if self.auto_open_bill:
                self.after(120, self.open_selected_bill)

    def open_selected_bill(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return "break"

        bill_id = self.tree.item(sel[0])['values'][0]
        self.db.cursor.execute("SELECT * FROM transactions WHERE id=?", (bill_id,))
        row = self.db.cursor.fetchone()
        if not row:
            return "break"

        popup = tk.Toplevel(self)
        popup.title(f"Archived Bill #{bill_id}")
        popup.geometry("620x370")
        popup.configure(bg="#f7f7f7")
        popup.transient(self.controller)
        popup.grab_set()
        popup.bind("<Escape>", lambda e: popup.destroy())

        flow_label = "Sale (IN)" if row[4] == "IN" else "Purchase (OUT)"
        phone = row[7] if len(row) > 7 and row[7] else "-"
        addr = row[8] if len(row) > 8 and row[8] else "-"

        tk.Label(popup, text=f"Archived Bill #{bill_id}", font=("Segoe UI", 15, "bold"),
                 bg="#f7f7f7", fg="#263238").pack(pady=(14, 6))

        info = tk.Frame(popup, bg="#f7f7f7")
        info.pack(fill="x", padx=18)
        tk.Label(info, text=f"Date: {row[1]}", bg="#f7f7f7", anchor="w").pack(fill="x")
        tk.Label(info, text=f"Party: {row[2]}", bg="#f7f7f7", anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x")
        tk.Label(info, text=f"Type: {flow_label}", bg="#f7f7f7", anchor="w").pack(fill="x")
        tk.Label(info, text=f"Amount: Rs {row[5]:,.2f}", bg="#f7f7f7", anchor="w", fg="#1b5e20",
                 font=("Segoe UI", 10, "bold")).pack(fill="x")
        tk.Label(info, text=f"Phone: {phone}", bg="#f7f7f7", anchor="w").pack(fill="x")
        tk.Label(info, text=f"Address: {addr}", bg="#f7f7f7", anchor="w").pack(fill="x")

        tk.Label(popup, text="Description", bg="#f7f7f7", anchor="w", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=18, pady=(10, 2))
        desc_box = tk.Text(popup, height=7, wrap="word", font=("Consolas", 10))
        desc_box.pack(fill="both", expand=True, padx=18)
        desc_box.insert("1.0", row[3] if row[3] else "")
        desc_box.config(state="disabled")

        btns = tk.Frame(popup, bg="#f7f7f7")
        btns.pack(fill="x", padx=18, pady=12)

        def do_print():
            popup.destroy()
            printer.generate_invoice(row[1], row[2], row[3], row[5], row[4])

        tk.Button(btns, text="Print", bg="#1976d2", fg="white", padx=12, command=do_print).pack(side="left")
        tk.Button(btns, text="Close", command=popup.destroy, padx=12).pack(side="right")

        return "break"

    def select_all_rows(self, event=None):
        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children)
            self.tree.focus(children[0])
        return "break"

    def revert_status(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Revert", "Move back to Active?"):
            for s in sel:
                bid = self.tree.item(s)['values'][0]
                self.db.cursor.execute("UPDATE transactions SET status='Pending' WHERE id=?", (bid,))
            self.db.conn.commit()
            self.load_data()

    def open_print_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Print Archived")
        popup.geometry("600x400")
        
        # --- FIX: TRAP ESCAPE ---
        def close_me(e=None):
            popup.destroy()
            return "break"
        
        popup.bind("<Escape>", close_me)
        popup.transient(self)
        popup.grab_set()
        
        tk.Label(popup, text="Search Archive:").pack(pady=5)
        search = ttk.Entry(popup, width=40); search.pack(); search.focus()
        res = ttk.Treeview(popup, columns=("ID", "Date", "Desc", "Amt"), show="headings")
        for c in ("ID", "Date", "Desc", "Amt"): res.heading(c, text=c)
        res.pack(fill="both", expand=True)
        
        found = []
        def run(e=None):
            q = search.get()
            for i in res.get_children(): res.delete(i)
            # ONLY CLEARED
            self.db.cursor.execute("SELECT * FROM transactions WHERE status='Cleared' AND party_name LIKE ? ORDER BY id DESC", ('%'+q+'%',))
            rows = self.db.cursor.fetchall()
            found.clear(); found.extend(rows)
            for r in rows: res.insert("", "end", values=(r[0], r[1], r[3], r[5]))
            if rows: child=res.get_children()[0]; res.selection_set(child); res.focus(child)

        def prt(e=None):
            sel = res.selection()
            if not sel: return
            val = res.item(sel[0])['values']
            data = next((r for r in found if r[0] == val[0]), None)
            if data: 
                popup.destroy()
                printer.generate_invoice(data[1], data[2], data[3], data[5], data[4])

        search.bind("<KeyRelease>", run); search.bind("<Down>", lambda e: res.focus_set()); res.bind("<Return>", prt)
        tk.Button(popup, text="Print Selected", command=prt).pack(pady=10)