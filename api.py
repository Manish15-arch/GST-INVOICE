# -*- coding: utf-8 -*-
"""
api.py  —  FastAPI REST backend for the GST Billing Suite
Run:  uvicorn api:app --reload --port 8000
"""
import os, sys, tempfile, json, shutil, hashlib, secrets, time
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
from pydantic import BaseModel

from database import Database
from invoice_engine import (amount_in_words, state_from_gstin,
                             calc_item_tax, compute_totals, validate_gstin)

# ── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(title="GST Billing Suite", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

db = Database()
db.initialize()

# ── Authentication ────────────────────────────────────────────────────────────
_JWT_SECRET = os.environ.get('JWT_SECRET', 'gst-suite-secret-' + secrets.token_hex(8))
_TOKEN_EXPIRY = 86400 * 7  # 7 days

def _hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _make_token(user_id: int) -> str:
    import base64
    payload = json.dumps({'uid': user_id, 'exp': int(time.time()) + _TOKEN_EXPIRY})
    sig = hashlib.sha256((payload + _JWT_SECRET).encode()).hexdigest()[:16]
    return base64.urlsafe_b64encode(f'{payload}|{sig}'.encode()).decode()

def _verify_token(token: str):
    import base64
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        payload_str, sig = decoded.rsplit('|', 1)
        expected_sig = hashlib.sha256((payload_str + _JWT_SECRET).encode()).hexdigest()[:16]
        if sig != expected_sig:
            return None
        payload = json.loads(payload_str)
        if payload.get('exp', 0) < time.time():
            return None
        return payload.get('uid')
    except Exception:
        return None

# Seed default admin user if none exists
_default_admin = db.get_user_by_username('admin')
if not _default_admin:
    db.create_user('admin', _hash_pw('admin123'), 'Administrator', '', 'admin')
    print('[AUTH] Created default admin user (username: admin, password: admin123)')

class LoginIn(BaseModel):
    username: str
    password: str

class RegisterIn(BaseModel):
    username: str
    password: str
    full_name: str = ''
    email: str = ''

@app.post('/api/auth/login')
def login(data: LoginIn):
    user = db.get_user_by_username(data.username)
    if not user or user['password_hash'] != _hash_pw(data.password):
        raise HTTPException(401, 'Invalid username or password')
    db.update_user_login(user['id'])
    token = _make_token(user['id'])
    return {'token': token, 'user': {'id': user['id'], 'username': user['username'],
            'full_name': user['full_name'], 'email': user['email'], 'role': user['role']}}

@app.post('/api/auth/register')
def register(data: RegisterIn):
    if db.get_user_by_username(data.username):
        raise HTTPException(400, 'Username already taken')
    uid = db.create_user(data.username, _hash_pw(data.password), data.full_name, data.email)
    if not uid:
        raise HTTPException(500, 'Could not create user')
    token = _make_token(uid)
    return {'token': token, 'user': {'id': uid, 'username': data.username,
            'full_name': data.full_name, 'email': data.email, 'role': 'admin'}}

@app.get('/api/auth/me')
def get_me(authorization: str = ''):
    from fastapi import Header
    return {'error': 'Use header'}

@app.get('/api/auth/verify')
def verify_token_route(token: str = Query('')):
    uid = _verify_token(token)
    if not uid:
        raise HTTPException(401, 'Invalid or expired token')
    user = db.get_user_by_id(uid)
    if not user:
        raise HTTPException(401, 'User not found')
    return {'user': user}

@app.post('/api/auth/change-password')
def change_password(data: dict):
    token = data.get('token', '')
    uid = _verify_token(token)
    if not uid:
        raise HTTPException(401, 'Invalid token')
    old_pw = data.get('old_password', '')
    new_pw = data.get('new_password', '')
    user = db.get_user_by_username_raw(uid)
    db.change_user_password(uid, _hash_pw(new_pw))
    return {'ok': True}


# ── Pydantic models ──────────────────────────────────────────────────────────
class InvoiceItem(BaseModel):
    sno:          int
    product_name: str
    hsn_sac:      str   = ""
    unit:         str   = "NOS"
    qty:          float = 1
    rate:         float = 0
    gst_rate:     float = 18
    amount:       float = 0
    cgst_rate:    float = 0
    cgst_amount:  float = 0
    sgst_rate:    float = 0
    sgst_amount:  float = 0
    igst_rate:    float = 0
    igst_amount:  float = 0
    total_amount: float = 0

class InvoiceIn(BaseModel):
    invoice_no:         str
    invoice_date:       str
    customer_name:      str
    customer_gstin:     str  = ""
    customer_address:   str  = ""
    customer_city:      str  = ""
    customer_state:     str  = ""
    customer_state_code:str  = ""
    customer_pincode:   str  = ""
    customer_phone:     str  = ""
    customer_email:     str  = ""
    is_igst:            int  = 0
    subtotal:           float= 0
    cgst_total:         float= 0
    sgst_total:         float= 0
    igst_total:         float= 0
    round_off:          float= 0
    grand_total:        float= 0
    amount_in_words:    str  = ""
    notes:              str  = ""
    items:              List[InvoiceItem] = []

class PaymentIn(BaseModel):
    amount:       float
    payment_date: str
    mode:         str  = "Cash"
    reference:    str  = ""
    notes:        str  = ""

class CustomerIn(BaseModel):
    name:         str
    gstin:        str  = ""
    address:      str  = ""
    city:         str  = ""
    state:        str  = ""
    state_code:   str  = ""
    pincode:      str  = ""
    phone:        str  = ""
    email:        str  = ""

class ProductIn(BaseModel):
    id:           Optional[int] = None
    name:         str
    hsn_sac:      str   = ""
    unit:         str   = "NOS"
    default_price:float = 0
    price:        float = 0   # alias accepted from frontend
    gst_rate:     float = 18

class CompanyIn(BaseModel):
    company_name: str  = ""
    gstin:        str  = ""
    address:      str  = ""
    city:         str  = ""
    state:        str  = ""
    state_code:   str  = ""
    pincode:      str  = ""
    phone:        str  = ""
    email:        str  = ""
    bank_name:    str  = ""
    account_no:   str  = ""
    ifsc_code:    str  = ""
    logo_path:    str  = ""
    signature_path:str = ""

# ── HELPERS ──────────────────────────────────────────────────────────────────
def _row(r):
    """sqlite Row → plain dict."""
    if r is None: return None
    if isinstance(r, dict): return r
    return dict(r)

def _rows(rs):
    return [_row(r) for r in (rs or [])]

def _tmp_pdf():
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    f.close()
    return f.name

# ════════════════════════════════════════════════════════════════════════════
# COMPANY
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/company")
def get_company():
    return _row(db.get_company()) or {}

@app.post("/api/company")
def save_company(data: CompanyIn):
    db.save_company(data.dict())
    return {"ok": True}

# ════════════════════════════════════════════════════════════════════════════
# CUSTOMERS
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/customers")
def list_customers(search: str = '', recent: bool = False):
    if recent:
        return _rows(db.get_recent_customers())
    if search:
        return _rows(db.search_customers(search))
    return _rows(db.get_all_customers())

@app.post("/api/customers")
def upsert_customer(data: CustomerIn):
    db.save_customer(data.dict())
    return {"ok": True}

@app.delete("/api/customers/{gstin}")
def del_customer(gstin: str):
    db.delete_customer(gstin)
    return {"ok": True}

@app.get("/api/customers/gstin/{gstin}")
def lookup_customer(gstin: str):
    c = db.fetch_customer_by_gstin(gstin)
    if not c: raise HTTPException(404, "Customer not found")
    return _row(c)

# ════════════════════════════════════════════════════════════════════════════
# PRODUCTS
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/products")
def list_products(search: str = ''):
    if search:
        return _rows(db.search_products(search))
    return _rows(db.get_all_products())

@app.post("/api/products")
def upsert_product(data: ProductIn):
    d = data.dict()
    # resolve price → default_price
    if not d.get('default_price') and d.get('price'):
        d['default_price'] = d['price']
    db.save_product(d)
    return {"ok": True}

@app.delete("/api/products/{pid}")
def del_product(pid: int):
    db.delete_product(pid)
    return {"ok": True}

# ════════════════════════════════════════════════════════════════════════════
# INVOICES
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/invoices")
def list_invoices():
    return _rows(db.get_all_invoices_with_status())

@app.get("/api/invoices/next-number")
def next_inv_no():
    return {"invoice_no": db.next_invoice_no()}

@app.get("/api/invoices/{iid}")
def get_invoice(iid: int):
    inv = db.get_invoice(iid)
    if not inv: raise HTTPException(404, "Invoice not found")
    return _row(inv)

@app.post("/api/invoices")
def create_invoice(data: InvoiceIn):
    inv_dict  = data.dict(exclude={"items"})
    items_list = [i.dict() for i in data.items]
    iid = db.save_invoice(inv_dict, items_list)
    return {"id": iid, "invoice_no": data.invoice_no}

@app.delete("/api/invoices/{iid}")
def delete_invoice(iid: int):
    db.delete_invoice(iid)
    return {"ok": True}

# ── PDF export ───────────────────────────────────────────────────────────────
@app.get("/api/invoices/{iid}/pdf")
def export_pdf(iid: int, format: str = Query("modern", regex="^(modern|tally)$")):
    inv = db.get_invoice(iid)
    if not inv: raise HTTPException(404)
    inv = _row(inv)
    inv['company'] = _row(db.get_company()) or {}
    p = _tmp_pdf()
    if format == "tally":
        from tally_pdf import generate_tally_pdf
        generate_tally_pdf(inv, p)
    else:
        from pdf_exporter import generate_pdf
        generate_pdf(inv, p)
    return FileResponse(p, filename=f"{inv['invoice_no']}.pdf",
                        media_type="application/pdf")

# ── XML export ───────────────────────────────────────────────────────────────
@app.get("/api/invoices/{iid}/xml")
def export_xml(iid: int):
    inv = db.get_invoice(iid)
    if not inv: raise HTTPException(404)
    inv = _row(inv)
    inv['company'] = _row(db.get_company()) or {}
    from tally_exporter import generate_tally_xml
    xml_str = generate_tally_xml(inv)
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.xml', mode='w', encoding='utf-8')
    f.write(xml_str); f.close()
    return FileResponse(f.name, filename=f"{inv['invoice_no']}.xml",
                        media_type="application/xml")

# ════════════════════════════════════════════════════════════════════════════
# PAYMENTS
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/invoices/{iid}/payments")
def list_payments(iid: int):
    return _rows(db.get_payments_for_invoice(iid))

@app.post("/api/invoices/{iid}/payments")
def add_payment(iid: int, data: PaymentIn):
    inv = db.get_invoice(iid)
    if not inv: raise HTTPException(404)
    db.record_payment(iid, data.amount, data.payment_date,
                      data.mode, data.reference, data.notes)
    return {"ok": True}

@app.delete("/api/payments/{pid}")
def del_payment(pid: int):
    db.delete_payment(pid)
    return {"ok": True}

# ════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/dashboard")
def dashboard():
    return _row(db.get_dashboard_stats()) or {}

# ════════════════════════════════════════════════════════════════════════════
# OUTSTANDING
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/outstanding")
def outstanding():
    return _rows(db.get_outstanding_invoices())

# ════════════════════════════════════════════════════════════════════════════
# LEDGER
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/ledger")
def ledger(customer: str = Query(...)):
    return _rows(db.get_customer_ledger(customer))

@app.get("/api/ledger/pdf")
def ledger_pdf(customer: str = Query(...)):
    entries = _rows(db.get_customer_ledger(customer))
    company = _row(db.get_company()) or {}
    p = _tmp_pdf()
    from pdf_exporter import generate_ledger_pdf
    generate_ledger_pdf(customer, entries, company, p)
    return FileResponse(p, filename=f"ledger_{customer}.pdf",
                        media_type="application/pdf")

# ════════════════════════════════════════════════════════════════════════════
# STATEMENT
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/statement")
def statement(customer: str = Query(...),
              from_date: str = Query(...),
              to_date: str   = Query(...)):
    rows = _rows(db.get_customer_statement(customer, from_date, to_date))
    return rows

@app.get("/api/statement/pdf")
def statement_pdf(customer: str = Query(...),
                  from_date: str = Query(...),
                  to_date: str   = Query(...)):
    rows    = _rows(db.get_customer_statement(customer, from_date, to_date))
    company = _row(db.get_company()) or {}
    p = _tmp_pdf()
    from pdf_exporter import generate_statement_pdf
    generate_statement_pdf(customer, rows, from_date, to_date, company, p)
    return FileResponse(p, filename=f"statement_{customer}.pdf",
                        media_type="application/pdf")

@app.get("/api/statement/excel")
def statement_excel(customer: str = Query(...),
                    from_date: str = Query(...),
                    to_date: str   = Query(...)):
    rows    = _rows(db.get_customer_statement(customer, from_date, to_date))
    company = _row(db.get_company()) or {}
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    f.close()
    from excel_exporter import generate_statement_excel
    generate_statement_excel(customer, rows, from_date, to_date, company, f.name)
    return FileResponse(f.name, filename=f"statement_{customer}.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ════════════════════════════════════════════════════════════════════════════
@app.get("/api/gstin/{gstin}")
def gstin_info(gstin: str):
    sc, sname = state_from_gstin(gstin)
    valid = validate_gstin(gstin)
    return {"state_code": sc, "state_name": sname, "valid": valid}

@app.post("/api/compute-tax")
def compute_tax(data: dict):
    items    = data.get("items", [])
    is_igst  = bool(data.get("is_igst", 0))
    return compute_totals(items, is_igst)

@app.get("/api/amount-in-words/{amount}")
def get_words(amount: float):
    return {"words": amount_in_words(amount)}

# ════════════════════════════════════════════════════════════════════════════
# VENDORS
# ════════════════════════════════════════════════════════════════════════════
class VendorIn(BaseModel):
    id: Optional[int] = None
    name: str
    gstin: str = ''
    address: str = ''
    city: str = ''
    state: str = ''
    state_code: str = ''
    pincode: str = ''
    phone: str = ''
    email: str = ''
    contact_person: str = ''
    payment_terms: int = 30

@app.get('/api/vendors')
def list_vendors():
    return _rows(db.get_all_vendors())

@app.post('/api/vendors')
def upsert_vendor(data: VendorIn):
    vid = db.save_vendor(data.dict())
    return {'ok': True, 'id': vid}

@app.delete('/api/vendors/{vid}')
def del_vendor(vid: int):
    db.delete_vendor(vid)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# EXPENSES
# ════════════════════════════════════════════════════════════════════════════
class ExpenseIn(BaseModel):
    id: Optional[int] = None
    expense_date: str
    category: str = 'General'
    vendor_id: Optional[int] = None
    vendor_name: str = ''
    description: str = ''
    amount: float = 0
    gst_rate: float = 0
    gst_amount: float = 0
    total_amount: float = 0
    payment_mode: str = 'Cash'
    reference: str = ''
    is_recurring: int = 0
    notes: str = ''

@app.get('/api/expenses')
def list_expenses():
    return _rows(db.get_all_expenses())

@app.post('/api/expenses')
def upsert_expense(data: ExpenseIn):
    db.save_expense(data.dict())
    return {'ok': True}

@app.delete('/api/expenses/{eid}')
def del_expense(eid: int):
    db.delete_expense(eid)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# BILLS
# ════════════════════════════════════════════════════════════════════════════
class BillItem(BaseModel):
    sno: int
    product_name: str
    hsn_sac: str = ''
    unit: str = 'PCS'
    qty: float = 1
    rate: float = 0
    amount: float = 0
    gst_rate: float = 18
    cgst_rate: float = 0; cgst_amount: float = 0
    sgst_rate: float = 0; sgst_amount: float = 0
    igst_rate: float = 0; igst_amount: float = 0
    total_amount: float = 0

class BillIn(BaseModel):
    bill_no: str
    bill_date: str
    due_date: str = ''
    vendor_id: Optional[int] = None
    vendor_name: str
    vendor_gstin: str = ''
    is_igst: int = 0
    subtotal: float = 0
    cgst_total: float = 0
    sgst_total: float = 0
    igst_total: float = 0
    grand_total: float = 0
    notes: str = ''
    items: List[BillItem] = []

class BillPaymentIn(BaseModel):
    amount: float
    payment_date: str
    mode: str = 'Cash'
    reference: str = ''
    notes: str = ''

@app.get('/api/bills')
def list_bills():
    return _rows(db.get_all_bills())

@app.get('/api/bills/next-number')
def next_bill_no():
    return {'bill_no': db.next_bill_no()}

@app.get('/api/bills/{bid}')
def get_bill(bid: int):
    b = db.get_bill(bid)
    if not b: raise HTTPException(404, 'Bill not found')
    return _row(b)

@app.post('/api/bills')
def create_bill(data: BillIn):
    bill_dict = data.dict(exclude={'items'})
    items_list = [i.dict() for i in data.items]
    bid = db.save_bill(bill_dict, items_list)
    return {'id': bid, 'bill_no': data.bill_no}

@app.delete('/api/bills/{bid}')
def delete_bill(bid: int):
    db.delete_bill(bid)
    return {'ok': True}

@app.post('/api/bills/{bid}/payments')
def add_bill_payment(bid: int, data: BillPaymentIn):
    b = db.get_bill(bid)
    if not b: raise HTTPException(404)
    db.record_bill_payment(bid, data.amount, data.payment_date, data.mode, data.reference, data.notes)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# PURCHASE ORDERS
# ════════════════════════════════════════════════════════════════════════════
class POIn(BaseModel):
    po_no: str
    po_date: str
    expected_date: str = ''
    vendor_id: Optional[int] = None
    vendor_name: str
    vendor_gstin: str = ''
    subtotal: float = 0
    tax_total: float = 0
    grand_total: float = 0
    status: str = 'Draft'
    notes: str = ''

@app.get('/api/purchase-orders')
def list_pos():
    return _rows(db.get_all_purchase_orders())

@app.get('/api/purchase-orders/next-number')
def next_po_no():
    return {'po_no': db.next_po_no()}

@app.post('/api/purchase-orders')
def create_po(data: POIn):
    pid = db.save_purchase_order(data.dict())
    return {'id': pid, 'po_no': data.po_no}

@app.delete('/api/purchase-orders/{pid}')
def delete_po(pid: int):
    db.delete_purchase_order(pid)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# BANKING
# ════════════════════════════════════════════════════════════════════════════
class BankAccountIn(BaseModel):
    id: Optional[int] = None
    account_name: str
    bank_name: str = ''
    account_no: str = ''
    ifsc_code: str = ''
    account_type: str = 'Current'
    opening_balance: float = 0

class BankTxnIn(BaseModel):
    account_id: int
    txn_date: str
    description: str = ''
    reference: str = ''
    debit: float = 0
    credit: float = 0
    balance: float = 0
    category: str = ''
    reconciled: int = 0

@app.get('/api/bank-accounts')
def list_bank_accounts():
    return _rows(db.get_all_bank_accounts())

@app.post('/api/bank-accounts')
def upsert_bank_account(data: BankAccountIn):
    aid = db.save_bank_account(data.dict())
    return {'ok': True, 'id': aid}

@app.delete('/api/bank-accounts/{aid}')
def del_bank_account(aid: int):
    db.delete_bank_account(aid)
    return {'ok': True}

@app.get('/api/bank-accounts/{aid}/transactions')
def list_bank_txns(aid: int):
    return _rows(db.get_bank_transactions(aid))

@app.post('/api/bank-transactions')
def add_bank_txn(data: BankTxnIn):
    tid = db.add_bank_transaction(data.dict())
    return {'ok': True, 'id': tid}

# ════════════════════════════════════════════════════════════════════════════
# CHART OF ACCOUNTS
# ════════════════════════════════════════════════════════════════════════════
class AccountIn(BaseModel):
    id: Optional[int] = None
    code: str
    name: str
    account_type: str
    parent_id: Optional[int] = None
    description: str = ''

@app.get('/api/accounts')
def list_accounts():
    return _rows(db.get_all_accounts())

@app.post('/api/accounts')
def upsert_account(data: AccountIn):
    aid = db.save_account(data.dict())
    return {'ok': True, 'id': aid}

@app.delete('/api/accounts/{aid}')
def del_account(aid: int):
    db.delete_account(aid)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# JOURNAL ENTRIES
# ════════════════════════════════════════════════════════════════════════════
class JournalLine(BaseModel):
    account_id: int
    debit: float = 0
    credit: float = 0
    narration: str = ''

class JournalIn(BaseModel):
    entry_no: str
    entry_date: str
    narration: str = ''
    reference: str = ''
    lines: List[JournalLine] = []

@app.get('/api/journals')
def list_journals():
    return _rows(db.get_all_journals())

@app.get('/api/journals/next-number')
def next_journal_no():
    return {'entry_no': db.next_journal_no()}

@app.get('/api/journals/{jid}')
def get_journal(jid: int):
    j = db.get_journal(jid)
    if not j: raise HTTPException(404)
    return j

@app.post('/api/journals')
def create_journal(data: JournalIn):
    entry = data.dict(exclude={'lines'})
    lines = [l.dict() for l in data.lines]
    jid = db.save_journal(entry, lines)
    return {'id': jid, 'entry_no': data.entry_no}

@app.delete('/api/journals/{jid}')
def delete_journal(jid: int):
    db.delete_journal(jid)
    return {'ok': True}

@app.get('/api/trial-balance')
def trial_balance():
    return _rows(db.get_trial_balance())

# ════════════════════════════════════════════════════════════════════════════
# PROJECTS & TIMESHEETS
# ════════════════════════════════════════════════════════════════════════════
class ProjectIn(BaseModel):
    id: Optional[int] = None
    name: str
    customer_id: Optional[int] = None
    customer_name: str = ''
    status: str = 'Active'
    billing_type: str = 'Fixed'
    budget: float = 0
    start_date: str = ''
    end_date: str = ''
    description: str = ''

class TimesheetIn(BaseModel):
    id: Optional[int] = None
    project_id: Optional[int] = None
    project_name: str = ''
    entry_date: str
    task: str = ''
    hours: float = 0
    rate: float = 0
    is_billable: int = 1
    notes: str = ''

@app.get('/api/projects')
def list_projects():
    return _rows(db.get_all_projects())

@app.post('/api/projects')
def upsert_project(data: ProjectIn):
    pid = db.save_project(data.dict())
    return {'ok': True, 'id': pid}

@app.delete('/api/projects/{pid}')
def del_project(pid: int):
    db.delete_project(pid)
    return {'ok': True}

@app.get('/api/timesheets')
def list_timesheets(project_id: Optional[int] = None):
    return _rows(db.get_all_timesheets(project_id))

@app.post('/api/timesheets')
def upsert_timesheet(data: TimesheetIn):
    db.save_timesheet(data.dict())
    return {'ok': True}

@app.delete('/api/timesheets/{tid}')
def del_timesheet(tid: int):
    db.delete_timesheet(tid)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ════════════════════════════════════════════════════════════════════════════
from fastapi import UploadFile, File

DOCS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'documents')
os.makedirs(DOCS_DIR, exist_ok=True)

@app.get('/api/documents')
def list_documents():
    return _rows(db.get_all_documents())

@app.post('/api/documents/upload')
async def upload_document(file: UploadFile = File(...), description: str = '', related_type: str = '', related_id: int = 0):
    dest = os.path.join(DOCS_DIR, file.filename)
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(dest)
    did = db.save_document({'filename': file.filename, 'original_name': file.filename, 'file_path': dest,
                             'file_size': size, 'mime_type': file.content_type or '',
                             'related_type': related_type, 'related_id': related_id, 'description': description})
    return {'ok': True, 'id': did}

@app.delete('/api/documents/{did}')
def del_document(did: int):
    db.delete_document(did)
    return {'ok': True}

# ════════════════════════════════════════════════════════════════════════════
# REPORTS
# ════════════════════════════════════════════════════════════════════════════
@app.get('/api/reports/pl')
def report_pl(from_date: str = Query(...), to_date: str = Query(...)):
    return db.get_pl_report(from_date, to_date)

@app.get('/api/reports/gst')
def report_gst(from_date: str = Query(...), to_date: str = Query(...)):
    return db.get_gst_report(from_date, to_date)

@app.get('/api/reports/sales')
def report_sales(from_date: str = Query(...), to_date: str = Query(...)):
    return db.get_sales_report(from_date, to_date)

# ── Serve the built React app (SPA with catch-all) ───────────────────────────
_base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
_dist = None
for _try in [
    os.path.join(os.path.dirname(__file__), "web", "dist"),
    os.path.join(_base, "web", "dist"),
    os.path.join(_base, "_internal", "web", "dist"),
]:
    if os.path.exists(_try):
        _dist = _try
        break
if _dist:
    from fastapi.responses import HTMLResponse
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_catchall(full_path: str):
        # First check if it's a real static file (logo.png, favicon.svg, etc.)
        if full_path:
            static_file = os.path.join(_dist, full_path)
            if os.path.isfile(static_file):
                return FileResponse(static_file)
        # Otherwise serve the SPA index.html
        index = os.path.join(_dist, "index.html")
        if os.path.exists(index):
            with open(index, encoding="utf-8") as f:
                return HTMLResponse(f.read())
        return HTMLResponse("<h1>Frontend not built. Run: cd web && npm run build</h1>", status_code=503)


