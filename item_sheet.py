import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import sqlite3

class ItemSheetPage(tk.Frame):
    def __init__(self, parent, controller, db_manager):
        super().__init__(parent)
        self.controller = controller
        self.db = db_manager
        self.configure(bg="#f0f0f0")
        self.setup_ui()
        self.load_items()
        self.after(100, self.entry_name.focus_set)
        self.bind_all_keys()
        self.bind("<Destroy>", self.cleanup_shortcuts)

    def bind_all_keys(self):
        self.controller.bind("<Control-f>", self.focus_item_name)
        self.controller.bind("<Control-i>", self.trigger_import)

    def cleanup_shortcuts(self, event):
        if event.widget == self:
            try:
                self.controller.unbind("<Control-f>")
                self.controller.unbind("<Control-i>")
            except:
                pass

    def focus_item_name(self, event=None):
        try:
            self.entry_name.focus_set()
            self.entry_name.selection_range(0, tk.END)
        except:
            pass

    def trigger_import(self, event=None):
        try:
            self.import_csv()
        except:
            pass

    def setup_ui(self):
        h = tk.Frame(self, bg="#607d8b", height=60); h.pack(fill="x")
        tk.Button(h, text="< Menu (Esc)", bg="#455a64", fg="white", command=self.controller.show_main_menu).pack(side="left", padx=10)
        tk.Label(h, text="ITEM MASTER", bg="#607d8b", fg="white", font=("Arial", 16, "bold")).pack(side="left")

        c = tk.Frame(self, bg="white", pady=15); c.pack(fill="x", padx=10, pady=10)
        self.entry_name = ttk.Entry(c, width=20); self.entry_name.pack(side="left", padx=5)
        self.entry_rate = ttk.Entry(c, width=10); self.entry_rate.pack(side="left", padx=5)
        tk.Button(c, text="Add (Enter)", bg="#4CAF50", fg="white", command=self.add_single_item).pack(side="left")
        tk.Button(c, text="Import CSV", bg="#2196F3", fg="white", command=self.import_csv).pack(side="right")

        # Arrow Nav
        self.entry_name.bind("<Return>", lambda e: self.entry_rate.focus())
        self.entry_name.bind("<Down>", lambda e: self.entry_rate.focus())
        self.entry_name.bind("<Right>", lambda e: self.entry_rate.focus())
        
        self.entry_rate.bind("<Return>", lambda e: self.add_single_item())
        self.entry_rate.bind("<Up>", lambda e: self.entry_name.focus())
        self.entry_rate.bind("<Left>", lambda e: self.entry_name.focus())

        l = tk.Frame(self, bg="white"); l.pack(fill="both", expand=True, padx=10)
        self.tree = ttk.Treeview(l, columns=("ID", "Name", "Rate"), show="headings")
        self.tree.heading("ID", text="ID"); self.tree.heading("Name", text="Item"); self.tree.heading("Rate", text="Rate")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Delete>", self.delete_item)

    def load_items(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        self.db.cursor.execute("SELECT * FROM items ORDER BY item_name")
        for r in self.db.cursor.fetchall(): self.tree.insert("", "end", values=r)

    def add_single_item(self):
        n, r = self.entry_name.get(), self.entry_rate.get()
        if n and r:
            try:
                self.db.cursor.execute("INSERT INTO items (item_name, rate) VALUES (?, ?)", (n, float(r)))
                self.db.conn.commit(); self.load_items(); self.entry_name.delete(0, tk.END); self.entry_rate.delete(0, tk.END); self.entry_name.focus()
            except: messagebox.showerror("Error", "Check data")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if path:
            try:
                with open(path, newline='', encoding='utf-8') as f:
                    for row in csv.reader(f):
                        if len(row)>=2: 
                            try: self.db.cursor.execute("INSERT INTO items (item_name, rate) VALUES (?, ?)", (row[0], float(row[1])))
                            except: pass
                self.db.conn.commit(); self.load_items()
            except Exception as e: messagebox.showerror("Error", str(e))

    def delete_item(self, event):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Delete", "Delete Item?"):
            self.db.cursor.execute("DELETE FROM items WHERE id=?", (self.tree.item(sel[0])['values'][0],))
            self.db.conn.commit(); self.load_items()