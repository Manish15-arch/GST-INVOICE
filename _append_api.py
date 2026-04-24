new_routes = r"""

# ════════════════════════════════════════════════════════════════════════════
# VENDORS
# ════════════════════════════════════════════════════════════════════════════
from pydantic import BaseModel
from typing import Optional, List as _List

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
    items: _List[BillItem] = []

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
    lines: _List[JournalLine] = []

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
import shutil
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
"""

with open(r'e:\IT WORK\PYTHON\tally-invoice-generator\api.py', 'a', encoding='utf-8') as f:
    f.write(new_routes)
print('Done — api.py extended.')
