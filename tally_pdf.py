# -*- coding: utf-8 -*-
"""
tally_pdf.py — Tally ERP-style Tax Invoice PDF generator
Produces a white-background, orange-accent A4 invoice matching
the classic Tally ERP format (shown in the reference image):
  - 2-col header: company/consignee/buyer | invoice meta
  - Items table with CGST/SGST (or IGST) sub-rows + R/O + Total
  - Amount in words (English)
  - HSN/SAC summary table with merged CGST/SGST column headers
  - Tax amount in words
  - Declaration | Authorised Signatory
  - "This is a Computer Generated Invoice" footer
"""
import os, io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, Image as RLImage)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Unicode font for the Rs./₹ symbol ─────────────────────────────────────────
_UFONT = "Helvetica"
_RUPEE = "Rs."

def _try_reg(name, path):
    global _UFONT, _RUPEE
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            bold_path = path.replace(".ttf","B.ttf")
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(name+"-Bold", bold_path))
            else:
                pdfmetrics.registerFont(TTFont(name+"-Bold", path))
            _UFONT = name
            _RUPEE = "\u20b9"
            return True
        except Exception:
            pass
    return False

for _n, _p in [("NirmalaUI",  r"C:\Windows\Fonts\Nirmala.ttf"),
               ("SegoeUI",    r"C:\Windows\Fonts\segoeui.ttf"),
               ("ArialUni",   r"C:\Windows\Fonts\arialuni.ttf")]:
    if _try_reg(_n, _p):
        break


def generate_tally_pdf(inv: dict, out_path: str) -> str:
    """
    Generate a Tally ERP-style Tax Invoice PDF.
    `inv` must contain keys matching the database invoice dict,
    plus `inv['company']` = company profile dict.
    Returns `out_path`.
    """
    inv = dict(inv)
    # Auto-compute amount in words if not present
    if not inv.get('amount_in_words'):
        try:
            from invoice_engine import amount_in_words as _aiw
            inv['amount_in_words'] = _aiw(float(inv.get('grand_total', 0)))
        except Exception:
            inv['amount_in_words'] = f"{_RUPEE}{float(inv.get('grand_total',0)):,.2f}"

    company   = inv.get('company', {})
    items_raw = inv.get('items',   [])
    is_igst   = bool(inv.get('is_igst', 0))
    has_gstin = bool(str(inv.get('customer_gstin', '')).strip())

    # ── Page geometry ──────────────────────────────────────────
    ML = MR = 10 * mm
    FW = A4[0] - ML - MR       # 190 mm
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=ML, rightMargin=MR,
                            topMargin=8*mm, bottomMargin=8*mm)
    story = []

    # ── Colour palette (Tally white-bg, orange accents) ────────
    T_ORANGE = colors.HexColor("#C07000")
    T_BLACK  = colors.black
    T_WHITE  = colors.white
    T_LGRAY  = colors.HexColor("#F0F0F0")
    T_TAXROW = colors.HexColor("#FFFDE7")

    # ── Style factory ──────────────────────────────────────────
    def ts(nm, sz=9, bold=False, clr=T_BLACK, al=TA_LEFT, lead=None):
        fn = _UFONT + ("-Bold" if bold else "")
        try: pdfmetrics.getFont(fn)
        except Exception: fn = "Helvetica-Bold" if bold else "Helvetica"
        return ParagraphStyle(nm, fontName=fn, fontSize=sz, textColor=clr,
                              alignment=al, leading=lead or sz+3,
                              spaceAfter=0, spaceBefore=0)

    def pp(text, sty):
        return Paragraph(str(text) if text is not None else "", sty)

    SN  = ts("sn")
    SB  = ts("sb",  bold=True)
    SC  = ts("sc",  al=TA_CENTER)
    SR  = ts("sr",  al=TA_RIGHT)
    SBR = ts("sbr", bold=True, al=TA_RIGHT)
    SBC = ts("sbc", bold=True, al=TA_CENTER)
    SBS = ts("sbs", 10, True)           # large company name
    SOL = ts("sol",  8, False, T_BLACK)
    SOC = ts("soc",  8, True,  T_BLACK, TA_CENTER)
    SOR = ts("sor",  9, True,  T_BLACK, TA_RIGHT)

    # ══════════════════════════════════════════════════════════
    # TITLE
    # ══════════════════════════════════════════════════════════
    story.append(pp("Tax Invoice" if has_gstin else "Bill of Supply",
                    ts("ttl", 13, True, T_BLACK, TA_CENTER, 16)))

    # ══════════════════════════════════════════════════════════
    # SECTION 1 — HEADER
    # Left  (50%): company info | consignee | buyer
    # Right (50%): invoice meta in 4-sub-column grid
    # ══════════════════════════════════════════════════════════
    LHS = FW * 0.50
    RHS = FW - LHS

    co      = company
    co_gstin= co.get('gstin','')
    co_sc   = co.get('state_code','') or (co_gstin[:2] if len(co_gstin) >= 2 else '')
    cn      = inv.get('customer_name','')
    ca      = ", ".join(filter(None,[inv.get('customer_address',''),
                                     inv.get('customer_city',''),
                                     inv.get('customer_pincode','')]))
    cg      = inv.get('customer_gstin','')
    cst     = inv.get('customer_state','')
    csc     = inv.get('customer_state_code','')

    def _stln(state, code):
        parts = []
        if state: parts.append(f"State Name : {state}")
        if code:  parts.append(f"Code : {code}")
        return ",  ".join(parts)

    left_data = [
        [pp(co.get('company_name',''), SBS)],
        [pp(f"GSTIN/UIN: {co_gstin}", SN)],
        [pp(_stln(co.get('state',''), co_sc), SN)],
        [pp(", ".join(filter(None,[co.get('address',''), co.get('city',''),
                                    co.get('pincode','')])), ts("cad",8))],
    ]
    consignee_start = len(left_data)
    if cn:
        left_data += [[pp("Consignee (Ship to)", SB)], [pp(cn, SBS)]]
        if cg: left_data.append([pp(f"GSTIN/UIN: {cg}", SN)])
        if ca: left_data.append([pp(ca, ts("cadr",8))])
        left_data.append([pp(_stln(cst, csc), SN)])
        buyer_start = len(left_data)
        left_data += [[pp("Buyer (Bill to)", SB)], [pp(cn, SBS)]]
        if ca: left_data.append([pp(ca, ts("badr",8))])
        left_data.append([pp(_stln(cst, csc), SN)])
    else:
        buyer_start = None

    lt = Table(left_data, colWidths=[LHS - 2])
    lt_s = [('TOPPADDING',(0,0),(-1,-1),2), ('BOTTOMPADDING',(0,0),(-1,-1),2),
            ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4)]
    if cn:
        lt_s.append(('LINEABOVE',(0,consignee_start),(0,consignee_start),.5,T_BLACK))
        lt_s.append(('LINEABOVE',(0,buyer_start),(0,buyer_start),.5,T_BLACK))
    lt.setStyle(TableStyle(lt_s))

    # Right: 4-column invoice-meta grid
    RL1 = RHS/2*0.56; RV1 = RHS/2*0.44
    RL2 = RHS/2*0.56; RV2 = RHS/2*0.44
    right_rows = [
        [pp("Invoice No.", SOL), pp(inv.get('invoice_no',''), SB),
         pp("Dated",       SOL), pp(inv.get('invoice_date',''), SB)],
        [pp("Delivery Note",            SOL), pp("",SN),
         pp("Mode/Terms of Payment",    SOL), pp("",SN)],
        [pp("Reference No. & Date.",    SOL), pp("",SN),
         pp("Other References",          SOL), pp("",SN)],
        [pp("Buyer's Order No.",        SOL), pp("",SN),
         pp("Dated",                    SOL), pp("",SN)],
        [pp("Dispatch Doc No.",         SOL), pp("",SN),
         pp("Delivery Note Date",        SOL), pp("",SN)],
        [pp("Dispatched through",       SOL), pp("",SN),
         pp("Destination",              SOL), pp("",SN)],
        [pp("Terms of Delivery",        SOL), pp("",SN), pp("",SN), pp("",SN)],
    ]
    rt = Table(right_rows, colWidths=[RL1, RV1, RL2, RV2])
    rt.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),.5,T_BLACK),
        ('SPAN',(0,6),(-1,6)),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[T_WHITE, T_LGRAY]),
        ('TOPPADDING',(0,0),(-1,-1),2), ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
    ]))

    hdr = Table([[lt, rt]], colWidths=[LHS, RHS])
    hdr.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),.5,T_BLACK),
        ('GRID',(0,0),(-1,-1),.5,T_BLACK),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(0,0),(-1,-1),0), ('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(hdr)

    # ══════════════════════════════════════════════════════════
    # SECTION 2 — ITEMS TABLE
    # SI No | Description | HSN/SAC | Quantity | Rate | Per | Amount
    # Widths: 8+72+22+22+22+12+32 = 190 mm
    # ══════════════════════════════════════════════════════════
    ICW = [8*mm, 72*mm, 22*mm, 22*mm, 22*mm, 12*mm, 32*mm]

    item_data = [[pp("SI\nNo.",SOC), pp("Description of Goods",SOC),
                  pp("HSN/SAC",SOC), pp("Quantity",SOC),
                  pp("Rate",SOC), pp("per",SOC), pp("Amount",SOC)]]
    row_patches = []
    r = 1
    qty_totals = {}

    for it in items_raw:
        unit = it.get('unit',''); qty = float(it.get('qty',0))
        qty_totals[unit] = qty_totals.get(unit,0) + qty
        item_data.append([
            pp(str(it['sno']), SC),
            pp(it.get('product_name',''), SB),
            pp(it.get('hsn_sac',''), SC),
            pp(f"{qty:.2f} {unit}", SC),
            pp(f"{float(it.get('rate',0)):,.2f}", SR),
            pp(unit, SC),
            pp(f"{float(it.get('amount',0)):,.2f}", SR),
        ]); r += 1

        if is_igst:
            ir = float(it.get('igst_rate',0)); ia = float(it.get('igst_amount',0))
            item_data.append([pp("",SN), pp(f"IGST {ir:.0f}% SALE",SOR),
                               pp("",SN), pp("",SN), pp(f"{ir:.0f} %",SR), pp("",SN), pp(f"{ia:,.2f}",SR)])
            row_patches.append(('BACKGROUND',(0,r),(-1,r),T_TAXROW)); r+=1
        else:
            cr=float(it.get('cgst_rate',0)); ca=float(it.get('cgst_amount',0))
            sr_=float(it.get('sgst_rate',0)); sa=float(it.get('sgst_amount',0))
            item_data.append([pp("",SN), pp(f"CGST {cr:.0f}% SALE",SOR),
                               pp("",SN), pp("",SN), pp(f"{cr:.0f} %",SR), pp("",SN), pp(f"{ca:,.2f}",SR)])
            row_patches.append(('BACKGROUND',(0,r),(-1,r),T_TAXROW)); r+=1
            item_data.append([pp("",SN), pp(f"SGST {sr_:.0f}% SALE",SOR),
                               pp("",SN), pp("",SN), pp(f"{sr_:.0f} %",SR), pp("",SN), pp(f"{sa:,.2f}",SR)])
            row_patches.append(('BACKGROUND',(0,r),(-1,r),T_TAXROW)); r+=1

    roff = float(inv.get('round_off',0))
    if abs(roff) > 0.0001:
        item_data.append([pp("",SN), pp("R/O",SOR), pp("",SN), pp("",SN),
                           pp("",SN), pp("",SN), pp(f"{roff:+.2f}",SR)])
        row_patches.append(('BACKGROUND',(0,r),(-1,r),T_TAXROW)); r+=1

    # Blank spacer rows for Tally-style bottom padding
    for _ in range(max(0, 6 - len(items_raw))):
        item_data.append(["","","","","","",""]); r+=1

    qty_str  = "  ".join(f"{v:.0f} {u}" for u,v in qty_totals.items())
    grand    = float(inv.get('grand_total',0))
    total_r  = r
    item_data.append([pp("",SB), pp("Total",SB), pp("",SB),
                       pp(qty_str,SBC), pp("",SB), pp("",SB),
                       pp(f"{_RUPEE} {grand:,.2f}",ts("gt",10,True,T_BLACK,TA_RIGHT,13))])

    items_tbl = Table(item_data, colWidths=ICW, repeatRows=1)
    items_tbl.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),.5,T_BLACK),
        ('BACKGROUND',(0,0),(-1,0),T_LGRAY),
        ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),3), ('RIGHTPADDING',(0,0),(-1,-1),3),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEABOVE',(0,total_r),(-1,total_r),1.,T_BLACK),
        ('BACKGROUND',(0,total_r),(-1,total_r),T_LGRAY),
    ] + row_patches))
    story.append(items_tbl)

    # ══════════════════════════════════════════════════════════
    # SECTION 3 — AMOUNT IN WORDS
    # ══════════════════════════════════════════════════════════
    words = inv.get('amount_in_words','')
    aw = Table(
        [[pp("Amount Chargeable (in words)", SN),
          pp("E. & O.E", ts("eoe",8,al=TA_RIGHT))],
         [pp(words, ts("aw",9,True,T_BLACK,TA_LEFT,12)), pp("",SN)]],
        colWidths=[FW*0.65, FW*0.35])
    aw.setStyle(TableStyle([
        ('SPAN',(0,1),(-1,1)),
        ('BOX',(0,0),(-1,-1),.5,T_BLACK), ('LINEBELOW',(0,0),(-1,0),.5,T_BLACK),
        ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4),
    ]))
    story.append(aw)

    # ══════════════════════════════════════════════════════════
    # SECTION 4 — HSN/SAC SUMMARY
    # HSN|Taxable|CGST(Rate+Amt)|SGST(Rate+Amt)|TotalTax  = 190 mm
    # 28 + 32 + 17 + 28 + 17 + 28 + 40 = 190
    # ══════════════════════════════════════════════════════════
    HCW = [28*mm, 32*mm, 17*mm, 28*mm, 17*mm, 28*mm, 40*mm]

    hsn_agg = {}
    for it in items_raw:
        k = it.get('hsn_sac','')
        h = hsn_agg.setdefault(k, dict(tx=0.,cr=0.,ca=0.,sr=0.,sa=0.,ir=0.,ia=0.))
        h['tx'] += float(it.get('amount',0))
        h['cr']  = float(it.get('cgst_rate',0));  h['ca'] += float(it.get('cgst_amount',0))
        h['sr']  = float(it.get('sgst_rate',0));  h['sa'] += float(it.get('sgst_amount',0))
        h['ir']  = float(it.get('igst_rate',0));  h['ia'] += float(it.get('igst_amount',0))

    if is_igst:
        hdr1 = [pp("HSN/SAC",SOC), pp("Taxable\nValue",SOC),
                pp("IGST",SOC), pp("",SN), pp("",SN), pp("",SN), pp("Total\nTax Amount",SOC)]
        hdr2 = [pp("",SN), pp("",SN), pp("Rate",SOC), pp("Amount",SOC),
                pp("",SN), pp("",SN), pp("",SN)]
        gspans = [('SPAN',(2,0),(3,0)),('SPAN',(4,0),(5,0))]
    else:
        hdr1 = [pp("HSN/SAC",SOC), pp("Taxable\nValue",SOC),
                pp("CGST",SOC), pp("",SN), pp("SGST/UTGST",SOC), pp("",SN),
                pp("Total\nTax Amount",SOC)]
        hdr2 = [pp("",SN), pp("",SN), pp("Rate",SOC), pp("Amount",SOC),
                pp("Rate",SOC), pp("Amount",SOC), pp("",SN)]
        gspans = [('SPAN',(2,0),(3,0)),('SPAN',(4,0),(5,0))]


    hsn_rows = [hdr1, hdr2]
    tot_tx=tot_ca=tot_sa=tot_ia=0.

    for k,h in hsn_agg.items():
        tot_tx+=h['tx']; tot_ca+=h['ca']; tot_sa+=h['sa']; tot_ia+=h['ia']
        if is_igst:
            hsn_rows.append([pp(k,SC), pp(f"{h['tx']:,.2f}",SR),
                              pp(f"{h['ir']:.0f}%",SC), pp(f"{h['ia']:,.2f}",SR),
                              pp("",SN), pp("",SN), pp(f"{h['ia']:,.2f}",SR)])
        else:
            hsn_rows.append([pp(k,SC), pp(f"{h['tx']:,.2f}",SR),
                              pp(f"{h['cr']:.0f}%",SC), pp(f"{h['ca']:,.2f}",SR),
                              pp(f"{h['sr']:.0f}%",SC), pp(f"{h['sa']:,.2f}",SR),
                              pp(f"{h['ca']+h['sa']:,.2f}",SR)])

    if is_igst:
        hsn_rows.append([pp("Total",SBC), pp(f"{tot_tx:,.2f}",SBR),
                          pp("",SN), pp(f"{tot_ia:,.2f}",SBR),
                          pp("",SN), pp("",SN), pp(f"{tot_ia:,.2f}",SBR)])
    else:
        hsn_rows.append([pp("Total",SBC), pp(f"{tot_tx:,.2f}",SBR),
                          pp("",SN), pp(f"{tot_ca:,.2f}",SBR),
                          pp("",SN), pp(f"{tot_sa:,.2f}",SBR),
                          pp(f"{tot_ca+tot_sa:,.2f}",SBR)])
    lh = len(hsn_rows)-1
    hsn_tbl = Table(hsn_rows, colWidths=HCW)
    hsn_tbl.setStyle(TableStyle([
        ('GRID',(0,0),(-1,-1),.5,T_BLACK),
        ('BACKGROUND',(0,0),(-1,1),T_LGRAY),
        ('BACKGROUND',(0,lh),(-1,lh),T_LGRAY),
        ('TOPPADDING',(0,0),(-1,-1),2), ('BOTTOMPADDING',(0,0),(-1,-1),2),
        ('LEFTPADDING',(0,0),(-1,-1),3), ('RIGHTPADDING',(0,0),(-1,-1),3),
    ] + gspans))
    story.append(hsn_tbl)

    # ══════════════════════════════════════════════════════════
    # SECTION 5 — TAX AMOUNT IN WORDS
    # ══════════════════════════════════════════════════════════
    try:
        from invoice_engine import amount_in_words as _aiw
        tax_amt   = tot_ia if is_igst else (tot_ca + tot_sa)
        tax_words = _aiw(tax_amt)
    except Exception:
        tax_words = f"{_RUPEE}{(tot_ia if is_igst else tot_ca+tot_sa):,.2f}"
    tw = Table([[pp(f"Tax Amount (in words) :  {tax_words}", ts("taw",8))]],
               colWidths=[FW])
    tw.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),.5,T_BLACK),
        ('TOPPADDING',(0,0),(-1,-1),3), ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4),
    ]))
    story.append(tw)

    # ══════════════════════════════════════════════════════════
    # SECTION 6 — DECLARATION | AUTHORISED SIGNATORY
    # ══════════════════════════════════════════════════════════
    decl = ("<b>Declaration</b><br/>"
            "We declare that this invoice shows the actual price of the goods described "
            "and that all particulars are true and correct.")
    sig_path = co.get('signature_path','')
    if sig_path and os.path.exists(sig_path):
        try:    sig_elem = RLImage(sig_path, width=40*mm, height=14*mm, kind='proportional')
        except: sig_elem = pp("", SN)
    else:
        sig_elem = pp("", SN)
    co_nm = co.get('company_name','')
    sig_inner = Table([[pp(f"for {co_nm}", ts("fcn",8,True,T_BLACK,TA_CENTER))],
                       [sig_elem],
                       [pp("Authorised Signatory", ts("asn",8,al=TA_RIGHT))]],
                      colWidths=[FW*0.38])
    sig_inner.setStyle(TableStyle([
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),4),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
    ]))
    decl_tbl = Table([[pp(decl, ts("decl",7,al=TA_LEFT,lead=9)), sig_inner]],
                     colWidths=[FW*0.62, FW*0.38])
    decl_tbl.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),.5,T_BLACK),
        ('LINEBEFORE',(1,0),(1,-1),.5,T_BLACK),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),4), ('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),4), ('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(decl_tbl)

    story.append(Spacer(1, 3*mm))
    story.append(pp("This is a Computer Generated Invoice",
                    ts("ftr",8,False,T_ORANGE,TA_CENTER)))

    doc.build(story)
    with open(out_path, 'wb') as f:
        f.write(buf.getvalue())
    return out_path
