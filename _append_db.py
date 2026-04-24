new_methods = r"""
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
            cnt = c.execute('SELECT COUNT(*) FROM bills').fetchone()[0] + 1
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
            cnt = c.execute('SELECT COUNT(*) FROM purchase_orders').fetchone()[0] + 1
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
            cnt = c.execute('SELECT COUNT(*) FROM journal_entries').fetchone()[0] + 1
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
"""

with open(r'e:\IT WORK\PYTHON\tally-invoice-generator\database.py', 'a', encoding='utf-8') as f:
    f.write(new_methods)
print('Done — appended all CRUD methods.')
