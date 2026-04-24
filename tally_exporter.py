"""
tally_exporter.py — Generate Tally ERP 9 / TallyPrime compatible XML
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime


def _tdate(d: str) -> str:
    """YYYY-MM-DD → YYYYMMDD"""
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y%m%d")
    except Exception:
        return d.replace("-", "")


def _sub(parent, tag, text=""):
    e = ET.SubElement(parent, tag)
    if text:
        e.text = str(text)
    return e


def generate_tally_xml(inv: dict) -> str:
    """
    inv — the full invoice dict produced by database.get_invoice()
    Returns pretty-printed XML string.
    """
    company     = inv.get('company', {})
    cname       = company.get('company_name', 'My Company')
    customer    = inv.get('customer', inv)          # flat dict from DB
    party_name  = customer.get('customer_name') or customer.get('name', '')
    inv_no      = inv['invoice_no']
    tdate       = _tdate(inv['invoice_date'])
    grand       = float(inv.get('grand_total', 0))
    subtotal    = float(inv.get('subtotal', 0))
    is_igst     = bool(inv.get('is_igst', 0))
    items       = inv.get('items', [])

    ENV  = ET.Element('ENVELOPE')
    HDR  = _sub(ENV,  'HEADER')
    _sub(HDR, 'TALLYREQUEST', 'Import Data')

    BODY = _sub(ENV, 'BODY')
    IMPD = _sub(BODY, 'IMPORTDATA')
    RDSC = _sub(IMPD, 'REQUESTDESC')
    _sub(RDSC, 'REPORTNAME', 'Vouchers')
    SV   = _sub(RDSC, 'STATICVARIABLES')
    _sub(SV, 'SVCURRENTCOMPANY', cname)

    RDAT = _sub(IMPD, 'REQUESTDATA')
    TMSG = _sub(RDAT, 'TALLYMESSAGE')
    TMSG.set('xmlns:UDF', 'TallyUDF')

    VCH = _sub(TMSG, 'VOUCHER')
    VCH.set('REMOTEID',  inv_no)
    VCH.set('VCHTYPE',   'Sales')
    VCH.set('ACTION',    'Create')
    VCH.set('OBJVIEW',   'Invoice Voucher View')

    _sub(VCH, 'DATE',              tdate)
    _sub(VCH, 'EFFECTIVEDATE',     tdate)
    _sub(VCH, 'VOUCHERTYPENAME',   'Sales')
    _sub(VCH, 'VOUCHERNUMBER',     inv_no)
    _sub(VCH, 'PARTYLEDGERNAME',   party_name)
    _sub(VCH, 'PERSISTEDVIEW',     'Invoice Voucher View')
    _sub(VCH, 'ISINVOICE',         'Yes')
    _sub(VCH, 'GSTIN',             customer.get('customer_gstin', customer.get('gstin', '')))

    # ── Party (debit) ──
    L1 = _sub(VCH, 'ALLLEDGERENTRIES.LIST')
    _sub(L1, 'LEDGERNAME',      party_name)
    _sub(L1, 'ISDEEMEDPOSITIVE','Yes')
    _sub(L1, 'ISPARTYLEDGER',   'Yes')
    _sub(L1, 'AMOUNT',          f"-{grand:.2f}")

    # ── Sales (credit) ──
    L2 = _sub(VCH, 'ALLLEDGERENTRIES.LIST')
    _sub(L2, 'LEDGERNAME',      'Sales')
    _sub(L2, 'ISDEEMEDPOSITIVE','No')
    _sub(L2, 'ISPARTYLEDGER',   'No')
    _sub(L2, 'AMOUNT',          f"{subtotal:.2f}")

    # ── Tax ledgers ──
    tax_map: dict = {}
    for it in items:
        r = float(it.get('gst_rate', 0))
        key = str(r)
        if key not in tax_map:
            tax_map[key] = {'r': r, 'cgst': 0.0, 'sgst': 0.0, 'igst': 0.0}
        tax_map[key]['cgst'] += float(it.get('cgst_amount', 0))
        tax_map[key]['sgst'] += float(it.get('sgst_amount', 0))
        tax_map[key]['igst'] += float(it.get('igst_amount', 0))

    for key, t in tax_map.items():
        r = t['r']
        if is_igst and t['igst'] > 0:
            L = _sub(VCH, 'ALLLEDGERENTRIES.LIST')
            _sub(L, 'LEDGERNAME',      f"IGST @ {r}%")
            _sub(L, 'ISDEEMEDPOSITIVE','No')
            _sub(L, 'AMOUNT',          f"{t['igst']:.2f}")
        else:
            if t['cgst'] > 0:
                L = _sub(VCH, 'ALLLEDGERENTRIES.LIST')
                _sub(L, 'LEDGERNAME',      f"CGST @ {r/2}%")
                _sub(L, 'ISDEEMEDPOSITIVE','No')
                _sub(L, 'AMOUNT',          f"{t['cgst']:.2f}")
            if t['sgst'] > 0:
                L = _sub(VCH, 'ALLLEDGERENTRIES.LIST')
                _sub(L, 'LEDGERNAME',      f"SGST/UTGST @ {r/2}%")
                _sub(L, 'ISDEEMEDPOSITIVE','No')
                _sub(L, 'AMOUNT',          f"{t['sgst']:.2f}")

    # Round-off
    ro = float(inv.get('round_off', 0))
    if ro != 0:
        L = _sub(VCH, 'ALLLEDGERENTRIES.LIST')
        _sub(L, 'LEDGERNAME',      'Round Off')
        _sub(L, 'ISDEEMEDPOSITIVE','No' if ro > 0 else 'Yes')
        _sub(L, 'AMOUNT',          f"{abs(ro):.2f}")

    # ── Inventory entries ──
    for it in items:
        IE = _sub(VCH, 'INVENTORYENTRIES.LIST')
        _sub(IE, 'STOCKITEMNAME', it['product_name'])
        unit = it.get('unit', 'PCS')
        _sub(IE, 'BILLEDQTY',     f"{it['qty']} {unit}")
        _sub(IE, 'ACTUALQTY',     f"{it['qty']} {unit}")
        _sub(IE, 'RATE',          f"{float(it['rate']):.2f}/{unit}")
        _sub(IE, 'AMOUNT',        f"{float(it['amount']):.2f}")
        # Accounting allocation
        AA = _sub(IE, 'ACCOUNTINGALLOCATIONLIST.LIST')
        _sub(AA, 'LEDGERNAME', 'Sales')
        _sub(AA, 'ISDEEMEDPOSITIVE', 'No')
        _sub(AA, 'AMOUNT', f"{float(it['amount']):.2f}")
        # GST details
        if it.get('hsn_sac'):
            GD = _sub(IE, 'GSTDETAILS.LIST')
            _sub(GD, 'TAXTYPE',  'GST')
            _sub(GD, 'HSNCODE',  it['hsn_sac'])
            r = float(it.get('gst_rate', 0))
            if is_igst:
                _sub(GD, 'IGSTRATE',  str(r))
            else:
                _sub(GD, 'CGSTRATE',  str(r / 2))
                _sub(GD, 'SGSTRATE',  str(r / 2))

    # Pretty print
    raw = ET.tostring(ENV, encoding='unicode')
    dom = minidom.parseString(raw)
    pretty = dom.toprettyxml(indent='  ')
    # Remove the extra <?xml?> that toprettyxml adds (keep our explicit one)
    lines = pretty.split('\n')
    if lines[0].startswith('<?xml'):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return '\n'.join(lines)
