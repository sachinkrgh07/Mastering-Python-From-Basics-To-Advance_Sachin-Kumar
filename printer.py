import os
import webbrowser
import tempfile
import html

# --- EDIT YOUR COMPANY DETAILS HERE ---
COMPANY_INFO = {
    "name": "MY SHOP NAME",
    "tagline": "Dealers in All Kinds of Goods",
    "address_1": "Shop No. 12, Main Market",
    "address_2": "City, State - 395007",
    "phone": "98765 43210",
    "email": "contact@myshop.com",
    "gst": "24ABCDE1234F1Z5",
    "footer": "Thank you for your business! Goods once sold will not be taken back."
}
# --------------------------------------

def generate_invoice(date, party, description, amount, flow_type):
    """
    Generates an invoice matching the 'Bill Book' image format.
    """
    
    # --- 1. DATA PARSING (Kept logic same as your original) ---
    items_part = ""; tax_part = "0"; frgt_part = "0"
    clean_desc = description.replace("[SALE (Cr)]", "").replace("[PURCHASE (Dr)]", "").strip()
    parts = clean_desc.split("|")
    if len(parts) > 0: items_part = parts[0].replace("Items:", "").strip()
    
    for p in parts[1:]:
        if "Tax:" in p: tax_part = p.replace("Tax:", "").replace("%", "").strip()
        if "Freight:" in p or "Frgt:" in p: frgt_part = p.split(":")[1].strip()

    item_list = items_part.split(",")
    rows_data = []
    subtotal = 0.0
    
    # Process items to get data first
    for idx, it in enumerate(item_list):
        sr_no = idx + 1
        if "(" in it and "x" in it:
            name = it.split("(")[0].strip()
            rest = it.split("(")[1].replace(")", "")
            try:
                qty, rate = rest.split("x")
                qty = float(qty)
                rate = float(rate)
                line_total = qty * rate
                subtotal += line_total
            except: 
                line_total=0; qty=0; rate=0
            
            rows_data.append({
                "sr": sr_no, "desc": name, "qty": qty, "rate": rate, "total": line_total
            })
        else:
            # Handle items without explicit qty/rate
            rows_data.append({
                "sr": sr_no, "desc": it, "qty": "", "rate": "", "total": 0.00
            })

    # --- 2. CALCULATE EXTRAS ---
    try: tax_val = subtotal * (float(tax_part) / 100)
    except: tax_val = 0
    try: frgt_val = float(frgt_part)
    except: frgt_val = 0
    
    final_total = subtotal + tax_val + frgt_val

    # --- 3. HTML GENERATION (The "Bill Book" Style) ---
    
    # We need to fill empty rows to make the grid look like the image
    MAX_ROWS = 18 
    rows_html = ""
    
    # Add actual items
    for row in rows_data:
        q_str = f"{row['qty']:.2f}" if isinstance(row['qty'], (int, float)) else ""
        r_str = f"{row['rate']:.2f}" if isinstance(row['rate'], (int, float)) else ""
        t_str = f"{row['total']:.2f}" if row['total'] > 0 else ""
        
        rows_html += f"""
        <tr>
            <td class="col-sr">{row['sr']}</td>
            <td class="col-desc">{row['desc']}</td>
            <td class="col-qt">{q_str}</td>
            <td class="col-amt">{r_str}</td>
            <td class="col-total">{t_str}</td>
        </tr>"""

    # Add Tax/Freight as rows inside the grid if space permits, or just calculate at bottom
    # To match image exactly, we usually put tax in the grid logic or just summary. 
    # Let's add Tax/Freight as items in the grid for clarity if they exist.
    current_row_count = len(rows_data)
    
    if tax_val > 0:
        current_row_count += 1
        rows_html += f"""<tr><td class="col-sr"></td><td class="col-desc">Tax ({tax_part}%)</td><td></td><td></td><td class="col-total">{tax_val:.2f}</td></tr>"""
    
    # Fill remaining space with empty grid lines
    items_to_fill = MAX_ROWS - current_row_count
    for _ in range(items_to_fill):
        rows_html += """
        <tr>
            <td class="col-sr">&nbsp;</td>
            <td class="col-desc">&nbsp;</td>
            <td class="col-qt">&nbsp;</td>
            <td class="col-amt">&nbsp;</td>
            <td class="col-total">&nbsp;</td>
        </tr>"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Invoice</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #555; padding: 20px; }}
            .page {{ 
                background: white; 
                width: 21cm; 
                min-height: 29.7cm; 
                margin: 0 auto; 
                border: 1px solid black;
                position: relative;
            }}
            
            /* --- HEADER SECTION --- */
            .header {{
                background-color: #e0e0e0; /* Gray background */
                border-bottom: 2px solid black;
                padding: 15px;
            }}
            .company-title {{ font-weight: bold; margin-bottom: 20px; font-size: 1.1em; }}
            
            .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
            .field {{ display: flex; align-items: baseline; }}
            .label {{ font-weight: bold; margin-right: 10px; min-width: 50px; }}
            .input-box {{ 
                background: white; 
                border: 1px solid white; /* Invisible border to look like paper */
                padding: 5px; 
                min-width: 150px; 
                font-weight: bold;
                border-bottom: 1px dotted #999; /* Dotted line look */
            }}
            .address-box {{
                background: white;
                width: 350px;
                padding: 5px;
                border-bottom: 1px dotted #999;
            }}

            /* --- TABLE SECTION --- */
            .grid-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            .grid-table th {{
                background-color: #e0e0e0;
                border: 1px solid black;
                padding: 5px;
                text-align: center;
                font-weight: bold;
            }}
            .grid-table td {{
                border: 1px solid black;
                padding: 5px 8px;
                height: 25px; /* Fixed height for rows */
            }}
            
            /* Column Widths to match image */
            .col-sr {{ width: 5%; text-align: center; }}
            .col-desc {{ width: 55%; }}
            .col-qt {{ width: 10%; text-align: center; }}
            .col-amt {{ width: 15%; text-align: right; }}
            .col-total {{ width: 15%; text-align: right; }}

            /* --- FOOTER SECTION --- */
            .footer-section {{
                background-color: #e0e0e0;
                border-top: 2px solid black;
                padding: 15px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
            }}
            .freight-box {{
                display: flex; align-items: center;
                font-weight: bold;
            }}
            .total-box {{
                display: flex; align-items: center;
                font-weight: bold;
                font-size: 1.2em;
            }}
            .white-box {{
                background: white;
                padding: 5px 15px;
                margin-left: 10px;
                min-width: 100px;
                text-align: right;
            }}

        </style>
    </head>
    <body>
        <div class="page">
            <div class="header">
                <div class="company-title">Company details</div>
                
                <div class="row">
                    <div class="field">
                        <span class="label">Name :</span>
                        <div class="input-box" style="width: 400px;">{party}</div>
                    </div>
                    <div class="field">
                        <span class="label">No. :</span>
                        <div class="input-box">1</div> </div>
                </div>

                <div class="row">
                    <div class="field">
                        <span class="label">Add. :</span>
                        <div class="address-box">{COMPANY_INFO['address_1']}, {COMPANY_INFO['address_2']}</div>
                    </div>
                    <div class="field">
                        <span class="label">Date :</span>
                        <div class="input-box">{date}</div>
                    </div>
                </div>
            </div>

            <table class="grid-table">
                <thead>
                    <tr>
                        <th class="col-sr">Sr.</th>
                        <th>Item name</th>
                        <th class="col-qt">Qt</th>
                        <th class="col-amt">Amt</th>
                        <th class="col-total">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <div class="footer-section">
                <div class="freight-box">
                    Freight : 
                    <div class="white-box">{frgt_val:.2f}</div>
                </div>
                <div class="total-box">
                    TOTAL : 
                    <div class="white-box">₹ {amount:.2f}</div>
                </div>
            </div>
        </div>
        <script>window.onload = function() {{ window.print(); }}</script>
    </body>
    </html>
    """
    
    fd, path = tempfile.mkstemp(suffix=".html")
    with os.fdopen(fd, 'w', encoding='utf-8') as tmp: tmp.write(html_content)
    webbrowser.open('file://' + path)


def generate_ledger_report(rows, start_date, end_date):
        safe_rows = rows or []

        data_rows = []
        total_in = 0.0
        total_out = 0.0
        closing_balance = 0.0

        for row in safe_rows:
                vals = list(row) if isinstance(row, (list, tuple)) else []
                vals += [""] * (8 - len(vals))

                txn_id = str(vals[0])
                date = str(vals[1])
                particulars = str(vals[2])
                txn_type = str(vals[3])
                in_val = str(vals[4]).strip()
                out_val = str(vals[5]).strip()
                bal_val = str(vals[6]).strip()
                status = str(vals[7])

                def to_float(text):
                        try:
                                return float(str(text).replace(",", "").replace("₹", "").strip())
                        except:
                                return 0.0

                in_num = to_float(in_val) if in_val else 0.0
                out_num = to_float(out_val) if out_val else 0.0
                bal_num = to_float(bal_val) if bal_val else closing_balance

                total_in += in_num
                total_out += out_num
                closing_balance = bal_num

                data_rows.append(
                        (
                                html.escape(txn_id),
                                html.escape(date),
                                html.escape(particulars),
                                html.escape(txn_type),
                                f"{in_num:,.2f}" if in_num else "",
                                f"{out_num:,.2f}" if out_num else "",
                                f"{bal_num:,.2f}",
                                html.escape(status),
                        )
                )

        rows_html = ""
        for r in data_rows:
                rows_html += (
                        "<tr>"
                        f"<td>{r[0]}</td>"
                        f"<td>{r[1]}</td>"
                        f"<td class='left'>{r[2]}</td>"
                        f"<td>{r[3]}</td>"
                        f"<td class='num'>{r[4]}</td>"
                        f"<td class='num'>{r[5]}</td>"
                        f"<td class='num'>{r[6]}</td>"
                        f"<td>{r[7]}</td>"
                        "</tr>"
                )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='UTF-8'>
            <title>Ledger Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 16px; color: #111827; }}
                .header {{ margin-bottom: 10px; }}
                .company {{ font-size: 20px; font-weight: bold; }}
                .meta {{ margin-top: 4px; color: #374151; }}
                .summary {{ margin: 10px 0 12px; display: flex; gap: 16px; flex-wrap: wrap; }}
                .chip {{ border: 1px solid #d1d5db; padding: 6px 10px; border-radius: 6px; background: #f9fafb; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
                th, td {{ border: 1px solid #d1d5db; padding: 6px; text-align: center; }}
                th {{ background: #f3f4f6; font-weight: 700; }}
                td.left {{ text-align: left; }}
                td.num {{ text-align: right; }}
                @media print {{
                    body {{ margin: 0.6cm; }}
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>
            <div class='header'>
                <div class='company'>{html.escape(COMPANY_INFO.get('name', 'Ledger Report'))}</div>
                <div class='meta'>Ledger Report | From {html.escape(str(start_date))} To {html.escape(str(end_date))}</div>
            </div>

            <div class='summary'>
                <div class='chip'>Cash In: ₹ {total_in:,.2f}</div>
                <div class='chip'>Cash Out: ₹ {total_out:,.2f}</div>
                <div class='chip'>Net: ₹ {(total_in - total_out):,.2f}</div>
                <div class='chip'>Closing Balance: ₹ {closing_balance:,.2f}</div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Date</th>
                        <th>Particulars</th>
                        <th>Type</th>
                        <th>Cash In</th>
                        <th>Cash Out</th>
                        <th>Balance</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html if rows_html else "<tr><td colspan='8'>No data</td></tr>"}
                </tbody>
            </table>

            <script>window.onload = function(){{ window.print(); }}</script>
        </body>
        </html>
        """

        fd, path = tempfile.mkstemp(suffix=".html")
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.write(html_content)
        webbrowser.open("file://" + path)