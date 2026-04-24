"""
excel_exporter.py — Excel export using openpyxl
"""
from datetime import datetime

def generate_statement_excel(customer_name, rows, from_date, to_date, company, out_path):
    try:
        import openpyxl
        from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                                     numbers as num_fmt)
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError("openpyxl not installed. Run: pip install openpyxl")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statement"

    # Styles
    navy_fill  = PatternFill("solid", fgColor="1A237E")
    blue_fill  = PatternFill("solid", fgColor="283593")
    light_fill = PatternFill("solid", fgColor="E8EAF6")
    green_fill = PatternFill("solid", fgColor="E8F5E9")
    red_fill   = PatternFill("solid", fgColor="FFEBEE")
    white_fill = PatternFill("solid", fgColor="FFFFFF")
    thin  = Side(style='thin',  color="BDBDBD")
    thick = Side(style='medium',color="1A237E")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def cell(row, col, value, bold=False, color="000000", bg=None,
             align="left", fmt=None, sz=10):
        c = ws.cell(row=row, column=col, value=value)
        c.font = Font(name="Calibri", bold=bold, color=color, size=sz)
        c.alignment = Alignment(horizontal=align, vertical="center", wrap_text=True)
        c.border = border
        if bg:
            c.fill = bg
        if fmt:
            c.number_format = fmt
        return c

    # ── Header ──────────────────────────────────────────────
    r = 1
    ws.merge_cells(f"A{r}:F{r}")
    cell(r, 1, company.get('company_name','Company'), bold=True, color="FFFFFF",
         bg=navy_fill, align="center", sz=16)
    ws.row_dimensions[r].height = 30
    r += 1
    ws.merge_cells(f"A{r}:F{r}")
    cell(r, 1, f"GSTIN: {company.get('gstin','')}  |  "
               f"{company.get('address','')} {company.get('city','')} {company.get('state','')}",
         color="FFFFFF", bg=blue_fill, align="center", sz=9)
    r += 1
    ws.merge_cells(f"A{r}:F{r}")
    cell(r, 1, "CUSTOMER STATEMENT", bold=True, color="FFFFFF",
         bg=navy_fill, align="center", sz=13)
    ws.row_dimensions[r].height = 22
    r += 1

    # Customer + period info
    ws.merge_cells(f"A{r}:C{r}")
    cell(r, 1, f"Customer: {customer_name}", bold=True, sz=11)
    ws.merge_cells(f"D{r}:F{r}")
    cell(r, 4, f"Period: {from_date} to {to_date}", align="right", sz=10)
    r += 1

    # Gap
    r += 1
    # Column headers
    headers = ["Date", "Invoice No", "Invoice Amount", "Amount Paid", "Balance Due", "Status"]
    for ci, h in enumerate(headers, 1):
        cell(r, ci, h, bold=True, color="FFFFFF", bg=blue_fill, align="center", sz=10)
    ws.row_dimensions[r].height = 18
    r += 1

    # Data rows
    tot_amt = tot_paid = tot_bal = 0.0
    for i, row in enumerate(rows):
        bg = light_fill if i % 2 == 0 else white_fill
        paid   = float(row['paid'])
        amount = float(row['amount'])
        bal    = float(row['balance'])
        status = "Paid" if bal <= 0 else ("Partial" if paid > 0 else "Unpaid")
        status_bg = PatternFill("solid", fgColor=("C8E6C9" if status=="Paid"
                                                   else "FFF9C4" if status=="Partial"
                                                   else "FFCDD2"))
        cell(r, 1, row['date'],       bg=bg, align="center")
        cell(r, 2, row['invoice_no'], bg=bg)
        cell(r, 3, amount,  bg=bg, align="right", fmt='#,##0.00')
        cell(r, 4, paid,    bg=bg, align="right", fmt='#,##0.00')
        cell(r, 5, bal,     bg=bg, align="right", fmt='#,##0.00')
        cell(r, 6, status,  bg=status_bg, align="center", bold=True)
        ws.row_dimensions[r].height = 16
        tot_amt  += amount
        tot_paid += paid
        tot_bal  += bal
        r += 1

    # Totals row
    cell(r, 1, "TOTAL", bold=True, bg=navy_fill, color="FFFFFF", align="center")
    ws.merge_cells(f"A{r}:B{r}")
    cell(r, 3, tot_amt,  bold=True, bg=navy_fill, color="FFFFFF", align="right", fmt='#,##0.00')
    cell(r, 4, tot_paid, bold=True, bg=navy_fill, color="FFFFFF", align="right", fmt='#,##0.00')
    cell(r, 5, tot_bal,  bold=True, bg=navy_fill, color="FFFFFF", align="right", fmt='#,##0.00')
    cell(r, 6, f"Outstanding: {tot_bal:,.2f}", bold=True,
         bg=PatternFill("solid", fgColor="C62828") if tot_bal > 0
               else PatternFill("solid", fgColor="1B5E20"),
         color="FFFFFF", align="center")
    ws.row_dimensions[r].height = 20
    r += 2

    # Footer
    ws.merge_cells(f"A{r}:F{r}")
    cell(r, 1, f"Generated on {datetime.now().strftime('%d-%m-%Y %H:%M')} | {company.get('company_name','')}",
         color="5C6BC0", align="center", sz=8)

    # Column widths
    for ci, w in enumerate([12, 18, 18, 16, 16, 12], 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    # Freeze header rows
    ws.freeze_panes = "A8"

    wb.save(out_path)
    return out_path
