import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import sys
import os
import math
import datetime
import subprocess
from datetime import timedelta

import bill_entry
import view_edit
import settled_view
import ledger_view
import item_sheet
import analysis_view
import backup_utils
import global_search

# --- CREDENTIALS ---
ADMIN_USER = "admin"
ADMIN_PASS = "shaurya"


def get_db_path():
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(application_path, 'portable_accounts.db')


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class DBManager:
    def __init__(self, custom_path=None):
        self.db_path = custom_path if custom_path else get_db_path()
        self.connect()

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.check_updates()

    def switch_db(self, new_path):
        self.conn.close()
        self.db_path = new_path
        self.connect()

    def check_updates(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT, party_name TEXT, description TEXT,
                flow TEXT, amount REAL, status TEXT DEFAULT 'Pending'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT UNIQUE, rate REAL
            )
        """)
        try:
            self.cursor.execute("SELECT status FROM transactions LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT 'Pending'")
        try:
            self.cursor.execute("SELECT party_phone FROM transactions LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN party_phone TEXT DEFAULT ''")
        try:
            self.cursor.execute("SELECT party_address FROM transactions LIMIT 1")
        except:
            self.cursor.execute("ALTER TABLE transactions ADD COLUMN party_address TEXT DEFAULT ''")
        self.conn.commit()

    def add_transaction(self, date, party, desc, flow, amount, phone="", address=""):
        try:
            self.cursor.execute("""
                INSERT INTO transactions
                    (date, party_name, description, flow, amount, status, party_phone, party_address)
                VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?)
            """, (date, party, desc, flow, amount, phone, address))
            self.conn.commit()
            return True
        except Exception as e:
            print(e)
            return False

    def get_transaction_count(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM transactions")
            return self.cursor.fetchone()[0]
        except:
            return 0

    def get_party_details(self, party_name):
        try:
            self.cursor.execute(
                "SELECT party_phone, party_address FROM transactions "
                "WHERE party_name=? ORDER BY id DESC LIMIT 1", (party_name,))
            return self.cursor.fetchone()
        except:
            return None


# ══════════════════════════════════════════════
#  LOGIN  — runs as a standalone Tk root first,
#  then is replaced by the main app on success.
# ══════════════════════════════════════════════
def show_login():
    """
    Show a plain login window.
    Returns True if login succeeded, False if user closed it.
    Uses its own Tk root so there are zero issues with
    withdrawn parents, grab_set on hidden windows, etc.
    """
    result = {"ok": False}

    win = tk.Tk()
    win.title("Login")
    win.resizable(False, False)
    win.configure(bg="#1e2a3a")

    # Center
    win.update_idletasks()
    w, h = 340, 360
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    attempts = [0]

    # ── UI ──────────────────────────────────────────────
    tk.Label(win, text="Accounts System",
             font=("Arial", 16, "bold"),
             bg="#1e2a3a", fg="white").pack(pady=(30, 2))
    tk.Label(win, text="Administrator Login",
             font=("Arial", 9),
             bg="#1e2a3a", fg="#aaaaaa").pack()

    frame = tk.Frame(win, bg="#263545", padx=28, pady=20)
    frame.pack(fill="x", padx=20, pady=20)

    tk.Label(frame, text="Username", bg="#263545", fg="#aaaaaa",
             font=("Arial", 9), anchor="w").pack(fill="x")
    entry_user = tk.Entry(frame, font=("Arial", 12),
                          bg="#1e2a3a", fg="white",
                          insertbackground="white",
                          relief="flat", bd=3)
    entry_user.pack(fill="x", pady=(2, 12), ipady=5)

    tk.Label(frame, text="Password", bg="#263545", fg="#aaaaaa",
             font=("Arial", 9), anchor="w").pack(fill="x")

    pass_frame = tk.Frame(frame, bg="#1e2a3a")
    pass_frame.pack(fill="x", pady=(2, 4))

    entry_pass = tk.Entry(pass_frame, font=("Arial", 12),
                          bg="#1e2a3a", fg="white",
                          insertbackground="white",
                          relief="flat", bd=3, show="*")
    entry_pass.pack(side="left", fill="x", expand=True, ipady=5)

    show_var = [False]

    def toggle_show():
        show_var[0] = not show_var[0]
        entry_pass.config(show="" if show_var[0] else "*")
        btn_show.config(text="Hide" if show_var[0] else "Show")

    btn_show = tk.Button(pass_frame, text="Show",
                         bg="#263545", fg="#aaaaaa",
                         font=("Arial", 8), relief="flat", bd=0,
                         command=toggle_show)
    btn_show.pack(side="right", padx=4)

    lbl_error = tk.Label(frame, text="", bg="#263545",
                         fg="#ff6b6b", font=("Arial", 9))
    lbl_error.pack(pady=(8, 0))

    def do_login(event=None):
        user = entry_user.get().strip()
        pwd  = entry_pass.get().strip()
        if user == ADMIN_USER and pwd == ADMIN_PASS:
            result["ok"] = True
            win.destroy()
        else:
            attempts[0] += 1
            entry_pass.delete(0, tk.END)
            if attempts[0] >= 3:
                lbl_error.config(
                    text="Wrong credentials  (%d failed attempts)" % attempts[0])
            else:
                lbl_error.config(text="Invalid username or password")
            entry_user.focus_set()

    def on_close():
        result["ok"] = False
        win.destroy()

    win.protocol("WM_DELETE_WINDOW", on_close)

    btn_login = tk.Button(win, text="LOGIN",
                          bg="#1565c0", fg="white",
                          font=("Arial", 11, "bold"),
                          relief="flat", bd=0, pady=10,
                          activebackground="#0d47a1",
                          activeforeground="white",
                          command=do_login)
    btn_login.pack(fill="x", padx=20, pady=(0, 6))

    tk.Button(win, text="Exit",
              bg="#1e2a3a", fg="#888888",
              font=("Arial", 9), relief="flat", bd=0,
              command=on_close).pack()

    # Keyboard nav
    entry_user.bind("<Return>", lambda e: entry_pass.focus_set())
    entry_pass.bind("<Return>", do_login)
    win.bind("<Escape>", lambda e: on_close())

    entry_user.focus_set()
    win.mainloop()

    return result["ok"]


# ══════════════════════════════════════════════
#   MAIN APPLICATION
# ══════════════════════════════════════════════
class AccountingApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Portable Accounting System")
        self.auto_backup_enabled = False
        self.backup_interval     = 50
        self.backup_folder       = ""

        try:
            icon_path = resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass

        self.db = DBManager()

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=14)
        self.style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"), foreground="#1f2937", background="#f5f7fb")
        self.style.configure("Subtle.TLabel", font=("Segoe UI", 10), foreground="#4b5563", background="#f5f7fb")
        self.style.configure("MenuPrimary.TButton", font=("Segoe UI", 11, "bold"), padding=12, background="#1d4ed8", foreground="white")
        self.style.map("MenuPrimary.TButton", background=[("active", "#1e40af")])
        self.style.configure("MenuNeutral.TButton", font=("Segoe UI", 11), padding=12)

        self.container = tk.Frame(self, bg="#f5f7fb")
        self.container.pack(fill="both", expand=True)
        self.current_page = None
        self.menu_nav_buttons = []
        self.menu_focus_index = 0

        self.bind_all("<F1>",        lambda e: self.show_bill_entry())
        self.bind_all("<F2>",        lambda e: self.show_bill_view())
        self.bind_all("<F3>",        lambda e: self.show_settled_view())
        self.bind_all("<F4>",        lambda e: self.show_ledger_view())
        self.bind_all("<F6>",        lambda e: self.show_analysis_view())
        self.bind_all("<Escape>",    self.handle_escape)
        self.bind_all("<Control-g>", self.open_global_search)
        self.bind_all("<Control-h>", self.show_shortcuts_help)
        self.bind_all("<Control-H>", self.show_shortcuts_help)
        self.bind_all("<F12>",       self.trigger_panic_mode)

        self.state("zoomed")
        self.show_main_menu()

    def trigger_panic_mode(self, event=None):
        try:
            subprocess.Popen('calc.exe')
        except:
            pass
        self.destroy()
        sys.exit()

    def clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def handle_escape(self, event):
        if self.current_page == "MENU":
            if messagebox.askyesno("Exit", "Close Application?"):
                self.destroy()
        elif self.current_page:
            self.show_main_menu()

    def open_global_search(self, event=None):
        search_window = global_search.GlobalSearchPopup(self, self.db)
        search_window.transient(self)
        search_window.grab_set()

    def _shortcut_sections(self):
        current_page_name = {
            "MENU": "Main Menu",
            "VIEW": "Pending Bills",
            "ARCHIVE": "Archives",
            "LEDGER": "Ledger",
            "ITEMS": "Item Master",
            "ANALYSIS": "Analysis"
        }.get(self.current_page, "Billing")

        sections = [
            (
                "Global",
                [
                    ("F1", "New Bill"),
                    ("F2", "Pending Bills"),
                    ("F3", "Archives"),
                    ("F4", "Ledger"),
                    ("F6", "Analysis"),
                    ("F5", "Item Master"),
                    ("Ctrl+G", "Global Search"),
                    ("Ctrl+H", "Show this shortcuts help"),
                    ("Esc", "Back to menu / Exit from menu"),
                    ("F12", "Panic mode")
                ]
            )
        ]

        page_specific = {
            "MENU": [
                ("1", "Open New Bill"),
                ("2", "Open Pending Bills"),
                ("3", "Open Archives"),
                ("4", "Open Ledger"),
                ("5", "Open Analysis"),
                ("↑ / ↓ / ← / →", "Move across dashboard options"),
                ("Enter", "Open focused dashboard option")
            ],
            "VIEW": [
                ("Ctrl+F", "Focus search"),
                ("Ctrl+P", "Print selected bill(s)"),
                ("E", "Edit selected bill"),
                ("Delete", "Settle selected bill(s)"),
                ("Enter", "Edit selected bill")
            ],
            "ARCHIVE": [
                ("Ctrl+F", "Focus search"),
                ("Ctrl+P", "Print popup"),
                ("Alt+R", "Revert selected to Pending")
            ],
            "LEDGER": [
                ("Ctrl+P", "Print report"),
                ("Ctrl+F", "Focus From Date"),
                ("Enter", "Apply date filter (when date box focused)")
            ],
            "ITEMS": [
                ("Ctrl+F", "Focus item name"),
                ("Enter", "Name → Rate → Add item"),
                ("Delete", "Delete selected item")
            ],
            "ANALYSIS": [
                ("Ctrl+R", "Refresh analysis"),
                ("Ctrl+F", "Focus period selector")
            ]
        }

        sections.append((current_page_name, page_specific.get(self.current_page, [])))
        return sections

    def show_shortcuts_help(self, event=None):
        popup = tk.Toplevel(self)
        popup.title("Keyboard Shortcuts")
        popup.geometry("700x520")
        popup.configure(bg="white")
        popup.transient(self)
        popup.grab_set()
        popup.bind("<Escape>", lambda e: popup.destroy())

        tk.Label(
            popup,
            text="Keyboard Shortcuts",
            bg="white",
            fg="#1e2a3a",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=16, pady=(14, 6))

        tk.Label(
            popup,
            text="Tip: Use Ctrl+H anywhere to open this help.",
            bg="white",
            fg="#555",
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=16, pady=(0, 10))

        body = tk.Frame(popup, bg="white")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        for section_name, rows in self._shortcut_sections():
            if not rows:
                continue

            frame = tk.LabelFrame(body, text=section_name, bg="white", fg="#1e2a3a", padx=10, pady=8)
            frame.pack(fill="x", pady=6)

            for key, action in rows:
                row_frame = tk.Frame(frame, bg="white")
                row_frame.pack(fill="x", pady=1)
                tk.Label(row_frame, text=key, bg="#eef3f9", fg="#0d47a1",
                         width=14, anchor="w", font=("Consolas", 10, "bold")).pack(side="left", padx=(0, 8))
                tk.Label(row_frame, text=action, bg="white", fg="#222",
                         anchor="w", font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)

        tk.Button(
            popup,
            text="Close (Esc)",
            bg="#1565c0",
            fg="white",
            relief="flat",
            padx=16,
            pady=6,
            command=popup.destroy
        ).pack(pady=(0, 12))

    def check_auto_backup(self):
        if self.auto_backup_enabled and self.backup_folder:
            count = self.db.get_transaction_count()
            if count > 0 and count % self.backup_interval == 0:
                fname = f"AutoBackup_{datetime.date.today()}_{count}.db"
                path  = os.path.join(self.backup_folder, fname)
                backup_utils.create_backup(self.db.db_path, path)

    def logout(self):
        if messagebox.askyesno("Logout", "Log out and return to login screen?"):
            self.destroy()
            # Re-run login → re-launch app if successful
            if show_login():
                app = AccountingApp()
                app.mainloop()

    def _focus_menu_button(self):
        if not self.menu_nav_buttons:
            return
        self.menu_focus_index %= len(self.menu_nav_buttons)
        try:
            self.menu_nav_buttons[self.menu_focus_index].focus_set()
        except:
            pass

    def menu_move_focus(self, step):
        if self.current_page != "MENU" or not self.menu_nav_buttons:
            return "break"
        self.menu_focus_index = (self.menu_focus_index + step) % len(self.menu_nav_buttons)
        self._focus_menu_button()
        return "break"

    def menu_activate_focused(self, event=None):
        if self.current_page != "MENU" or not self.menu_nav_buttons:
            return "break"
        try:
            self.menu_nav_buttons[self.menu_focus_index].invoke()
        except:
            pass
        return "break"

    def show_main_menu(self):
        self.clear_container()
        self.current_page = "MENU"
        self.unbind_menu_keys()
        self.container.configure(bg="#f5f7fb")

        menu_frame = tk.Frame(self.container, bg="#f5f7fb")
        menu_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(menu_frame, text="Accounting Dashboard",
                  style="Header.TLabel").pack(pady=(0, 5))

        db_name = os.path.basename(self.db.db_path)
        tk.Label(menu_frame, text="Active DB: " + db_name,
                 bg="#e8edf7", fg="#374151", padx=12, pady=6,
                 font=("Arial", 10, "bold")).pack(pady=(0, 15))

        self.menu_nav_buttons = []

        btn_new = ttk.Button(menu_frame, text="1. New Bill (F1)", style="MenuPrimary.TButton", command=self.show_bill_entry)
        btn_new.pack(fill="x", pady=5)
        self.menu_nav_buttons.append(btn_new)

        btn_pending = ttk.Button(menu_frame, text="2. Pending Bills (F2)", style="MenuNeutral.TButton", command=self.show_bill_view)
        btn_pending.pack(fill="x", pady=5)
        self.menu_nav_buttons.append(btn_pending)

        btn_archive = ttk.Button(menu_frame, text="3. Archives (F3)", style="MenuNeutral.TButton", command=self.show_settled_view)
        btn_archive.pack(fill="x", pady=5)
        self.menu_nav_buttons.append(btn_archive)

        btn_ledger = ttk.Button(menu_frame, text="4. Ledger (F4)", style="MenuNeutral.TButton", command=self.show_ledger_view)
        btn_ledger.pack(fill="x", pady=5)
        self.menu_nav_buttons.append(btn_ledger)

        btn_analysis = ttk.Button(menu_frame, text="5. Analysis (F6)", style="MenuNeutral.TButton", command=self.show_analysis_view)
        btn_analysis.pack(fill="x", pady=5)
        self.menu_nav_buttons.append(btn_analysis)

        btn_help = ttk.Button(menu_frame, text="Shortcuts Help (Ctrl+H)", style="MenuNeutral.TButton", command=self.show_shortcuts_help)
        btn_help.pack(fill="x", pady=5)
        self.menu_nav_buttons.append(btn_help)

        btn_exit = ttk.Button(menu_frame, text="Exit (Esc)", style="MenuNeutral.TButton", command=self.destroy)
        btn_exit.pack(fill="x", pady=20)
        self.menu_nav_buttons.append(btn_exit)

        tk.Button(self.container, text="Items (F5)",
              bg="#334155", fg="white", relief="flat", padx=12, pady=6,
                  command=self.show_item_sheet
                  ).place(relx=0.02, rely=0.92, anchor="sw")

        tool_frame = tk.Frame(self.container, bg="#f5f7fb")
        tool_frame.place(relx=0.98, rely=0.92, anchor="se")
        tk.Button(tool_frame, text="Load DB", bg="#7c3aed", fg="white",
              padx=12, pady=6, relief="flat", command=self.load_external_db).pack(side="left", padx=5)
        tk.Button(tool_frame, text="Backup",  bg="#ea580c", fg="white",
              padx=12, pady=6, relief="flat", command=self.open_backup_popup).pack(side="left", padx=5)
        tk.Button(tool_frame, text="Logout",  bg="#b91c1c", fg="white",
              padx=12, pady=6, relief="flat", command=self.logout).pack(side="left", padx=5)

        self.bind("1",    lambda e: self.show_bill_entry())
        self.bind("2",    lambda e: self.show_bill_view())
        self.bind("3",    lambda e: self.show_settled_view())
        self.bind("4",    lambda e: self.show_ledger_view())
        self.bind("5",    lambda e: self.show_analysis_view())
        self.bind("<F5>", lambda e: self.show_item_sheet())
        self.bind("<Down>",  lambda e: self.menu_move_focus(1))
        self.bind("<Up>",    lambda e: self.menu_move_focus(-1))
        self.bind("<Right>", lambda e: self.menu_move_focus(1))
        self.bind("<Left>",  lambda e: self.menu_move_focus(-1))
        self.bind("<Return>", self.menu_activate_focused)

        self.menu_focus_index = 0
        self.after(100, self._focus_menu_button)

    def unbind_menu_keys(self):
        try:
            self.unbind("1"); self.unbind("2")
            self.unbind("3"); self.unbind("4")
            self.unbind("5")
            self.unbind("<F5>")
            self.unbind("<Down>")
            self.unbind("<Up>")
            self.unbind("<Right>")
            self.unbind("<Left>")
            self.unbind("<Return>")
        except:
            pass

    def load_external_db(self):
        path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if path:
            try:
                self.db.switch_db(path)
                messagebox.showinfo("Loaded", "Loaded: " + os.path.basename(path))
                self.show_main_menu()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def open_backup_popup(self):
        top = tk.Toplevel(self)
        top.title("Backup Settings")
        top.geometry("500x450")
        top.configure(bg="#f0f0f0")

        tk.Label(top, text="Create Backup",
                 font=("Segoe UI", 12, "bold"), bg="#f0f0f0").pack(pady=10)
        filter_frame = tk.LabelFrame(top, text="Backup Range",
                                     bg="#f0f0f0", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20)

        today = datetime.date.today()
        s_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))
        e_var = tk.StringVar(value=today.strftime("%Y-%m-%d"))

        def set_range(mode):
            s, e = today, today
            if mode == "week":
                s = today - timedelta(days=today.weekday())
                e = s + timedelta(days=6)
            elif mode == "month":
                s = today.replace(day=1)
                n = today.replace(day=28) + timedelta(days=4)
                e = n - timedelta(days=n.day)
            elif mode == "year":
                s = today.replace(month=1, day=1)
                e = today.replace(month=12, day=31)
            elif mode == "full":
                s_var.set(""); e_var.set(""); return
            s_var.set(s.strftime("%Y-%m-%d"))
            e_var.set(e.strftime("%Y-%m-%d"))

        btn_f = tk.Frame(filter_frame, bg="#f0f0f0")
        btn_f.pack(fill="x", pady=5)
        tk.Button(btn_f, text="This Month", command=lambda: set_range("month")).pack(side="left", padx=2)
        tk.Button(btn_f, text="This Year",  command=lambda: set_range("year")).pack(side="left", padx=2)
        tk.Button(btn_f, text="FULL DB", bg="#ddd", command=lambda: set_range("full")).pack(side="left", padx=10)

        entry_f = tk.Frame(filter_frame, bg="#f0f0f0")
        entry_f.pack(fill="x", pady=5)
        tk.Label(entry_f, text="From:", bg="#f0f0f0").pack(side="left")
        tk.Entry(entry_f, textvariable=s_var, width=12).pack(side="left", padx=5)
        tk.Label(entry_f, text="To:", bg="#f0f0f0").pack(side="left")
        tk.Entry(entry_f, textvariable=e_var, width=12).pack(side="left", padx=5)

        def do_backup():
            path = filedialog.asksaveasfilename(
                defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
            if not path:
                return
            s, e = s_var.get(), e_var.get()
            success, msg = backup_utils.create_backup(
                self.db.db_path, path,
                s if s else None, e if e else None)
            if success:
                messagebox.showinfo("Success", msg)
                top.destroy()
            else:
                messagebox.showerror("Error", msg)

        tk.Button(top, text="CREATE BACKUP", bg="#27ae60", fg="white",
                  font=("Segoe UI", 10, "bold"), command=do_backup).pack(pady=10)

        ttk.Separator(top, orient="horizontal").pack(fill="x", padx=20, pady=10)
        tk.Label(top, text="Auto-Backup",
                 font=("Segoe UI", 12, "bold"), bg="#f0f0f0").pack(pady=5)

        def toggle_auto():
            self.auto_backup_enabled = not self.auto_backup_enabled
            status_lbl.config(
                text="Status: " + ("ON" if self.auto_backup_enabled else "OFF"),
                fg="green" if self.auto_backup_enabled else "red"
            )
            if self.auto_backup_enabled and not self.backup_folder:
                folder = filedialog.askdirectory()
                if folder:
                    self.backup_folder = folder
                else:
                    self.auto_backup_enabled = False
                    status_lbl.config(text="Status: OFF", fg="red")

        status_lbl = tk.Label(
            top,
            text="Status: " + ("ON" if self.auto_backup_enabled else "OFF"),
            fg="green" if self.auto_backup_enabled else "red",
            bg="#f0f0f0"
        )
        status_lbl.pack()
        tk.Button(top, text="Toggle Auto-Backup", command=toggle_auto).pack(pady=5)

    def show_bill_entry(self):
        self.unbind_menu_keys()
        bill_entry.BillEntryPage(self, self, self.db)

    def show_bill_view(self):
        self.unbind_menu_keys()
        self.clear_container()
        self.current_page = "VIEW"
        view_edit.ViewEditPage(self.container, self, self.db).pack(fill="both", expand=True)

    def show_settled_view(self, focus_bill_id=None, auto_open_bill=False):
        self.unbind_menu_keys()
        self.clear_container()
        self.current_page = "ARCHIVE"
        settled_view.SettledViewPage(
            self.container, self, self.db,
            focus_bill_id=focus_bill_id,
            auto_open_bill=auto_open_bill
        ).pack(fill="both", expand=True)

    def show_ledger_view(self):
        self.unbind_menu_keys()
        self.clear_container()
        self.current_page = "LEDGER"
        ledger_view.LedgerPage(self.container, self, self.db).pack(fill="both", expand=True)

    def show_item_sheet(self):
        self.unbind_menu_keys()
        self.clear_container()
        self.current_page = "ITEMS"
        item_sheet.ItemSheetPage(self.container, self, self.db).pack(fill="both", expand=True)

    def show_analysis_view(self):
        self.unbind_menu_keys()
        self.clear_container()
        self.current_page = "ANALYSIS"
        analysis_view.AnalysisPage(self.container, self, self.db).pack(fill="both", expand=True)


# ══════════════════════════════════════════════
#   ENTRY POINT
# ══════════════════════════════════════════════
if __name__ == "__main__":
    # Step 1: show login window (its own Tk root, cleanest approach)
    if show_login():
        # Step 2: login succeeded — destroy that root and start real app
        app = AccountingApp()
        app.mainloop()
    # If login was closed/cancelled, just exit silently
