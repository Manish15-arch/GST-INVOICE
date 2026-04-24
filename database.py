"""
database.py — SQLite layer for GST Billing Suite
"""
import sqlite3
import os
from datetime import datetime
from ui.styles import GSTIN_STATES


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base, "data", "invoice_db.sqlite")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ─────────────────────────────────────────────────────────
    def initialize(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS company_profile (
                    id INTEGER PRIMARY KEY,
                    company_name TEXT DEFAULT '',  gstin TEXT DEFAULT '',
                    address TEXT DEFAULT '',       city TEXT DEFAULT '',
                    state TEXT DEFAULT '',         state_code TEXT DEFAULT '',
                    pincode TEXT DEFAULT '',       phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',         bank_name TEXT DEFAULT '',
                    account_no TEXT DEFAULT '',    ifsc_code TEXT DEFAULT '',
                    logo_path TEXT DEFAULT '',     signature_path TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gstin TEXT UNIQUE,
                    name TEXT NOT NULL,
                    address TEXT DEFAULT '',  city TEXT DEFAULT '',
                    state TEXT DEFAULT '',    state_code TEXT DEFAULT '',
                    pincode TEXT DEFAULT '',  phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    hsn_sac TEXT DEFAULT '',
                    unit TEXT DEFAULT 'PCS',
                    default_price REAL DEFAULT 0.0,
                    gst_rate REAL DEFAULT 18.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT UNIQUE NOT NULL,
                    invoice_date TEXT NOT NULL,
                    due_date TEXT DEFAULT '',
                    customer_gstin TEXT DEFAULT '',
                    customer_name TEXT NOT NULL,
                    customer_address TEXT DEFAULT '',
                    customer_city TEXT DEFAULT '',
                    customer_state TEXT DEFAULT '',
                    customer_state_code TEXT DEFAULT '',
                    customer_pincode TEXT DEFAULT '',
                    customer_phone TEXT DEFAULT '',
                    customer_email TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    cgst_total REAL DEFAULT 0.0,
                    sgst_total REAL DEFAULT 0.0,
                    igst_total REAL DEFAULT 0.0,
                    grand_total REAL DEFAULT 0.0,
                    round_off REAL DEFAULT 0.0,
                    is_igst INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    sno INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    hsn_sac TEXT DEFAULT '',
                    unit TEXT DEFAULT 'PCS',
                    qty REAL DEFAULT 1.0,
                    rate REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    gst_rate REAL DEFAULT 18.0,
                    cgst_rate REAL DEFAULT 0.0,  cgst_amount REAL DEFAULT 0.0,
                    sgst_rate REAL DEFAULT 0.0,  sgst_amount REAL DEFAULT 0.0,
                    igst_rate REAL DEFAULT 0.0,  igst_amount REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_date TEXT NOT NULL,
                    mode TEXT DEFAULT 'Cash',
                    reference TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    gstin TEXT DEFAULT '',
                    address TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    state TEXT DEFAULT '',
                    state_code TEXT DEFAULT '',
                    pincode TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    contact_person TEXT DEFAULT '',
                    payment_terms INTEGER DEFAULT 30,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    expense_date TEXT NOT NULL,
                    category TEXT DEFAULT 'General',
                    vendor_id INTEGER,
                    vendor_name TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    amount REAL DEFAULT 0.0,
                    gst_rate REAL DEFAULT 0.0,
                    gst_amount REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    payment_mode TEXT DEFAULT 'Cash',
                    reference TEXT DEFAULT '',
                    is_recurring INTEGER DEFAULT 0,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_no TEXT UNIQUE NOT NULL,
                    po_date TEXT NOT NULL,
                    expected_date TEXT DEFAULT '',
                    vendor_id INTEGER,
                    vendor_name TEXT NOT NULL,
                    vendor_gstin TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    tax_total REAL DEFAULT 0.0,
                    grand_total REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'Draft',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_no TEXT UNIQUE NOT NULL,
                    bill_date TEXT NOT NULL,
                    due_date TEXT DEFAULT '',
                    vendor_id INTEGER,
                    vendor_name TEXT NOT NULL,
                    vendor_gstin TEXT DEFAULT '',
                    subtotal REAL DEFAULT 0.0,
                    cgst_total REAL DEFAULT 0.0,
                    sgst_total REAL DEFAULT 0.0,
                    igst_total REAL DEFAULT 0.0,
                    grand_total REAL DEFAULT 0.0,
                    is_igst INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Unpaid',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS bill_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER NOT NULL,
                    sno INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    hsn_sac TEXT DEFAULT '',
                    unit TEXT DEFAULT 'PCS',
                    qty REAL DEFAULT 1.0,
                    rate REAL DEFAULT 0.0,
                    amount REAL DEFAULT 0.0,
                    gst_rate REAL DEFAULT 18.0,
                    cgst_rate REAL DEFAULT 0.0, cgst_amount REAL DEFAULT 0.0,
                    sgst_rate REAL DEFAULT 0.0, sgst_amount REAL DEFAULT 0.0,
                    igst_rate REAL DEFAULT 0.0, igst_amount REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bill_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    payment_date TEXT NOT NULL,
                    mode TEXT DEFAULT 'Cash',
                    reference TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_name TEXT NOT NULL,
                    bank_name TEXT DEFAULT '',
                    account_no TEXT DEFAULT '',
                    ifsc_code TEXT DEFAULT '',
                    account_type TEXT DEFAULT 'Current',
                    opening_balance REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS bank_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    txn_date TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    reference TEXT DEFAULT '',
                    debit REAL DEFAULT 0.0,
                    credit REAL DEFAULT 0.0,
                    balance REAL DEFAULT 0.0,
                    category TEXT DEFAULT '',
                    reconciled INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES bank_accounts(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS chart_of_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    parent_id INTEGER,
                    description TEXT DEFAULT '',
                    is_system INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_no TEXT UNIQUE NOT NULL,
                    entry_date TEXT NOT NULL,
                    narration TEXT DEFAULT '',
                    reference TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS journal_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_id INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    debit REAL DEFAULT 0.0,
                    credit REAL DEFAULT 0.0,
                    narration TEXT DEFAULT '',
                    FOREIGN KEY (journal_id) REFERENCES journal_entries(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    customer_id INTEGER,
                    customer_name TEXT DEFAULT '',
                    status TEXT DEFAULT 'Active',
                    billing_type TEXT DEFAULT 'Fixed',
                    budget REAL DEFAULT 0.0,
                    start_date TEXT DEFAULT '',
                    end_date TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS timesheets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    project_name TEXT DEFAULT '',
                    entry_date TEXT NOT NULL,
                    task TEXT DEFAULT '',
                    hours REAL DEFAULT 0.0,
                    rate REAL DEFAULT 0.0,
                    is_billable INTEGER DEFAULT 1,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    original_name TEXT DEFAULT '',
                    file_path TEXT DEFAULT '',
                    file_size INTEGER DEFAULT 0,
                    mime_type TEXT DEFAULT '',
                    related_type TEXT DEFAULT '',
                    related_id INTEGER DEFAULT 0,
                    description TEXT DEFAULT '',
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT DEFAULT '',
                email TEXT DEFAULT '',
                role TEXT DEFAULT 'admin',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );

            """)
            cnt = c.execute("SELECT COUNT(*) FROM company_profile").fetchone()[0]
            if cnt == 0:
                c.execute("INSERT INTO company_profile (id) VALUES (1)")
            # Migrations — add new columns to existing DBs safely
            self._migrate(c)

    def _migrate(self, c):
        """Add new columns to existing databases without breaking them."""
        existing = {row[1] for row in
                    c.execute("PRAGMA table_info(company_profile)").fetchall()}
        for col, defval in [("signature_path", "''"), ("logo_path", "''")]:
            if col not in existing:
                c.execute(f"ALTER TABLE company_profile ADD COLUMN {col} TEXT DEFAULT {defval}")
        # Seed default Chart of Accounts if empty
        cnt = c.execute("SELECT COUNT(*) FROM chart_of_accounts").fetchone()[0]
        if cnt == 0:
            accounts = [
                ('1000','Cash & Bank','Asset',None,1),('1100','Accounts Receivable','Asset',None,1),
                ('1200','Inventory','Asset',None,1),('2000','Accounts Payable','Liability',None,1),
                ('2100','GST Payable','Liability',None,1),('3000','Capital','Equity',None,1),
                ('4000','Sales Revenue','Income',None,1),('4100','Other Income','Income',None,1),
                ('5000','Cost of Goods Sold','Expense',None,1),('5100','Salaries','Expense',None,1),
                ('5200','Rent','Expense',None,1),('5300','Utilities','Expense',None,1),
                ('5400','Marketing','Expense',None,1),('5500','Office Expenses','Expense',None,1),
                ('5600','Travel','Expense',None,1),('5700','Depreciation','Expense',None,1),
            ]
            c.executemany("INSERT INTO chart_of_accounts (code,name,account_type,parent_id,is_system) VALUES (?,?,?,?,?)", accounts)

    # ═══════════════════════ Company ═══════════════════════════
    def get_company(self):
        with self._conn() as c:
            row = c.execute("SELECT * FROM company_profile WHERE id=1").fetchone()
            return dict(row) if row else {}

    def save_company(self, d):
        with self._conn() as c:
            c.execute("""UPDATE company_profile SET
                company_name=?, gstin=?, address=?, city=?, state=?, state_code=?,
                pincode=?, phone=?, email=?, bank_name=?, account_no=?, ifsc_code=?,
                logo_path=?, signature_path=?
                WHERE id=1""",
                (d.get('company_name',''), d.get('gstin',''), d.get('address',''),
                 d.get('city',''), d.get('state',''), d.get('state_code',''),
                 d.get('pincode',''), d.get('phone',''), d.get('email',''),
                 d.get('bank_name',''), d.get('account_no',''), d.get('ifsc_code',''),
                 d.get('logo_path',''), d.get('signature_path','')))

    # ═══════════════════════ Customers ═════════════════════════
    def fetch_customer_by_gstin(self, gstin: str):
        with self._conn() as c:
            row = c.execute("SELECT * FROM customers WHERE gstin=?",
                            (gstin.upper().strip(),)).fetchone()
            return dict(row) if row else None

    def save_customer(self, d):
        """Save or update customer. If GSTIN is blank, use name as key."""
        with self._conn() as c:
            gstin = (d.get('gstin','') or '').upper().strip()
            name  = d.get('name','')
            # Check if exists by GSTIN (if provided) or by name
            existing = None
            if gstin:
                existing = c.execute("SELECT id FROM customers WHERE gstin=?", (gstin,)).fetchone()
            else:
                existing = c.execute("SELECT id FROM customers WHERE name=? AND (gstin='' OR gstin IS NULL)", (name,)).fetchone()
            vals = (gstin, name, d.get('address',''), d.get('city',''), d.get('state',''),
                    d.get('state_code',''), d.get('pincode',''), d.get('phone',''), d.get('email',''))
            if existing:
                c.execute("""UPDATE customers SET gstin=?,name=?,address=?,city=?,state=?,
                    state_code=?,pincode=?,phone=?,email=?,updated_at=CURRENT_TIMESTAMP
                    WHERE id=?""", (*vals, existing['id']))
            else:
                c.execute("""INSERT INTO customers (gstin,name,address,city,state,state_code,pincode,phone,email)
                    VALUES (?,?,?,?,?,?,?,?,?)""", vals)

    def get_all_customers(self):
        with self._conn() as c:
            return [dict(r) for r in
                    c.execute("SELECT * FROM customers ORDER BY name").fetchall()]

    def delete_customer(self, gstin: str):
        with self._conn() as c:
            c.execute("DELETE FROM customers WHERE gstin=?", (gstin,))

    # ═══════════════════════ Products ══════════════════════════
    def save_product(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute("""UPDATE products SET name=?,description=?,hsn_sac=?,unit=?,
                    default_price=?,gst_rate=? WHERE id=?""",
                    (d['name'], d.get('description',''), d.get('hsn_sac',''),
                     d.get('unit','PCS'), float(d.get('default_price',0)),
                     float(d.get('gst_rate',18)), d['id']))
            else:
                c.execute("""INSERT INTO products (name,description,hsn_sac,unit,default_price,gst_rate)
                    VALUES (?,?,?,?,?,?)""",
                    (d['name'], d.get('description',''), d.get('hsn_sac',''),
                     d.get('unit','PCS'), float(d.get('default_price',0)),
                     float(d.get('gst_rate',18))))

    def get_all_products(self):
        with self._conn() as c:
            return [dict(r) for r in
                    c.execute("SELECT * FROM products ORDER BY name").fetchall()]

    def delete_product(self, pid: int):
        with self._conn() as c:
            c.execute("DELETE FROM products WHERE id=?", (pid,))

    # ═══════════════════════ Invoices ══════════════════════════
    def next_invoice_no(self):
        with self._conn() as c:
            cnt = c.execute("SELECT COALESCE(MAX(id),0) FROM invoices").fetchone()[0] + 1
            ym = datetime.now().strftime("%y%m")
            return f"INV-{ym}-{cnt:04d}"

    def save_invoice(self, inv: dict, items: list) -> int:
        with self._conn() as c:
            cur = c.execute("""INSERT INTO invoices
                (invoice_no,invoice_date,due_date,customer_gstin,customer_name,
                 customer_address,customer_city,customer_state,customer_state_code,
                 customer_pincode,customer_phone,customer_email,
                 subtotal,cgst_total,sgst_total,igst_total,grand_total,round_off,is_igst,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (inv['invoice_no'], inv['invoice_date'], inv.get('due_date',''),
                 inv.get('customer_gstin',''), inv['customer_name'],
                 inv.get('customer_address',''), inv.get('customer_city',''),
                 inv.get('customer_state',''), inv.get('customer_state_code',''),
                 inv.get('customer_pincode',''), inv.get('customer_phone',''),
                 inv.get('customer_email',''),
                 inv.get('subtotal',0), inv.get('cgst_total',0),
                 inv.get('sgst_total',0), inv.get('igst_total',0),
                 inv.get('grand_total',0), inv.get('round_off',0),
                 1 if inv.get('is_igst') else 0, inv.get('notes','')))
            iid = cur.lastrowid
            for it in items:
                c.execute("""INSERT INTO invoice_items
                    (invoice_id,sno,product_name,description,hsn_sac,unit,qty,rate,amount,
                     gst_rate,cgst_rate,cgst_amount,sgst_rate,sgst_amount,
                     igst_rate,igst_amount,total_amount)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (iid, it['sno'], it['product_name'], it.get('description',''),
                     it.get('hsn_sac',''), it.get('unit','PCS'),
                     it['qty'], it['rate'], it['amount'], it['gst_rate'],
                     it.get('cgst_rate',0), it.get('cgst_amount',0),
                     it.get('sgst_rate',0), it.get('sgst_amount',0),
                     it.get('igst_rate',0), it.get('igst_amount',0),
                     it['total_amount']))
            return iid

    def get_all_invoices(self):
        with self._conn() as c:
            rows = c.execute("""SELECT id,invoice_no,invoice_date,customer_name,
                customer_gstin,grand_total,created_at FROM invoices ORDER BY id DESC""").fetchall()
            return [dict(r) for r in rows]

    def get_all_invoices_with_status(self):
        """Return invoices enriched with paid amount and status."""
        with self._conn() as c:
            rows = c.execute("""
                SELECT i.id, i.invoice_no, i.invoice_date, i.customer_name,
                       i.customer_gstin, i.grand_total, i.created_at,
                       COALESCE(SUM(p.amount),0) AS paid_amount
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY i.id ORDER BY i.id DESC""").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                bal = round(d['grand_total'] - d['paid_amount'], 2)
                if bal <= 0:
                    d['status'] = 'Paid'
                elif d['paid_amount'] > 0:
                    d['status'] = 'Partial'
                else:
                    d['status'] = 'Unpaid'
                d['balance'] = max(bal, 0)
                result.append(d)
            return result

    def get_invoice(self, iid: int):
        with self._conn() as c:
            inv = c.execute("SELECT * FROM invoices WHERE id=?", (iid,)).fetchone()
            if not inv:
                return None
            d = dict(inv)
            d['items'] = [dict(r) for r in
                c.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY sno",
                          (iid,)).fetchall()]
            return d

    def delete_invoice(self, iid: int):
        with self._conn() as c:
            c.execute("DELETE FROM invoices WHERE id=?", (iid,))

    def search_invoices(self, q: str):
        with self._conn() as c:
            p = f"%{q}%"
            rows = c.execute("""SELECT id,invoice_no,invoice_date,customer_name,
                customer_gstin,grand_total,created_at FROM invoices
                WHERE invoice_no LIKE ? OR customer_name LIKE ? OR customer_gstin LIKE ?
                ORDER BY id DESC""", (p,p,p)).fetchall()
            return [dict(r) for r in rows]

    # ═══════════════════════ Payments ══════════════════════════
    def record_payment(self, invoice_id: int, amount: float, payment_date: str,
                       mode: str = 'Cash', reference: str = '', notes: str = ''):
        with self._conn() as c:
            c.execute("""INSERT INTO payments (invoice_id,amount,payment_date,mode,reference,notes)
                VALUES (?,?,?,?,?,?)""",
                (invoice_id, amount, payment_date, mode, reference, notes))

    def get_payments_for_invoice(self, invoice_id: int):
        with self._conn() as c:
            return [dict(r) for r in
                    c.execute("SELECT * FROM payments WHERE invoice_id=? ORDER BY payment_date",
                              (invoice_id,)).fetchall()]

    def get_invoice_balance(self, invoice_id: int) -> dict:
        with self._conn() as c:
            inv = c.execute("SELECT grand_total FROM invoices WHERE id=?",
                            (invoice_id,)).fetchone()
            if not inv:
                return {'grand_total': 0, 'paid': 0, 'balance': 0, 'status': 'Unknown'}
            paid = c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
                             (invoice_id,)).fetchone()[0]
            bal  = round(float(inv['grand_total']) - float(paid), 2)
            status = 'Paid' if bal <= 0 else ('Partial' if paid > 0 else 'Unpaid')
            return {'grand_total': inv['grand_total'], 'paid': paid,
                    'balance': max(bal, 0), 'status': status}

    def delete_payment(self, pid: int):
        with self._conn() as c:
            c.execute("DELETE FROM payments WHERE id=?", (pid,))

    # ═══════════════════════ Ledger / Reports ══════════════════
    def get_customer_ledger(self, customer_name: str):
        """All invoices + payments for a customer, date-sorted with running balance."""
        with self._conn() as c:
            invs = c.execute("""SELECT id,invoice_no,invoice_date,grand_total
                FROM invoices WHERE customer_name=? ORDER BY invoice_date,id""",
                (customer_name,)).fetchall()
            entries = []
            for inv in invs:
                entries.append({'date': inv['invoice_date'], 'type': 'Invoice',
                                'ref': inv['invoice_no'], 'debit': 0,
                                'credit': float(inv['grand_total']),
                                'invoice_id': inv['id']})
                for p in c.execute("SELECT * FROM payments WHERE invoice_id=? ORDER BY payment_date",
                                   (inv['id'],)).fetchall():
                    entries.append({'date': p['payment_date'], 'type': 'Payment',
                                    'ref': f"{p['mode']} {p['reference']}".strip(),
                                    'debit': float(p['amount']), 'credit': 0,
                                    'invoice_id': inv['id']})
            entries.sort(key=lambda x: x['date'])
            bal = 0.0
            for e in entries:
                bal += e['credit'] - e['debit']
                e['balance'] = round(bal, 2)
            return entries

    def get_customer_statement(self, customer_name: str, from_date: str, to_date: str):
        """Statement for a date range."""
        with self._conn() as c:
            invs = c.execute("""SELECT id,invoice_no,invoice_date,grand_total
                FROM invoices WHERE customer_name=?
                AND invoice_date BETWEEN ? AND ? ORDER BY invoice_date""",
                (customer_name, from_date, to_date)).fetchall()
            rows = []
            for inv in invs:
                paid = c.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE invoice_id=?",
                                 (inv['id'],)).fetchone()[0]
                rows.append({'date': inv['invoice_date'], 'invoice_no': inv['invoice_no'],
                             'amount': float(inv['grand_total']), 'paid': float(paid),
                             'balance': round(float(inv['grand_total']) - float(paid), 2)})
            return rows

    def get_outstanding_invoices(self):
        """All unpaid/partial invoices with days overdue."""
        from datetime import date
        today = date.today().isoformat()
        with self._conn() as c:
            rows = c.execute("""
                SELECT i.id, i.invoice_no, i.invoice_date, i.due_date,
                       i.customer_name, i.customer_gstin, i.grand_total,
                       COALESCE(SUM(p.amount),0) AS paid_amount
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY i.id
                HAVING grand_total - paid_amount > 0.005
                ORDER BY i.invoice_date""").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                bal = round(d['grand_total'] - d['paid_amount'], 2)
                d['balance'] = bal
                d['status'] = 'Partial' if d['paid_amount'] > 0 else 'Unpaid'
                ref_date = d.get('due_date') or d['invoice_date']
                try:
                    from datetime import date as dt
                    delta = (dt.fromisoformat(today) - dt.fromisoformat(ref_date)).days
                    d['days_overdue'] = max(delta, 0)
                except Exception:
                    d['days_overdue'] = 0
                result.append(d)
            return result

    def get_dashboard_stats(self):
        """Stats for dashboard cards."""
        from datetime import datetime, date
        today = date.today()
        month_start = today.replace(day=1).isoformat()
        with self._conn() as c:
            monthly_sales = c.execute(
                "SELECT COALESCE(SUM(grand_total),0) FROM invoices WHERE invoice_date >= ?",
                (month_start,)).fetchone()[0]
            total_invoices = c.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            total_customers = c.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
            gst_collected = c.execute(
                "SELECT COALESCE(SUM(cgst_total+sgst_total+igst_total),0) FROM invoices "
                "WHERE invoice_date >= ?", (month_start,)).fetchone()[0]
            outstanding = c.execute("""
                SELECT COALESCE(SUM(i.grand_total - COALESCE(p.paid,0)),0)
                FROM invoices i
                LEFT JOIN (SELECT invoice_id, SUM(amount) as paid FROM payments GROUP BY invoice_id) p
                ON p.invoice_id = i.id""").fetchone()[0]
            top_customers = c.execute("""
                SELECT customer_name, SUM(grand_total) as total, COUNT(*) as invoice_count
                FROM invoices GROUP BY customer_name
                ORDER BY total DESC LIMIT 5""").fetchall()
            recent_invoices = c.execute("""
                SELECT i.id, i.invoice_no, i.invoice_date, i.customer_name, i.grand_total,
                       COALESCE(SUM(p.amount),0) AS paid_amount
                FROM invoices i
                LEFT JOIN payments p ON p.invoice_id = i.id
                GROUP BY i.id ORDER BY i.id DESC LIMIT 8""").fetchall()
            recent = []
            for r in recent_invoices:
                d2 = dict(r)
                bal = round(d2['grand_total'] - d2['paid_amount'], 2)
                d2['status'] = 'Paid' if bal <= 0 else ('Partial' if d2['paid_amount'] > 0 else 'Unpaid')
                d2['balance'] = max(bal, 0)
                recent.append(d2)
            # Monthly sales for last 6 months
            monthly = []
            for i in range(5, -1, -1):
                from datetime import date as dt
                import calendar
                yr  = today.year if today.month - i > 0 else today.year - 1
                mo  = (today.month - i - 1) % 12 + 1
                s   = f"{yr}-{mo:02d}-01"
                _, last = calendar.monthrange(yr, mo)
                e   = f"{yr}-{mo:02d}-{last:02d}"
                sal = c.execute(
                    "SELECT COALESCE(SUM(grand_total),0) FROM invoices WHERE invoice_date BETWEEN ? AND ?",
                    (s, e)).fetchone()[0]
                gst_mo = c.execute(
                    "SELECT COALESCE(SUM(cgst_total+sgst_total+igst_total),0) FROM invoices WHERE invoice_date BETWEEN ? AND ?",
                    (s, e)).fetchone()[0]
                monthly.append({'month': f"{yr}-{mo:02d}", 'sales': float(sal), 'gst': float(gst_mo)})
            return {
                'monthly_sales': float(monthly_sales),
                'total_invoices': total_invoices,
                'total_customers': total_customers,
                'gst_collected': float(gst_collected),
                'outstanding': float(outstanding),
                'top_customers': [dict(r) for r in top_customers],
                'monthly_chart': monthly,
                'recent_invoices': recent,
            }

    # ===== Vendors =============================================
    def get_all_vendors(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM vendors ORDER BY name').fetchall()]

    def save_vendor(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute('UPDATE vendors SET name=?,gstin=?,address=?,city=?,state=?,state_code=?,pincode=?,phone=?,email=?,contact_person=?,payment_terms=? WHERE id=?',
                    (d['name'],d.get('gstin',''),d.get('address',''),d.get('city',''),d.get('state',''),d.get('state_code',''),d.get('pincode',''),d.get('phone',''),d.get('email',''),d.get('contact_person',''),int(d.get('payment_terms',30)),d['id']))
                return d['id']
            else:
                cur = c.execute('INSERT INTO vendors (name,gstin,address,city,state,state_code,pincode,phone,email,contact_person,payment_terms) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    (d['name'],d.get('gstin',''),d.get('address',''),d.get('city',''),d.get('state',''),d.get('state_code',''),d.get('pincode',''),d.get('phone',''),d.get('email',''),d.get('contact_person',''),int(d.get('payment_terms',30))))
                return cur.lastrowid

    def delete_vendor(self, vid):
        with self._conn() as c:
            c.execute('DELETE FROM vendors WHERE id=?', (vid,))

    # ===== Expenses ============================================
    def get_all_expenses(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM expenses ORDER BY expense_date DESC').fetchall()]

    def save_expense(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute('UPDATE expenses SET expense_date=?,category=?,vendor_id=?,vendor_name=?,description=?,amount=?,gst_rate=?,gst_amount=?,total_amount=?,payment_mode=?,reference=?,is_recurring=?,notes=? WHERE id=?',
                    (d['expense_date'],d.get('category','General'),d.get('vendor_id'),d.get('vendor_name',''),d.get('description',''),float(d.get('amount',0)),float(d.get('gst_rate',0)),float(d.get('gst_amount',0)),float(d.get('total_amount',0)),d.get('payment_mode','Cash'),d.get('reference',''),int(d.get('is_recurring',0)),d.get('notes',''),d['id']))
            else:
                c.execute('INSERT INTO expenses (expense_date,category,vendor_id,vendor_name,description,amount,gst_rate,gst_amount,total_amount,payment_mode,reference,is_recurring,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (d['expense_date'],d.get('category','General'),d.get('vendor_id'),d.get('vendor_name',''),d.get('description',''),float(d.get('amount',0)),float(d.get('gst_rate',0)),float(d.get('gst_amount',0)),float(d.get('total_amount',0)),d.get('payment_mode','Cash'),d.get('reference',''),int(d.get('is_recurring',0)),d.get('notes','')))

    def delete_expense(self, eid):
        with self._conn() as c:
            c.execute('DELETE FROM expenses WHERE id=?', (eid,))

    # ===== Bills ===============================================
    def next_bill_no(self):
        from datetime import datetime as _dt
        with self._conn() as c:
            cnt = c.execute('SELECT COALESCE(MAX(id),0) FROM bills').fetchone()[0] + 1
            return 'BILL-' + _dt.now().strftime('%y%m') + '-' + str(cnt).zfill(4)

    def get_all_bills(self):
        with self._conn() as c:
            rows = c.execute('SELECT b.id,b.bill_no,b.bill_date,b.due_date,b.vendor_name,b.grand_total,COALESCE(SUM(bp.amount),0) AS paid_amount FROM bills b LEFT JOIN bill_payments bp ON bp.bill_id=b.id GROUP BY b.id ORDER BY b.id DESC').fetchall()
            result = []
            for r in rows:
                d = dict(r); bal = round(d['grand_total'] - d['paid_amount'], 2)
                d['balance'] = max(bal, 0)
                d['status'] = 'Paid' if bal <= 0 else ('Partial' if d['paid_amount'] > 0 else 'Unpaid')
                result.append(d)
            return result

    def get_bill(self, bid):
        with self._conn() as c:
            b = c.execute('SELECT * FROM bills WHERE id=?', (bid,)).fetchone()
            if not b: return None
            d = dict(b)
            d['items'] = [dict(r) for r in c.execute('SELECT * FROM bill_items WHERE bill_id=? ORDER BY sno', (bid,)).fetchall()]
            d['payments'] = [dict(r) for r in c.execute('SELECT * FROM bill_payments WHERE bill_id=? ORDER BY payment_date', (bid,)).fetchall()]
            return d

    def save_bill(self, bill, items):
        with self._conn() as c:
            cur = c.execute('INSERT INTO bills (bill_no,bill_date,due_date,vendor_id,vendor_name,vendor_gstin,subtotal,cgst_total,sgst_total,igst_total,grand_total,is_igst,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (bill['bill_no'],bill['bill_date'],bill.get('due_date',''),bill.get('vendor_id'),bill['vendor_name'],bill.get('vendor_gstin',''),bill.get('subtotal',0),bill.get('cgst_total',0),bill.get('sgst_total',0),bill.get('igst_total',0),bill.get('grand_total',0),int(bill.get('is_igst',0)),bill.get('notes','')))
            bid = cur.lastrowid
            for it in items:
                c.execute('INSERT INTO bill_items (bill_id,sno,product_name,hsn_sac,unit,qty,rate,amount,gst_rate,cgst_rate,cgst_amount,sgst_rate,sgst_amount,igst_rate,igst_amount,total_amount) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (bid,it['sno'],it['product_name'],it.get('hsn_sac',''),it.get('unit','PCS'),it['qty'],it['rate'],it['amount'],it['gst_rate'],it.get('cgst_rate',0),it.get('cgst_amount',0),it.get('sgst_rate',0),it.get('sgst_amount',0),it.get('igst_rate',0),it.get('igst_amount',0),it['total_amount']))
            return bid

    def record_bill_payment(self, bid, amount, date, mode='Cash', ref='', notes=''):
        with self._conn() as c:
            c.execute('INSERT INTO bill_payments (bill_id,amount,payment_date,mode,reference,notes) VALUES (?,?,?,?,?,?)', (bid, amount, date, mode, ref, notes))

    def delete_bill(self, bid):
        with self._conn() as c:
            c.execute('DELETE FROM bills WHERE id=?', (bid,))

    # ===== Purchase Orders =====================================
    def next_po_no(self):
        from datetime import datetime as _dt
        with self._conn() as c:
            cnt = c.execute('SELECT COALESCE(MAX(id),0) FROM purchase_orders').fetchone()[0] + 1
            return 'PO-' + _dt.now().strftime('%y%m') + '-' + str(cnt).zfill(4)

    def get_all_purchase_orders(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM purchase_orders ORDER BY id DESC').fetchall()]

    def save_purchase_order(self, d):
        with self._conn() as c:
            cur = c.execute('INSERT INTO purchase_orders (po_no,po_date,expected_date,vendor_id,vendor_name,vendor_gstin,subtotal,tax_total,grand_total,status,notes) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                (d['po_no'],d['po_date'],d.get('expected_date',''),d.get('vendor_id'),d['vendor_name'],d.get('vendor_gstin',''),d.get('subtotal',0),d.get('tax_total',0),d.get('grand_total',0),d.get('status','Draft'),d.get('notes','')))
            return cur.lastrowid

    def delete_purchase_order(self, pid):
        with self._conn() as c:
            c.execute('DELETE FROM purchase_orders WHERE id=?', (pid,))

    # ===== Banking =============================================
    def get_all_bank_accounts(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM bank_accounts ORDER BY account_name').fetchall()]

    def save_bank_account(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute('UPDATE bank_accounts SET account_name=?,bank_name=?,account_no=?,ifsc_code=?,account_type=?,opening_balance=? WHERE id=?',
                    (d['account_name'],d.get('bank_name',''),d.get('account_no',''),d.get('ifsc_code',''),d.get('account_type','Current'),float(d.get('opening_balance',0)),d['id']))
                return d['id']
            else:
                cur = c.execute('INSERT INTO bank_accounts (account_name,bank_name,account_no,ifsc_code,account_type,opening_balance) VALUES (?,?,?,?,?,?)',
                    (d['account_name'],d.get('bank_name',''),d.get('account_no',''),d.get('ifsc_code',''),d.get('account_type','Current'),float(d.get('opening_balance',0))))
                return cur.lastrowid

    def delete_bank_account(self, aid):
        with self._conn() as c:
            c.execute('DELETE FROM bank_accounts WHERE id=?', (aid,))

    def get_bank_transactions(self, account_id):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM bank_transactions WHERE account_id=? ORDER BY txn_date DESC', (account_id,)).fetchall()]

    def add_bank_transaction(self, d):
        with self._conn() as c:
            cur = c.execute('INSERT INTO bank_transactions (account_id,txn_date,description,reference,debit,credit,balance,category,reconciled) VALUES (?,?,?,?,?,?,?,?,?)',
                (d['account_id'],d['txn_date'],d.get('description',''),d.get('reference',''),float(d.get('debit',0)),float(d.get('credit',0)),float(d.get('balance',0)),d.get('category',''),int(d.get('reconciled',0))))
            return cur.lastrowid

    # ===== Chart of Accounts & Journals ========================
    def get_all_accounts(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM chart_of_accounts ORDER BY code').fetchall()]

    def save_account(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute('UPDATE chart_of_accounts SET code=?,name=?,account_type=?,parent_id=?,description=? WHERE id=?',
                    (d['code'],d['name'],d['account_type'],d.get('parent_id'),d.get('description',''),d['id']))
                return d['id']
            else:
                cur = c.execute('INSERT INTO chart_of_accounts (code,name,account_type,parent_id,description) VALUES (?,?,?,?,?)',
                    (d['code'],d['name'],d['account_type'],d.get('parent_id'),d.get('description','')))
                return cur.lastrowid

    def delete_account(self, aid):
        with self._conn() as c:
            c.execute('DELETE FROM chart_of_accounts WHERE id=? AND is_system=0', (aid,))

    def next_journal_no(self):
        with self._conn() as c:
            cnt = c.execute('SELECT COALESCE(MAX(id),0) FROM journal_entries').fetchone()[0] + 1
            return 'JE-' + str(cnt).zfill(4)

    def get_all_journals(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM journal_entries ORDER BY id DESC').fetchall()]

    def get_journal(self, jid):
        with self._conn() as c:
            j = c.execute('SELECT * FROM journal_entries WHERE id=?', (jid,)).fetchone()
            if not j: return None
            d = dict(j)
            d['lines'] = [dict(r) for r in c.execute(
                'SELECT jl.*,coa.name as account_name,coa.code as account_code FROM journal_lines jl JOIN chart_of_accounts coa ON coa.id=jl.account_id WHERE jl.journal_id=?', (jid,)).fetchall()]
            return d

    def save_journal(self, entry, lines):
        with self._conn() as c:
            cur = c.execute('INSERT INTO journal_entries (entry_no,entry_date,narration,reference) VALUES (?,?,?,?)',
                (entry['entry_no'],entry['entry_date'],entry.get('narration',''),entry.get('reference','')))
            jid = cur.lastrowid
            for ln in lines:
                c.execute('INSERT INTO journal_lines (journal_id,account_id,debit,credit,narration) VALUES (?,?,?,?,?)',
                    (jid,ln['account_id'],float(ln.get('debit',0)),float(ln.get('credit',0)),ln.get('narration','')))
            return jid

    def delete_journal(self, jid):
        with self._conn() as c:
            c.execute('DELETE FROM journal_entries WHERE id=?', (jid,))

    def get_trial_balance(self):
        with self._conn() as c:
            rows = c.execute(
                'SELECT coa.id,coa.code,coa.name,coa.account_type,COALESCE(SUM(jl.debit),0) as total_debit,COALESCE(SUM(jl.credit),0) as total_credit '
                'FROM chart_of_accounts coa LEFT JOIN journal_lines jl ON jl.account_id=coa.id GROUP BY coa.id ORDER BY coa.code').fetchall()
            return [dict(r) for r in rows]

    # ===== Projects & Timesheets ===============================
    def get_all_projects(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM projects ORDER BY id DESC').fetchall()]

    def save_project(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute('UPDATE projects SET name=?,customer_id=?,customer_name=?,status=?,billing_type=?,budget=?,start_date=?,end_date=?,description=? WHERE id=?',
                    (d['name'],d.get('customer_id'),d.get('customer_name',''),d.get('status','Active'),d.get('billing_type','Fixed'),float(d.get('budget',0)),d.get('start_date',''),d.get('end_date',''),d.get('description',''),d['id']))
                return d['id']
            else:
                cur = c.execute('INSERT INTO projects (name,customer_id,customer_name,status,billing_type,budget,start_date,end_date,description) VALUES (?,?,?,?,?,?,?,?,?)',
                    (d['name'],d.get('customer_id'),d.get('customer_name',''),d.get('status','Active'),d.get('billing_type','Fixed'),float(d.get('budget',0)),d.get('start_date',''),d.get('end_date',''),d.get('description','')))
                return cur.lastrowid

    def delete_project(self, pid):
        with self._conn() as c:
            c.execute('DELETE FROM projects WHERE id=?', (pid,))

    def get_all_timesheets(self, project_id=None):
        with self._conn() as c:
            if project_id:
                return [dict(r) for r in c.execute('SELECT * FROM timesheets WHERE project_id=? ORDER BY entry_date DESC', (project_id,)).fetchall()]
            return [dict(r) for r in c.execute('SELECT * FROM timesheets ORDER BY entry_date DESC').fetchall()]

    def save_timesheet(self, d):
        with self._conn() as c:
            if d.get('id'):
                c.execute('UPDATE timesheets SET project_id=?,project_name=?,entry_date=?,task=?,hours=?,rate=?,is_billable=?,notes=? WHERE id=?',
                    (d.get('project_id'),d.get('project_name',''),d['entry_date'],d.get('task',''),float(d.get('hours',0)),float(d.get('rate',0)),int(d.get('is_billable',1)),d.get('notes',''),d['id']))
            else:
                c.execute('INSERT INTO timesheets (project_id,project_name,entry_date,task,hours,rate,is_billable,notes) VALUES (?,?,?,?,?,?,?,?)',
                    (d.get('project_id'),d.get('project_name',''),d['entry_date'],d.get('task',''),float(d.get('hours',0)),float(d.get('rate',0)),int(d.get('is_billable',1)),d.get('notes','')))

    def delete_timesheet(self, tid):
        with self._conn() as c:
            c.execute('DELETE FROM timesheets WHERE id=?', (tid,))

    # ===== Documents ===========================================
    def get_all_documents(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT * FROM documents ORDER BY uploaded_at DESC').fetchall()]

    def save_document(self, d):
        with self._conn() as c:
            cur = c.execute('INSERT INTO documents (filename,original_name,file_path,file_size,mime_type,related_type,related_id,description) VALUES (?,?,?,?,?,?,?,?)',
                (d['filename'],d.get('original_name',''),d.get('file_path',''),int(d.get('file_size',0)),d.get('mime_type',''),d.get('related_type',''),int(d.get('related_id',0)),d.get('description','')))
            return cur.lastrowid

    def delete_document(self, did):
        with self._conn() as c:
            c.execute('DELETE FROM documents WHERE id=?', (did,))

    # ===== Reports =============================================
    def get_pl_report(self, from_date, to_date):
        with self._conn() as c:
            income = float(c.execute('SELECT COALESCE(SUM(grand_total),0) FROM invoices WHERE invoice_date BETWEEN ? AND ?', (from_date, to_date)).fetchone()[0])
            exp_d = float(c.execute('SELECT COALESCE(SUM(total_amount),0) FROM expenses WHERE expense_date BETWEEN ? AND ?', (from_date, to_date)).fetchone()[0])
            bills_t = float(c.execute('SELECT COALESCE(SUM(grand_total),0) FROM bills WHERE bill_date BETWEEN ? AND ?', (from_date, to_date)).fetchone()[0])
            exp_cat = c.execute('SELECT category,COALESCE(SUM(total_amount),0) as total FROM expenses WHERE expense_date BETWEEN ? AND ? GROUP BY category', (from_date, to_date)).fetchall()
            by_month = c.execute("SELECT strftime('%Y-%m',invoice_date) as month,COALESCE(SUM(grand_total),0) as total FROM invoices WHERE invoice_date BETWEEN ? AND ? GROUP BY month ORDER BY month", (from_date, to_date)).fetchall()
            return {'income': income, 'expenses': exp_d + bills_t, 'net_profit': round(income - exp_d - bills_t, 2),
                    'expenses_by_category': [dict(r) for r in exp_cat], 'income_by_month': [dict(r) for r in by_month]}

    def get_gst_report(self, from_date, to_date):
        with self._conn() as c:
            rows = c.execute(
                'SELECT ii.hsn_sac,ii.gst_rate,COALESCE(SUM(ii.amount),0) as taxable_value,COALESCE(SUM(ii.cgst_amount),0) as cgst,'
                'COALESCE(SUM(ii.sgst_amount),0) as sgst,COALESCE(SUM(ii.igst_amount),0) as igst,COALESCE(SUM(ii.total_amount),0) as total '
                'FROM invoice_items ii JOIN invoices i ON i.id=ii.invoice_id WHERE i.invoice_date BETWEEN ? AND ? GROUP BY ii.hsn_sac,ii.gst_rate ORDER BY ii.hsn_sac',
                (from_date, to_date)).fetchall()
            summary = c.execute(
                'SELECT COALESCE(SUM(subtotal),0) as taxable,COALESCE(SUM(cgst_total),0) as cgst,COALESCE(SUM(sgst_total),0) as sgst,'
                'COALESCE(SUM(igst_total),0) as igst,COALESCE(SUM(grand_total),0) as total FROM invoices WHERE invoice_date BETWEEN ? AND ?',
                (from_date, to_date)).fetchone()
            return {'rows': [dict(r) for r in rows], 'summary': dict(summary)}

    def get_sales_report(self, from_date, to_date):
        with self._conn() as c:
            by_customer = c.execute('SELECT customer_name,COUNT(*) as invoices,SUM(grand_total) as total FROM invoices WHERE invoice_date BETWEEN ? AND ? GROUP BY customer_name ORDER BY total DESC', (from_date, to_date)).fetchall()
            by_month = c.execute("SELECT strftime('%Y-%m',invoice_date) as month,COUNT(*) as count,SUM(grand_total) as total FROM invoices WHERE invoice_date BETWEEN ? AND ? GROUP BY month ORDER BY month", (from_date, to_date)).fetchall()
            top_products = c.execute(
                'SELECT ii.product_name,SUM(ii.qty) as qty,SUM(ii.total_amount) as total FROM invoice_items ii JOIN invoices i ON i.id=ii.invoice_id '
                'WHERE i.invoice_date BETWEEN ? AND ? GROUP BY ii.product_name ORDER BY total DESC LIMIT 10', (from_date, to_date)).fetchall()
            return {'by_customer': [dict(r) for r in by_customer], 'by_month': [dict(r) for r in by_month], 'top_products': [dict(r) for r in top_products]}

    # ===== Users / Auth ========================================
    def get_user_by_username(self, username):
        with self._conn() as c:
            row = c.execute('SELECT * FROM users WHERE username=? AND is_active=1', (username,)).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, uid):
        with self._conn() as c:
            row = c.execute('SELECT id,username,full_name,email,role,created_at,last_login FROM users WHERE id=?', (uid,)).fetchone()
            return dict(row) if row else None

    def create_user(self, username, password_hash, full_name='', email='', role='admin'):
        with self._conn() as c:
            try:
                cur = c.execute('INSERT INTO users (username,password_hash,full_name,email,role) VALUES (?,?,?,?,?)',
                    (username, password_hash, full_name, email, role))
                return cur.lastrowid
            except Exception:
                return None

    def update_user_login(self, uid):
        with self._conn() as c:
            c.execute('UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?', (uid,))

    def update_user_profile(self, uid, full_name, email):
        with self._conn() as c:
            c.execute('UPDATE users SET full_name=?,email=? WHERE id=?', (full_name, email, uid))

    def change_user_password(self, uid, new_hash):
        with self._conn() as c:
            c.execute('UPDATE users SET password_hash=? WHERE id=?', (new_hash, uid))

    def get_all_users(self):
        with self._conn() as c:
            return [dict(r) for r in c.execute('SELECT id,username,full_name,email,role,is_active,created_at,last_login FROM users ORDER BY id').fetchall()]

    # ===== Search =============================================
    def search_customers(self, q):
        with self._conn() as c:
            q_like = f'%{q}%'
            return [dict(r) for r in c.execute(
                "SELECT * FROM customers WHERE name LIKE ? OR gstin LIKE ? OR city LIKE ? OR phone LIKE ? ORDER BY name LIMIT 20",
                (q_like, q_like, q_like, q_like)).fetchall()]

    def search_products(self, q):
        with self._conn() as c:
            q_like = f'%{q}%'
            return [dict(r) for r in c.execute(
                "SELECT * FROM products WHERE name LIKE ? OR hsn_sac LIKE ? OR description LIKE ? ORDER BY name LIMIT 20",
                (q_like, q_like, q_like)).fetchall()]

    def get_recent_customers(self, limit=5):
        """Get customers used in recent invoices."""
        with self._conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT DISTINCT c.* FROM customers c JOIN invoices i ON c.gstin = i.customer_gstin OR c.name = i.customer_name ORDER BY i.id DESC LIMIT ?",
                (limit,)).fetchall()]
