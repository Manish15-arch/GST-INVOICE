# -*- coding: utf-8 -*-
"""test_tally_pdf.py — quick smoke test for Tally-format PDF"""
import sys, os
sys.path.insert(0, '.')

from database import Database
from tally_pdf import generate_tally_pdf

db = Database(); db.initialize()
company = db.get_company()

items = [
    dict(sno=1, product_name="CEMENT 18%", hsn_sac="25232930",
         unit="BAG", qty=58, rate=277.62, amount=16101.69,
         gst_rate=18, cgst_rate=9, cgst_amount=1449.15,
         sgst_rate=9,  sgst_amount=1449.15,
         igst_rate=0,  igst_amount=0, total_amount=18999.99),
]

inv = dict(
    invoice_no="776", invoice_date="13-Mar-26",
    customer_name="GOVT.MID.SCHOOL MADANPURA",
    customer_gstin="23AAABG1234C1Z5",
    customer_address="", customer_city="Bhopal",
    customer_state="Madhya Pradesh", customer_state_code="23",
    customer_pincode="", customer_phone="", customer_email="",
    subtotal=16101.69, cgst_total=1449.15, sgst_total=1449.15,
    igst_total=0, grand_total=19000.00, round_off=0.01,
    is_igst=0, notes="",
    items=items,
    company=company or dict(
        company_name="BRAJESH BUILDING MATERIAL AND HARDWARE",
        gstin="23CIOPS5337L1ZN",
        address="Main Road", city="Bhopal",
        state="Madhya Pradesh", state_code="23",
        phone="9876543210", email="", bank_name="SBI",
        account_no="123456789", ifsc_code="SBIN0001234",
        logo_path="", signature_path=""),
)

out = "test_tally_invoice.pdf"
generate_tally_pdf(inv, out)
print(f"OK — {out} ({os.path.getsize(out):,} bytes)")
