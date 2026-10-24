import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import re
import printer 

class BillEntryPage(tk.Toplevel):
    def __init__(self, parent, controller, db_manager, bill_id=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db_manager
        self.edit_bill_id = bill_id 
        
        mode_title = f"EDIT INVOICE #{bill_id}" if bill_id else "NEW INVOICE"
        self.title(mode_title)
        self.configure(bg="#3c3c3c")
        self.transient(parent)
        self.grab_set()
        
        # Maximize
        try: self.state('zoomed')
        except: self.geometry("1200x800")

        self.current_cart = [] 
        self.full_item_list = [] 
        self.item_rates = {}
        self.full_party_list = []
        self.current_flow = "IN" # Default to Sale
        
        self.load_data_masters()
        self.setup_ui()
        
        # Load Data if Editing
        if self.edit_bill_id:
            self.load_existing_bill()
        else:
            self.update_flow_buttons() # Set default colors
        
        # Shortcuts
        self.bind("<Alt-c>", self.quick_create_item)
        self.bind("<Control-s>", self.save_shortcut)
        self.bind("<Control-f>", lambda e: self.entry_customer.focus_set())
        
        # --- FIX: TRAP ESCAPE KEY ---
        def close_me(event=None):
            self.destroy()
            return "break" # Stops event from reaching Main Window
        
        self.bind("<Escape>", close_me)

    def load_data_masters(self):
        try:
            self.db.cursor.execute("SELECT item_name, rate FROM items")
            rows = self.db.cursor.fetchall()
            self.full_item_list = [row[0] for row in rows]
            self.item_rates = {row[0]: row[1] for row in rows}
            self.db.cursor.execute("SELECT DISTINCT party_name FROM transactions ORDER BY party_name")
            self.full_party_list = [r[0] for r in self.db.cursor.fetchall()]
        except Exception: pass 

    def load_existing_bill(self):
        try:
            self.db.cursor.execute("SELECT * FROM transactions WHERE id=?", (self.edit_bill_id,))
            row = self.db.cursor.fetchone()
            if not row: return
            
            # 0:id, 1:date, 2:party, 3:desc, 4:flow, 5:amt, 6:status, 7:phone, 8:addr
            r_date, r_party, r_desc, r_flow, r_phone, r_addr = row[1], row[2], row[3], row[4], row[7], row[8]
            
            self.current_flow = r_flow
            self.update_flow_buttons()
            
            self.entry_customer.set(r_party)
            self.entry_date.delete(0, tk.END); self.entry_date.insert(0, r_date)
            self.entry_phone.delete(0, tk.END); self.entry_phone.insert(0, r_phone)
            self.entry_address.delete(0, tk.END); self.entry_address.insert(0, r_addr)
            
            clean_desc = r_desc.replace("[SALE]", "").replace("[PURCH]", "").strip()
            parts = clean_desc.split("|")
            items_str = parts[0]
            
            tax_val = "0"; frgt_val = "0"
            for p in parts[1:]:
                if "Tax:" in p: tax_val = p.replace("Tax:", "").replace("%", "").strip()
                if "Frgt:" in p: frgt_val = p.split(":")[1].strip()
            
            self.final_tax_pct.delete(0, tk.END); self.final_tax_pct.insert(0, tax_val)
            self.final_freight.delete(0, tk.END); self.final_freight.insert(0, frgt_val)
            
            item_pattern = re.compile(r"(.*)\s*\(\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*\)")
            for r_item in items_str.split(","):
                match = item_pattern.search(r_item.strip())
                if match:
                    name = match.group(1).strip()
                    qty = float(match.group(2))
                    rate = float(match.group(3))
                    sub = qty * rate
                    self.current_cart.append({"item": name, "qty": qty, "rate": rate, "subtotal": sub})
                    sr_no = len(self.tree.get_children()) + 1
                    self.tree.insert("", "end", values=(sr_no, name, qty, rate, f"{sub:.2f}"))
            
            self.recalculate_grand_total()
            
        except Exception as e:
            messagebox.showerror("Load Error", str(e))

    def update_flow_buttons(self):
        if self.current_flow == "IN":
            self.btn_cr.config(bg="#27ae60", relief="sunken", text="✅ SALE (Active)")
            self.btn_dr.config(bg="#95a5a6", relief="raised", text="Purchase (Out)")
        else:
            self.btn_cr.config(bg="#95a5a6", relief="raised", text="Sale (In)")
            self.btn_dr.config(bg="#c0392b", relief="sunken", text="✅ PURCHASE (Active)")

    def set_flow(self, flow):
        self.current_flow = flow
        self.update_flow_buttons()

    def setup_ui(self):
        paper_frame = tk.Frame(self, bg="white", padx=20, pady=20)
        paper_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- HEADER ---
        header = tk.Frame(paper_frame, bg="white")
        header.pack(fill="x", pady=(0, 10))
        
        tk.Label(header, text="Bill To:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.entry_customer = ttk.Combobox(header, font=("Segoe UI", 11), width=40, values=self.full_party_list)
        self.entry_customer.grid(row=0, column=1, padx=10, sticky="w")
        
        tk.Label(header, text="Date:", bg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, sticky="e", padx=(40, 5))
        self.entry_date = tk.Entry(header, width=15, font=("Segoe UI", 11), bg="#f0f0f0", bd=1)
        self.entry_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.entry_date.grid(row=0, column=3, sticky="e")

        tk.Label(header, text="Phone:", bg="white", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_phone = tk.Entry(header, width=42, font=("Segoe UI", 10), bg="#fafafa", bd=1)
        self.entry_phone.grid(row=1, column=1, padx=10, sticky="w", pady=5)

        tk.Label(header, text="Address:", bg="white", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
        self.entry_address = tk.Entry(header, width=42, font=("Segoe UI", 10), bg="#fafafa", bd=1)
        self.entry_address.grid(row=2, column=1, padx=10, sticky="w", pady=2)

        tk.Frame(paper_frame, bg="#333", height=2).pack(fill="x", pady=10)

        # --- ENTRY STRIP ---
        inp = tk.Frame(paper_frame, bg="#e0e0e0", pady=5, padx=5, relief="solid", bd=1)
        inp.pack(fill="x")
        
        tk.Label(inp, text="ITEM NAME", bg="#e0e0e0", font=("Arial", 8)).pack(side="left", padx=5)
        self.entry_item = ttk.Combobox(inp, font=("Segoe UI", 11), width=40, values=self.full_item_list)
        self.entry_item.pack(side="left", padx=2)
        
        tk.Label(inp, text="QTY", bg="#e0e0e0", font=("Arial", 8)).pack(side="left", padx=(10, 2))
        self.entry_qty = tk.Entry(inp, width=8, font=("Segoe UI", 11), justify="center")
        self.entry_qty.pack(side="left", padx=2)
        
        tk.Label(inp, text="RATE", bg="#e0e0e0", font=("Arial", 8)).pack(side="left", padx=(10, 2))
        self.entry_rate = tk.Entry(inp, width=10, font=("Segoe UI", 11), justify="right")
        self.entry_rate.pack(side="left", padx=2)
        
        tk.Button(inp, text="Add ↵", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), command=self.add_to_cart).pack(side="left", padx=15)

        # --- LIST ---
        lf = tk.Frame(paper_frame, bg="white"); lf.pack(fill="both", expand=True, pady=5)
        cols = ("SR", "Item Name", "Qty", "Rate", "Total")
        self.tree = ttk.Treeview(lf, columns=cols, show="headings", height=15)
        self.tree.column("SR", width=40, anchor="center")
        self.tree.column("Item Name", width=400, anchor="w")
        self.tree.column("Qty", width=80, anchor="center")
        self.tree.column("Rate", width=100, anchor="center")
        self.tree.column("Total", width=120, anchor="e")
        for c in cols: self.tree.heading(c, text=c)
        self.tree.pack(side="left", fill="both", expand=True)
        sc = ttk.Scrollbar(lf, command=self.tree.yview); self.tree.configure(yscrollcommand=sc.set); sc.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self.remove_item_from_list)
        self.tree.bind("<Delete>", self.remove_item_from_list)

        # --- FOOTER ---
        foot = tk.Frame(paper_frame, bg="#eee", height=100, pady=10, padx=10, relief="sunken", bd=1)
        foot.pack(fill="x", side="bottom", pady=(10, 0))

        bf = tk.Frame(foot, bg="#eee"); bf.pack(side="left")
        
        # Payment Buttons (Updates 'current_flow' variable)
        self.btn_cr = tk.Button(bf, text="SALE (In)", font=("Segoe UI", 10, "bold"), width=15, 
                                command=lambda: self.set_flow("IN"))
        self.btn_cr.pack(side="left", padx=5)
        
        self.btn_dr = tk.Button(bf, text="PURCHASE (Out)", font=("Segoe UI", 10, "bold"), width=15,
                                command=lambda: self.set_flow("OUT"))
        self.btn_dr.pack(side="left", padx=5)

        tf = tk.Frame(foot, bg="#eee"); tf.pack(side="right")
        tk.Label(tf, text="Freight:", bg="#eee").grid(row=0, column=0, sticky="e")
        self.final_freight = tk.Entry(tf, width=10, font=("Consolas", 10), justify="right"); self.final_freight.insert(0,"0"); self.final_freight.grid(row=0, column=1, padx=5)
        tk.Label(tf, text="Tax %:", bg="#eee").grid(row=1, column=0, sticky="e")
        self.final_tax_pct = tk.Entry(tf, width=10, font=("Consolas", 10), justify="right"); self.final_tax_pct.insert(0,"0"); self.final_tax_pct.grid(row=1, column=1, padx=5)
        
        tk.Frame(tf, bg="#aaa", height=1).grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        self.lbl_total = tk.Label(tf, text="0.00", bg="#eee", font=("Segoe UI", 16, "bold"), fg="#2c3e50"); self.lbl_total.grid(row=3, column=1, sticky="e")
        
        # SAVE BUTTON
        save_lbl = "UPDATE BILL" if self.edit_bill_id else "SAVE BILL"
        self.btn_save = tk.Button(tf, text=save_lbl, bg="#2980b9", fg="white", font=("Segoe UI", 10, "bold"), 
                                  command=self.finalize_bill)
        self.btn_save.grid(row=4, column=1, pady=10)

        # --- BINDINGS ---
        self.apply_focus(self.entry_customer); self.apply_focus(self.entry_phone); self.apply_focus(self.entry_address); self.apply_focus(self.entry_date)
        self.apply_focus(self.entry_item); self.apply_focus(self.entry_qty); self.apply_focus(self.entry_rate)
        self.apply_focus(self.final_freight); self.apply_focus(self.final_tax_pct)

        # Nav Chain
        self.entry_customer.bind("<Return>", self.on_customer_enter)
        self.entry_customer.bind("<FocusOut>", self.auto_fill_party)
        self.entry_customer.bind("<<ComboboxSelected>>", self.auto_fill_party)
        self.entry_customer.bind("<Down>", lambda e: self.entry_phone.focus()) 

        self.entry_phone.bind("<Return>", lambda e: self.entry_address.focus())
        self.entry_phone.bind("<Down>", lambda e: self.entry_address.focus())
        self.entry_address.bind("<Return>", lambda e: self.entry_date.focus())
        self.entry_address.bind("<Down>", lambda e: self.entry_item.focus())
        self.entry_date.bind("<Return>", lambda e: self.entry_item.focus())
        
        self.entry_item.bind("<Return>", self.handle_item_enter)
        self.entry_item.bind("<FocusOut>", self.fill_rate) 
        self.entry_item.bind("<<ComboboxSelected>>", self.fill_rate)
        self.entry_item.bind("<Right>", lambda e: self.entry_qty.focus())
        self.entry_item.bind("<Down>", lambda e: self.entry_qty.focus()) # Force Down

        self.entry_qty.bind("<Return>", lambda e: self.entry_rate.focus())
        self.entry_qty.bind("<Right>", lambda e: self.entry_rate.focus())
        self.entry_qty.bind("<Left>", lambda e: self.entry_item.focus())

        self.entry_rate.bind("<Return>", lambda e: self.add_to_cart())
        self.entry_rate.bind("<Left>", lambda e: self.entry_qty.focus())
        
        self.final_freight.bind("<Return>", lambda e: self.final_tax_pct.focus())
        self.final_tax_pct.bind("<Return>", lambda e: self.btn_save.focus())
        self.final_tax_pct.bind("<KeyRelease>", self.recalculate_grand_total)
        self.final_freight.bind("<KeyRelease>", self.recalculate_grand_total)
        self.btn_save.bind("<Return>", lambda e: self.finalize_bill())
        
        self.after(100, self.entry_customer.focus_set)

    def apply_focus(self, w):
        w.bind("<FocusIn>", lambda e: w.config(background="#ffffcc") if hasattr(w,'config') else None)
        w.bind("<FocusOut>", lambda e: w.config(background="white") if hasattr(w,'config') else None)

    def auto_fill_party(self, event=None):
        name = self.entry_customer.get()
        if not name: return
        try:
            self.db.cursor.execute("SELECT party_phone, party_address FROM transactions WHERE party_name=? ORDER BY id DESC LIMIT 1", (name,))
            res = self.db.cursor.fetchone()
            if res:
                phone, addr = res
                if not self.entry_phone.get(): self.entry_phone.delete(0, tk.END); self.entry_phone.insert(0, phone)
                if not self.entry_address.get(): self.entry_address.delete(0, tk.END); self.entry_address.insert(0, addr)
        except: pass

    def on_customer_enter(self, event): self.auto_fill_party(); self.entry_phone.focus()

    def quick_create_item(self, e=None):
        top = tk.Toplevel(self); top.title("New Item"); top.geometry("300x150")
        tk.Label(top, text="Name:").pack(); n=tk.Entry(top); n.pack(); n.focus()
        tk.Label(top, text="Rate:").pack(); r=tk.Entry(top); r.pack()
        def sv(e=None):
            if n.get(): 
                self.db.cursor.execute("INSERT INTO items (item_name, rate) VALUES (?, ?)", (n.get(), float(r.get() or 0)))
                self.db.conn.commit(); self.load_data_masters(); self.entry_item['values']=self.full_item_list
                self.entry_item.set(n.get()); self.entry_rate.delete(0,tk.END); self.entry_rate.insert(0, r.get())
                top.destroy(); self.entry_qty.focus()
        n.bind("<Return>", lambda e: r.focus()); r.bind("<Return>", sv)

    def save_shortcut(self, event): self.finalize_bill()
    def fill_rate(self, event=None):
        sel = self.entry_item.get()
        if sel in self.item_rates: self.entry_rate.delete(0, tk.END); self.entry_rate.insert(0, str(self.item_rates[sel]))
    def handle_item_enter(self, event):
        self.fill_rate(); 
        if not self.entry_item.get().strip(): self.final_freight.focus()
        else: self.entry_qty.focus()

    def remove_item_from_list(self, event):
        sel = self.tree.selection()
        if sel:
            idx = self.tree.index(sel[0])
            del self.current_cart[idx]
            self.tree.delete(sel[0])
            for i, item in enumerate(self.tree.get_children()): self.tree.set(item, "SR", i+1)
            self.recalculate_grand_total()

    def add_to_cart(self, event=None):
        item, qty, rate = self.entry_item.get(), self.entry_qty.get(), self.entry_rate.get()
        if not item or not qty: return
        try:
            sub = float(qty) * float(rate)
            self.current_cart.append({"item": item, "qty": float(qty), "rate": float(rate), "subtotal": sub})
            sr_no = len(self.tree.get_children()) + 1
            self.tree.insert("", "end", values=(sr_no, item, qty, rate, f"{sub:.2f}"))
            self.recalculate_grand_total()
            self.entry_item.set(''); self.entry_qty.delete(0,tk.END); self.entry_rate.delete(0,tk.END); self.entry_item.focus()
        except: pass

    def recalculate_grand_total(self, event=None):
        sub = sum(x["subtotal"] for x in self.current_cart)
        try: tax = float(self.final_tax_pct.get() or 0)
        except: tax = 0.0
        try: frgt = float(self.final_freight.get() or 0)
        except: frgt = 0.0
        grand = sub + (sub * (tax/100)) + frgt
        self.lbl_total.config(text=f"{grand:.2f}")
        return grand, tax, frgt

    def finalize_bill(self, event=None):
        if not self.current_cart: messagebox.showwarning("Empty", "Cart empty!"); return
        party = self.entry_customer.get(); phone = self.entry_phone.get(); addr = self.entry_address.get()
        if not party: self.entry_customer.focus(); return

        grand, tax, frgt = self.recalculate_grand_total()
        desc = ", ".join([f"{x['item']}({x['qty']}x{x['rate']})" for x in self.current_cart])
        if tax: desc += f" | Tax:{tax}%"
        if frgt: desc += f" | Frgt:{frgt}"
        
        # Use the toggle state
        flow_type = self.current_flow
        
        if self.edit_bill_id:
            try:
                self.db.cursor.execute("""
                    UPDATE transactions 
                    SET date=?, party_name=?, description=?, flow=?, amount=?, party_phone=?, party_address=?
                    WHERE id=?
                """, (self.entry_date.get(), party, desc, flow_type, grand, phone, addr, self.edit_bill_id))
                self.db.conn.commit()
                messagebox.showinfo("Success", "Bill Updated!")
                self.destroy()
                if hasattr(self.controller, 'load_data'): self.controller.load_data()
            except Exception as e: messagebox.showerror("Error", str(e))
        else:
            if self.db.add_transaction(self.entry_date.get(), party, desc, flow_type, grand, phone, addr):
                self.controller.check_auto_backup()
                if messagebox.askyesno("Saved", "Print Bill?"):
                    printer.generate_invoice(self.entry_date.get(), party, desc, grand, flow_type)
                self.destroy()
                self.controller.show_bill_entry()