import sqlite3
import shutil
import datetime

def create_backup(source_db, target_path, start_date=None, end_date=None):
    """
    Creates a backup. 
    If dates are provided, it creates a NEW DB and copies only matching transactions.
    If dates are None, it does a full file copy (safer/faster for full backups).
    """
    
    # CASE 1: FULL BACKUP (No dates provided)
    if not start_date and not end_date:
        try:
            shutil.copy2(source_db, target_path)
            return True, "Full backup created successfully."
        except Exception as e:
            return False, str(e)

    # CASE 2: PARTIAL BACKUP (Date Range)
    if not start_date or not end_date:
        return False, "Please provide both From and To dates for partial backup."

    try:
        src_conn = sqlite3.connect(source_db)
        src_cur = src_conn.cursor()

        tgt_conn = sqlite3.connect(target_path)
        tgt_cur = tgt_conn.cursor()

        # Make target predictable (fresh structure for each partial backup)
        tgt_cur.execute("DROP TABLE IF EXISTS transactions")
        tgt_cur.execute("DROP TABLE IF EXISTS items")

        tgt_cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                party_name TEXT,
                description TEXT,
                flow TEXT,
                amount REAL,
                status TEXT DEFAULT 'Pending',
                party_phone TEXT DEFAULT '',
                party_address TEXT DEFAULT ''
            )
        """)
        tgt_cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY,
                item_name TEXT UNIQUE,
                rate REAL
            )
        """)

        # Copy items master
        try:
            src_cur.execute("SELECT id, item_name, rate FROM items")
            items = src_cur.fetchall()
        except Exception:
            items = []

        for item in items:
            tgt_cur.execute(
                "INSERT OR IGNORE INTO items (id, item_name, rate) VALUES (?, ?, ?)",
                item
            )

        # Build schema-safe transaction query from source DB
        src_cur.execute("PRAGMA table_info(transactions)")
        source_cols = {row[1] for row in src_cur.fetchall()}

        def col_or_default(col_name, default_expr):
            return col_name if col_name in source_cols else f"{default_expr} AS {col_name}"

        select_expr = ", ".join([
            col_or_default("id", "NULL"),
            col_or_default("date", "''"),
            col_or_default("party_name", "''"),
            col_or_default("description", "''"),
            col_or_default("flow", "''"),
            col_or_default("amount", "0"),
            col_or_default("status", "'Pending'"),
            col_or_default("party_phone", "''"),
            col_or_default("party_address", "''")
        ])

        query = (
            f"SELECT {select_expr} "
            "FROM transactions WHERE date BETWEEN ? AND ? ORDER BY date, id"
        )
        src_cur.execute(query, (start_date, end_date))
        rows = src_cur.fetchall()

        count = 0
        for row in rows:
            tgt_cur.execute(
                """
                INSERT INTO transactions
                (id, date, party_name, description, flow, amount, status, party_phone, party_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row
            )
            count += 1

        tgt_conn.commit()
        src_conn.close()
        tgt_conn.close()
        
        return True, f"Partial backup created. {count} transactions exported."
        
    except Exception as e:
        return False, f"Backup failed: {e}"