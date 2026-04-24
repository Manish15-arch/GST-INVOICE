"""
pdf_exporter.py — Professional A4 GST Invoice
Fixes: Rupee sign via TTF font, all column widths precisely fit 180 mm.
"""
import os, io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable, Image as RLImage)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Page geometry ──────────────────────────────────────────────────────────────
# A4 = 210 mm wide; margins 15 mm each side → usable = 180 mm
MARGIN   = 15 * mm
FULL_W   = A4[0] - 2 * MARGIN       # ≈ 510 pt  = 180 mm

# ── Register a Unicode font for the ₹ symbol ──────────────────────────────────
_UNICODE_FONT = "Helvetica"          # overwritten below if a TTF is found
_RUPEE        = "Rs."               # fallback

def _try_register(name: str, path: str) -> bool:
    global _UNICODE_FONT, _RUPEE
    if os.path.exists(path):
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            bold_path = path.replace(".ttf", "B.ttf")
            if os.path.exists(bold_path):
                pdfmetrics.registerFont(TTFont(name + "-Bold", bold_path))
            else:
                pdfmetrics.registerFont(TTFont(name + "-Bold", path))
            _UNICODE_FONT = name
            _RUPEE = "\u20b9"   # ₹
            return True
        except Exception as e:
            print(f"Font registration failed for {name}: {e}")
    return False

for _n, _p in [
    ("NirmalaUI",  r"C:\Windows\Fonts\Nirmala.ttf"),
    ("SegoeUI",    r"C:\Windows\Fonts\segoeui.ttf"),
    ("ArialUni",   r"C:\Windows\Fonts\arialuni.ttf"),
    ("DejaVuSans", r"C:\Windows\Fonts\DejaVuSans.ttf"),
]:
    if _try_register(_n, _p):
        break

def R(v) -> str:
    """Format rupee amount: Rs.1,000.00 or ₹1,000.00"""
    try:
        return f"{_RUPEE}{float(v):,.2f}"
    except Exception:
        return f"Rs.{v}"

# ── Colour palette (B&W Tally style) ───────────────────────────────────────────
C_DARK   = colors.HexColor("#000000")
C_MID    = colors.HexColor("#333333")
C_LIGHT  = colors.HexColor("#F0F0F0")
C_ACCENT = colors.HexColor("#000000")
C_TEXT   = colors.HexColor("#000000")
C_MUTED  = colors.HexColor("#666666")
C_WHITE  = colors.white
C_LGRAY  = colors.HexColor("#F5F5F5")
C_GRID   = colors.HexColor("#999999")
C_GREEN  = colors.HexColor("#000000")
C_TOTAL  = colors.HexColor("#E8E8E8")

# ── Style factory ──────────────────────────────────────────────────────────────
def _sty(name, size=9, bold=False, color=C_TEXT, align=TA_LEFT, leading=None):
    fn = _UNICODE_FONT + ("-Bold" if bold else "")
    # fall back gracefully if Bold variant not registered
    try:
        pdfmetrics.getFont(fn)
    except Exception:
        fn = "Helvetica-Bold" if bold else "Helvetica"
    return ParagraphStyle(name, fontName=fn, fontSize=size, textColor=color,
                          alignment=align, leading=leading or (size + 3),
                          spaceAfter=0, spaceBefore=0)

def P(text, style):
    return Paragraph(str(text), style)

# Pre-built common styles
S_HDR_CO  = _sty("hco", 15, True,  C_WHITE,  TA_LEFT,  19)
S_HDR_SUB = _sty("hsu",  9, False, colors.HexColor("#CCCCCC"), TA_LEFT, 12)
S_HDR_TTL = _sty("httl",19, True,  C_WHITE,  TA_RIGHT, 23)
S_HDR_LBL = _sty("hlbl", 8, False, colors.HexColor("#AAAAAA"), TA_RIGHT, 10)
S_HDR_VAL = _sty("hval", 9, True,  C_WHITE,  TA_RIGHT, 12)
S_GSTIN   = _sty("gst",  8, True,  colors.HexColor("#DDDDDD"), TA_LEFT,  10)
S_SEC     = _sty("sec",  8, True,  C_MUTED,  TA_LEFT,  10)
S_NAME    = _sty("nm",  11, True,  C_TEXT,   TA_LEFT,  14)
S_BODY    = _sty("bd",   9, False, C_TEXT,   TA_LEFT,  12)
S_BODY_R  = _sty("bdr",  9, False, C_TEXT,   TA_RIGHT, 12)
S_BODY_C  = _sty("bdc",  9, False, C_TEXT,   TA_CENTER,12)
S_BOLD    = _sty("bl",   9, True,  C_TEXT,   TA_LEFT,  12)
S_BOLD_R  = _sty("blr",  9, True,  C_TEXT,   TA_RIGHT, 12)
S_WORDS   = _sty("wd",   9, True,  C_GREEN,  TA_LEFT,  12)
S_FOOT    = _sty("ft",   8, False, C_MUTED,  TA_CENTER,10)
S_SUPPLY  = _sty("sup",  9, True,  C_TEXT, TA_LEFT, 12)
S_SUPPLY2 = _sty("su2",  9, True,  C_TEXT, TA_LEFT, 12)

def _tblstyle(cmds):
    return TableStyle(cmds)

# ── Helpers ────────────────────────────────────────────────────────────────────
_BASE_CELL = [
    ('TOPPADDING',    (0,0),(-1,-1), 5),
    ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ('LEFTPADDING',   (0,0),(-1,-1), 5),
    ('RIGHTPADDING',  (0,0),(-1,-1), 5),
    ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
]

def _items_hdr_style():
    return _BASE_CELL + [
        ('BACKGROUND',  (0,0),(-1,0), C_MID),
        ('TEXTCOLOR',   (0,0),(-1,0), C_WHITE),
        ('FONTNAME',    (0,0),(-1,0), _UNICODE_FONT + "-Bold" if _UNICODE_FONT != "Helvetica" else "Helvetica-Bold"),
        ('FONTSIZE',    (0,0),(-1,0), 8),
        ('ALIGN',       (0,0),(-1,0), 'CENTER'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE, C_LIGHT]),
        ('FONTSIZE',    (0,1),(-1,-1), 8),
        ('GRID',        (0,0),(-1,-1), 0.4, C_GRID),
        ('LINEBELOW',   (0,0),(-1,0),  1.0, C_DARK),
    ]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(inv: dict, out_path: str):
    # Auto-compute amount in words
    if not inv.get('amount_in_words'):
        try:
            from invoice_engine import amount_in_words as _aiw
            inv = dict(inv)
            inv['amount_in_words'] = _aiw(float(inv.get('grand_total', 0)))
        except Exception:
            inv['amount_in_words'] = R(inv.get('grand_total', 0))

    company   = inv.get('company', {})
    items     = inv.get('items', [])
    is_igst   = bool(inv.get('is_igst', 0))
    has_gstin = bool(str(inv.get('customer_gstin', '')).strip())

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=10*mm, bottomMargin=10*mm)
    story = []

    # ══════════════════════════════════════════════════════════════════════════
    # 1. HEADER  (115 mm | 65 mm = 180 mm)
    # ══════════════════════════════════════════════════════════════════════════
    LW, RW = 115*mm, 65*mm     # must equal FULL_W

    # Logo (optional)
    logo_path = company.get('logo_path','')
    logo_elem  = None
    if logo_path and os.path.exists(logo_path):
        try:
            logo_elem = RLImage(logo_path, width=40*mm, height=14*mm,
                                kind='proportional')
        except Exception:
            logo_elem = None

    co_rows = []
    if logo_elem:
        co_rows.append([logo_elem])
    co_rows += [
        [P(company.get('company_name','Your Company'), S_HDR_CO)],
        [P(company.get('address',''), S_HDR_SUB)],
        [P(f"{company.get('city','')}  {company.get('state','')}  "
           f"{company.get('pincode','')}", S_HDR_SUB)],
        [P(f"Ph: {company.get('phone','')}   {company.get('email','')}", S_HDR_SUB)],
    ]
    if company.get('gstin'):
        co_rows.append([P(f"GSTIN: {company['gstin']}", S_GSTIN)])

    inv_label = "TAX INVOICE" if has_gstin else "BILL OF SUPPLY"
    inv_rows  = [
        [P(inv_label, S_HDR_TTL)],
        [P("Invoice No", S_HDR_LBL)],
        [P(inv.get('invoice_no',''), S_HDR_VAL)],
        [P("Date", S_HDR_LBL)],
        [P(inv.get('invoice_date',''), S_HDR_VAL)],
    ]

    co_tbl = Table(co_rows, colWidths=[LW - 4*mm])
    co_tbl.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1), C_DARK),
        ('TOPPADDING',(0,0),(-1,-1), 7),('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 10),('RIGHTPADDING',(0,0),(-1,-1), 4),
    ]))

    inv_tbl = Table(inv_rows, colWidths=[RW - 4*mm])
    inv_tbl.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1), C_DARK),
        ('TOPPADDING',(0,0),(-1,-1), 7),('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('LEFTPADDING',(0,0),(-1,-1), 4),('RIGHTPADDING',(0,0),(-1,-1), 10),
    ]))

    hdr = Table([[co_tbl, inv_tbl]], colWidths=[LW, RW])
    hdr.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1), C_DARK),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(hdr)
    story.append(HRFlowable(width="100%", thickness=3, color=C_ACCENT, spaceAfter=4))

    # ══════════════════════════════════════════════════════════════════════════
    # 2. BILL TO | SUPPLY INFO  (115 mm | 65 mm)
    # ══════════════════════════════════════════════════════════════════════════
    c = inv   # customer fields live flat on inv dict
    bill_rows = [[P("BILL TO", S_SEC)],
                 [P(c.get('customer_name',''), S_NAME)]]
    cg = str(c.get('customer_gstin','')).strip()
    if cg:
        bill_rows.append([P(f"GSTIN: {cg}",
            _sty("cg2",8,True,C_TEXT,TA_LEFT,11))])
    else:
        bill_rows.append([P("Unregistered Consumer",
            _sty("ur2",8,False,C_MUTED,TA_LEFT,11))])
    addr = c.get('customer_address','')
    if addr: bill_rows.append([P(addr, S_BODY)])
    ci = "  ".join(filter(None,[c.get('customer_city',''),
                                c.get('customer_state',''),
                                c.get('customer_pincode','')]))
    if ci: bill_rows.append([P(ci, S_BODY)])
    if c.get('customer_phone'): bill_rows.append([P(f"Ph: {c['customer_phone']}", S_BODY)])
    if c.get('customer_email'): bill_rows.append([P(c['customer_email'], S_BODY)])

    tax_label = "Inter-State Supply (IGST)" if is_igst else "Intra-State Supply (CGST+SGST)"
    sup_rows  = [
        [P("SUPPLY INFO",S_SEC)],
        [P("Place of Supply:",S_BOLD)],
        [P(c.get('customer_state','') or "—", S_BODY)],
        [P("Tax Type:", S_BOLD)],
        [P(tax_label, S_SUPPLY if is_igst else S_SUPPLY2)],
    ]
    if not has_gstin:
        sup_rows.append([P("(Unregistered Buyer – B2C)", _sty("b2c",8,False,C_MUTED,TA_LEFT,11))])

    bill_tbl = Table(bill_rows, colWidths=[LW - 6*mm])
    bill_tbl.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1),C_LGRAY),
        ('BOX',(0,0),(-1,-1),0.5,C_GRID),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    sup_tbl = Table(sup_rows, colWidths=[RW - 6*mm])
    sup_tbl.setStyle(_tblstyle([
        ('BOX',(0,0),(-1,-1),0.5,C_GRID),
        ('BACKGROUND',(0,0),(0,0),C_LGRAY),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))

    addr_row = Table([[bill_tbl, sup_tbl]], colWidths=[LW, RW])
    addr_row.setStyle(_tblstyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(addr_row)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 3. ITEMS TABLE  — total width = FULL_W = 180 mm
    # CGST (10 cols): 7+49+11+11+17+17+10+19+19+20 = 180 mm
    # IGST  (9 cols): 7+57+12+12+19+20+12+21+20    = 180 mm
    # ══════════════════════════════════════════════════════════════════════════
    if is_igst:
        col_labels = ["#","Description & HSN/SAC","Unit","Qty",
                      f"Rate\n({_RUPEE})",f"Taxable\n({_RUPEE})",
                      "IGST%",f"IGST\n({_RUPEE})",f"Total\n({_RUPEE})"]
        col_mm     = [7, 57, 12, 12, 19, 20, 12, 21, 20]
    else:
        col_labels = ["#","Description & HSN/SAC","Unit","Qty",
                      f"Rate\n({_RUPEE})",f"Taxable\n({_RUPEE})",
                      "GST%",f"CGST\n({_RUPEE})",f"SGST\n({_RUPEE})",f"Total\n({_RUPEE})"]
        col_mm     = [7, 49, 11, 11, 17, 17, 10, 19, 19, 20]

    assert sum(col_mm) == 180, f"Items cols sum={sum(col_mm)}"
    col_pts = [c * mm for c in col_mm]

    rows = [col_labels]
    for it in items:
        amt   = float(it.get('amount', 0))
        total = float(it.get('total_amount', 0))
        hsn   = it.get('hsn_sac','')
        desc  = f"<b>{it.get('product_name','')}</b>"
        if hsn:
            desc += f"<br/><font size='7' color='#666666'>HSN/SAC: {hsn}</font>"
        if is_igst:
            rows.append([
                P(str(it['sno']), S_BODY_C),
                P(desc, S_BODY),
                P(it.get('unit','PCS'), S_BODY_C),
                P(f"{float(it['qty']):.2f}", S_BODY_C),
                P(R(it['rate']),  S_BODY_R),
                P(R(amt),        S_BODY_R),
                P(f"{float(it['gst_rate'])}%", S_BODY_C),
                P(R(it.get('igst_amount',0)), S_BODY_R),
                P(R(total), S_BODY_R),
            ])
        else:
            rows.append([
                P(str(it['sno']), S_BODY_C),
                P(desc, S_BODY),
                P(it.get('unit','PCS'), S_BODY_C),
                P(f"{float(it['qty']):.2f}", S_BODY_C),
                P(R(it['rate']),  S_BODY_R),
                P(R(amt),        S_BODY_R),
                P(f"{float(it['gst_rate'])}%", S_BODY_C),
                P(R(it.get('cgst_amount',0)), S_BODY_R),
                P(R(it.get('sgst_amount',0)), S_BODY_R),
                P(R(total), S_BODY_R),
            ])

    items_tbl = Table(rows, colWidths=col_pts, repeatRows=1)
    items_tbl.setStyle(TableStyle(_items_hdr_style()))
    story.append(items_tbl)
    story.append(Spacer(1, 3*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 4. HSN SUMMARY (left) + TOTALS (right)
    # HSN table = 108 mm,  Totals = 72 mm,  total = 180 mm
    # ══════════════════════════════════════════════════════════════════════════
    TAX_W = 72 * mm
    HSN_W = FULL_W - TAX_W         # 108 mm

    subtotal   = float(inv.get('subtotal',  0))
    cgst_total = float(inv.get('cgst_total',0))
    sgst_total = float(inv.get('sgst_total',0))
    igst_total = float(inv.get('igst_total',0))
    round_off  = float(inv.get('round_off', 0))
    grand      = float(inv.get('grand_total',0))

    # ── HSN/rate summary ──────────────────────────────────────────────────────
    # Build groups
    hsn_map: dict = {}
    for it in items:
        key = (it.get('hsn_sac',''), float(it.get('gst_rate',0)))
        if key not in hsn_map:
            hsn_map[key] = dict(hsn=it.get('hsn_sac',''), rate=key[1],
                                taxable=0.0, cgst=0.0, sgst=0.0, igst=0.0)
        hsn_map[key]['taxable'] += float(it.get('amount',0))
        hsn_map[key]['cgst']   += float(it.get('cgst_amount',0))
        hsn_map[key]['sgst']   += float(it.get('sgst_amount',0))
        hsn_map[key]['igst']   += float(it.get('igst_amount',0))

    # Column layout for HSN table (must sum to HSN_W = 108 mm)
    if is_igst:
        # 5 cols: HSN(22) Taxable(28) Rate(14) IGST(28) Total(16) = 108
        hsn_hdr = ["HSN/SAC", f"Taxable\n({_RUPEE})", "Rate",
                   f"IGST\n({_RUPEE})", f"Tax Total\n({_RUPEE})"]
        hsn_cw  = [22*mm, 28*mm, 14*mm, 28*mm, 16*mm]
    else:
        # 6 cols: HSN(20) Taxable(22) Rate(12) CGST(18) SGST(18) Total(18)=108
        hsn_hdr = ["HSN/SAC", f"Taxable\n({_RUPEE})", "Rate",
                   f"CGST\n({_RUPEE})", f"SGST\n({_RUPEE})", f"Tax Total\n({_RUPEE})"]
        hsn_cw  = [20*mm, 22*mm, 12*mm, 18*mm, 18*mm, 18*mm]

    hsn_rows = [hsn_hdr]
    for key, h in hsn_map.items():
        tax = h['igst'] if is_igst else (h['cgst'] + h['sgst'])
        if is_igst:
            hsn_rows.append([
                P(h['hsn'] or "—", S_BODY),
                P(R(h['taxable']), S_BODY_R),
                P(f"{h['rate']}%", S_BODY_C),
                P(R(h['igst']),    S_BODY_R),
                P(R(tax),          S_BODY_R),
            ])
        else:
            hsn_rows.append([
                P(h['hsn'] or "—", S_BODY),
                P(R(h['taxable']), S_BODY_R),
                P(f"{h['rate']}%", S_BODY_C),
                P(R(h['cgst']),    S_BODY_R),
                P(R(h['sgst']),    S_BODY_R),
                P(R(tax),          S_BODY_R),
            ])

    hsn_tbl = Table(hsn_rows, colWidths=hsn_cw)
    hsn_tbl.setStyle(TableStyle(_BASE_CELL + [
        ('BACKGROUND', (0,0),(-1,0), C_LIGHT),
        ('FONTNAME',   (0,0),(-1,0), _UNICODE_FONT+"-Bold" if _UNICODE_FONT!="Helvetica" else "Helvetica-Bold"),
        ('FONTSIZE',   (0,0),(-1,-1), 8),
        ('ALIGN',      (0,0),(-1,0),  'CENTER'),
        ('GRID',       (0,0),(-1,-1), 0.4, C_GRID),
        ('LINEBELOW',  (0,0),(-1,0),  0.8, C_DARK),
        ('ALIGN',      (2,1),( 2,-1), 'CENTER'),
        ('ALIGN',      (1,1),( 1,-1), 'RIGHT'),
        ('ALIGN',      (3,1),(-1,-1), 'RIGHT'),
    ]))

    # ── Totals panel (72 mm wide) ─────────────────────────────────────────────
    TL = 38*mm   # label col
    TV = 34*mm   # value col   → TL+TV = 72 mm

    def _tr(label, val, big=False, bg=None):
        fs = 10 if big else 9
        sl = _sty("trl"+label, fs, big, C_DARK if big else C_TEXT, TA_LEFT,  fs+3)
        sv = _sty("trv"+label, fs, big, C_DARK if big else C_TEXT, TA_RIGHT, fs+3)
        t  = Table([[P(label, sl), P(val, sv)]], colWidths=[TL, TV])
        cmds = [('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
                ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6)]
        if bg:
            cmds.append(('BACKGROUND',(0,0),(-1,-1),bg))
        if big:
            cmds += [('BOX',(0,0),(-1,-1),1.5,C_ACCENT),
                     ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]
        t.setStyle(TableStyle(cmds))
        return t

    tot_rows = [[_tr("Subtotal:", R(subtotal))]]
    if is_igst:
        tot_rows.append([_tr("IGST:", R(igst_total))])
    else:
        tot_rows.append([_tr("CGST:", R(cgst_total))])
        tot_rows.append([_tr("SGST / UTGST:", R(sgst_total))])
    if round_off:
        tot_rows.append([_tr("Round Off:", f"{_RUPEE}{round_off:+.2f}")])
    tot_rows.append([_tr("GRAND TOTAL:", R(grand), big=True, bg=C_TOTAL)])

    tot_outer = Table(tot_rows, colWidths=[TAX_W])
    tot_outer.setStyle(TableStyle([
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('BOX',(0,0),(-1,-2),0.5,C_GRID),
    ]))

    # Side by side
    summary = Table([[hsn_tbl, tot_outer]], colWidths=[HSN_W, TAX_W])
    summary.setStyle(_tblstyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(summary)
    story.append(Spacer(1, 3*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 5. AMOUNT IN WORDS  (full width)
    # ══════════════════════════════════════════════════════════════════════════
    aw  = inv.get('amount_in_words', R(grand))
    awt = Table([[P("Amount in Words:", _sty("awl",8,True,C_MUTED,TA_LEFT,11)),
                  P(aw, S_WORDS)]],
                colWidths=[36*mm, FULL_W - 36*mm])
    awt.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1),C_LGRAY),
        ('BOX',(0,0),(-1,-1),0.8,C_GRID),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
    ]))
    story.append(awt)
    story.append(Spacer(1, 4*mm))

    # ══════════════════════════════════════════════════════════════════════════
    # 6. BANK DETAILS | SIGNATURE  (105 mm | 75 mm = 180 mm)
    # ══════════════════════════════════════════════════════════════════════════
    BNK_W = 105 * mm
    SIG_W = FULL_W - BNK_W    # 75 mm

    bank_rows = [[P("Bank Details", S_SEC)]]
    for lbl, key in [("Bank Name:", "bank_name"), ("Account No:", "account_no"),
                     ("IFSC Code:", "ifsc_code")]:
        if company.get(key):
            bank_rows.append([P(f"<b>{lbl}</b>  {company[key]}", S_BODY)])
    if len(bank_rows) == 1:
        bank_rows.append([P("Bank details not configured.", _sty("bnc",8,False,C_MUTED,TA_LEFT,11))])

    sig_path  = company.get('signature_path','')
    sig_rows  = [
        [P(f"For  <b>{company.get('company_name','')}</b>",
           _sty("sig2",9,False,C_TEXT,TA_CENTER,12))],
    ]
    if sig_path and os.path.exists(sig_path):
        try:
            sig_img = RLImage(sig_path, width=50*mm, height=18*mm, kind='proportional')
            sig_rows.append([sig_img])
        except Exception:
            sig_rows += [[P(" ",_sty("sp1",6,False,C_WHITE,TA_CENTER,18))],
                         [P(" ",_sty("sp2",6,False,C_WHITE,TA_CENTER,18))]]
    else:
        sig_rows += [[P(" ",_sty("sp1",6,False,C_WHITE,TA_CENTER,18))],
                     [P(" ",_sty("sp2",6,False,C_WHITE,TA_CENTER,18))]]
    sig_rows += [
        [P("________________________",_sty("ul2",9,False,C_MUTED,TA_CENTER,12))],
        [P("Authorised Signatory", _sty("as3",8,False,C_MUTED,TA_CENTER,11))],
    ]

    bank_tbl = Table(bank_rows, colWidths=[BNK_W - 8*mm])
    bank_tbl.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1),C_LGRAY),
        ('BOX',(0,0),(-1,-1),0.5,C_GRID),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    sig_tbl = Table(sig_rows, colWidths=[SIG_W - 8*mm])
    sig_tbl.setStyle(_tblstyle([
        ('BOX',(0,0),(-1,-1),0.5,C_GRID),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))

    footer_row = Table([[bank_tbl, sig_tbl]], colWidths=[BNK_W, SIG_W])
    footer_row.setStyle(_tblstyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(footer_row)

    # Notes
    if inv.get('notes'):
        story.append(Spacer(1, 3*mm))
        story.append(P(f"<b>Notes:</b>  {inv['notes']}", S_BODY))

    # ══════════════════════════════════════════════════════════════════════════
    # 7. PAGE FOOTER  (60 | 60 | 60 mm = 180 mm)
    # ══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_DARK, spaceAfter=3))
    fw = FULL_W / 3
    foot = Table([[
        P("Generated by Tally Invoice Generator", S_FOOT),
        P("This is a Computer Generated Invoice", S_FOOT),
        P("Original for Recipient", S_FOOT),
    ]], colWidths=[fw, fw, fw])
    foot.setStyle(_tblstyle([
        ('ALIGN',(0,0),(0,-1),'LEFT'),
        ('ALIGN',(1,0),(1,-1),'CENTER'),
        ('ALIGN',(2,0),(2,-1),'RIGHT'),
        ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
    ]))
    story.append(foot)

    # ── Build ──────────────────────────────────────────────────────────────────
    doc.build(story)
    with open(out_path, 'wb') as f:
        f.write(buf.getvalue())
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# LEDGER PDF
# ══════════════════════════════════════════════════════════════════════════════
def generate_ledger_pdf(customer_name: str, entries: list, company: dict, out_path: str):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=10*mm, bottomMargin=10*mm)
    story = []

    # Header
    hdr_data = [[
        P(company.get('company_name',''), _sty("lhco",14,True,C_WHITE,TA_LEFT,18)),
        P("CUSTOMER LEDGER", _sty("lhttl",16,True,C_WHITE,TA_RIGHT,20)),
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[FULL_W*0.6, FULL_W*0.4])
    hdr_tbl.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1),C_DARK),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    story.append(hdr_tbl)
    story.append(HRFlowable(width="100%", thickness=3, color=C_ACCENT, spaceAfter=4))

    # Customer info
    story.append(P(f"<b>Customer:</b>  {customer_name}",
                   _sty("lci",10,False,C_TEXT,TA_LEFT,14)))
    story.append(Spacer(1, 4*mm))

    # Table
    col_hdrs = ["Date","Type","Reference","Credit (Invoice)","Debit (Payment)","Balance"]
    col_W    = [22*mm, 18*mm, 45*mm, 35*mm, 35*mm, 25*mm]   # 180 mm total
    rows = [col_hdrs]
    for e in entries:
        rows.append([
            e['date'], e['type'], e['ref'],
            R(e['credit']) if e['credit'] else "",
            R(e['debit'])  if e['debit']  else "",
            R(e['balance']),
        ])
    tbl = Table(rows, colWidths=col_W, repeatRows=1)
    last = len(rows) - 1
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),C_MID),
        ('TEXTCOLOR',(0,0),(-1,0),C_WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ('GRID',(0,0),(-1,-1),0.4,C_GRID),
        ('ALIGN',(2,0),(-1,-1),'RIGHT'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(tbl)

    # Summary
    if entries:
        bal = entries[-1]['balance']
        story.append(Spacer(1,4*mm))
        story.append(P(f"<b>Closing Balance:  {R(bal)}</b>",
                       _sty("lcb",10,True,C_TEXT,TA_RIGHT,13)))

    doc.build(story)
    with open(out_path,'wb') as f: f.write(buf.getvalue())
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# STATEMENT PDF
# ══════════════════════════════════════════════════════════════════════════════
def generate_statement_pdf(customer_name, rows, from_date, to_date, company, out_path):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=10*mm, bottomMargin=10*mm)
    story = []

    # Header
    hdr_data = [[
        P(company.get('company_name',''), _sty("shco",13,True,C_WHITE,TA_LEFT,17)),
        P("CUSTOMER STATEMENT", _sty("shttl",15,True,C_WHITE,TA_RIGHT,19)),
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[FULL_W*0.6, FULL_W*0.4])
    hdr_tbl.setStyle(_tblstyle([
        ('BACKGROUND',(0,0),(-1,-1),C_DARK),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    story.append(hdr_tbl)
    story.append(HRFlowable(width="100%", thickness=3, color=C_ACCENT, spaceAfter=4))

    info = Table([[
        P(f"<b>Customer:</b>  {customer_name}",_sty("si1",9,False,C_TEXT,TA_LEFT,12)),
        P(f"<b>Period:</b>  {from_date}  to  {to_date}",_sty("si2",9,False,C_TEXT,TA_RIGHT,12)),
    ]], colWidths=[FULL_W/2, FULL_W/2])
    info.setStyle(_tblstyle([
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(info)
    story.append(Spacer(1,3*mm))

    # Table  cols sum = 180 mm: 25+45+37+37+36 = 180
    col_hdrs = ["Date","Invoice No","Invoice Amount","Amount Paid","Balance"]
    col_W    = [25*mm, 45*mm, 37*mm, 37*mm, 36*mm]
    tbl_rows = [col_hdrs]
    tot_amt = tot_paid = tot_bal = 0.0
    for r in rows:
        tbl_rows.append([r['date'], r['invoice_no'],
                         R(r['amount']), R(r['paid']), R(r['balance'])])
        tot_amt  += r['amount']
        tot_paid += r['paid']
        tot_bal  += r['balance']
    # Totals row
    tbl_rows.append(["TOTAL","",R(tot_amt),R(tot_paid),R(tot_bal)])

    tbl = Table(tbl_rows, colWidths=col_W, repeatRows=1)
    last = len(tbl_rows) - 1
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),C_MID),
        ('TEXTCOLOR',(0,0),(-1,0),C_WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,last-1),[C_WHITE,C_LIGHT]),
        ('BACKGROUND',(0,last),(-1,last),C_DARK),
        ('TEXTCOLOR',(0,last),(-1,last),C_WHITE),
        ('FONTNAME',(0,last),(-1,last),'Helvetica-Bold'),
        ('GRID',(0,0),(-1,-1),0.4,C_GRID),
        ('ALIGN',(2,0),(-1,-1),'RIGHT'),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(tbl)
    story.append(Spacer(1,4*mm))

    # Outstanding highlight
    story.append(P(f"<b>Outstanding Balance:  {R(tot_bal)}</b>",
                   _sty("sob",10,True,C_TEXT,TA_RIGHT,13)))

    doc.build(story)
    with open(out_path,'wb') as f: f.write(buf.getvalue())
    return out_path