import sys; sys.path.insert(0, '.')
from database import Database
from pdf_exporter import generate_pdf
import os

db = Database(); db.initialize()
company = db.get_company()

# Test 1: CGST+SGST — intra-state, no customer GSTIN (Bill of Supply)
items1 = [dict(sno=1, product_name='Web Design Services', hsn_sac='998314', unit='HR',
    qty=10, rate=1500, amount=15000, gst_rate=18,
    cgst_rate=9, cgst_amount=1350, sgst_rate=9, sgst_amount=1350,
    igst_rate=0, igst_amount=0, total_amount=17700)]
inv1 = dict(
    invoice_no='TEST-CGST-001', invoice_date='2026-04-15',
    customer_gstin='', customer_name='Suresh Kumar',
    customer_address='45 Park Street', customer_city='Mumbai',
    customer_state='Maharashtra', customer_pincode='400001',
    customer_phone='9876543210', customer_email='',
    subtotal=15000, cgst_total=1350, sgst_total=1350, igst_total=0,
    grand_total=17700, round_off=0, is_igst=0,
    notes='Payment due in 30 days.',
    items=items1, company=company)
generate_pdf(inv1, 'test_cgst_no_gstin.pdf')
print('Test 1 CGST+SGST (no GSTIN): OK')

# Test 2: IGST — inter-state, with customer GSTIN
items2 = [
    dict(sno=1, product_name='Software Development', hsn_sac='998314', unit='HR',
        qty=8, rate=2500, amount=20000, gst_rate=18,
        cgst_rate=0, cgst_amount=0, sgst_rate=0, sgst_amount=0,
        igst_rate=18, igst_amount=3600, total_amount=23600),
    dict(sno=2, product_name='Server Hosting', hsn_sac='998313', unit='MONTH',
        qty=1, rate=5000, amount=5000, gst_rate=18,
        cgst_rate=0, cgst_amount=0, sgst_rate=0, sgst_amount=0,
        igst_rate=18, igst_amount=900, total_amount=5900),
]
inv2 = dict(
    invoice_no='TEST-IGST-001', invoice_date='2026-04-15',
    customer_gstin='29ABCDE1234F1ZL', customer_name='XYZ Technologies Pvt Ltd',
    customer_address='45 MG Road', customer_city='Bangalore',
    customer_state='Karnataka', customer_pincode='560001',
    customer_phone='9988776655', customer_email='xyz@example.com',
    subtotal=25000, cgst_total=0, sgst_total=0, igst_total=4500,
    grand_total=29500, round_off=0, is_igst=1,
    notes='',
    items=items2, company=company)
generate_pdf(inv2, 'test_igst_with_gstin.pdf')
print('Test 2 IGST (with GSTIN): OK')

s1 = os.path.getsize('test_cgst_no_gstin.pdf')
s2 = os.path.getsize('test_igst_with_gstin.pdf')
print(f'PDF sizes: CGST={s1} bytes, IGST={s2} bytes')
print()
print('ALL PDF TESTS PASSED!')
