"""
invoice_engine.py — Invoice data model & tax calculation
"""
import re
from ui.styles import GSTIN_STATES


# ── GSTIN helpers ──────────────────────────────────────────
def validate_gstin(g: str) -> bool:
    return bool(re.match(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$', g.upper().strip()))


def state_from_gstin(g: str):
    """Return (state_code, state_name) from GSTIN string."""
    code = g[:2] if g and len(g) >= 2 else ""
    return code, GSTIN_STATES.get(code, "")


# ── Amount in words (Indian system) ────────────────────────
def _indian_words(n: int) -> str:
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
            "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
            "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    if n == 0:
        return "Zero"
    if n < 0:
        return "Minus " + _indian_words(-n)

    parts = []
    if n >= 10000000:
        parts.append(_indian_words(n // 10000000) + " Crore")
        n %= 10000000
    if n >= 100000:
        parts.append(_indian_words(n // 100000) + " Lakh")
        n %= 100000
    if n >= 1000:
        parts.append(_indian_words(n // 1000) + " Thousand")
        n %= 1000
    if n >= 100:
        parts.append(ones[n // 100] + " Hundred")
        n %= 100
    if n >= 20:
        word = tens[n // 10]
        if n % 10:
            word += " " + ones[n % 10]
        parts.append(word)
    elif n > 0:
        parts.append(ones[n])
    return " ".join(parts)


def amount_in_words(amount: float) -> str:
    rupees = int(amount)
    paise = round((amount - rupees) * 100)
    result = "Rupees " + _indian_words(rupees)
    if paise:
        result += f" And {_indian_words(paise)} Paise"
    return result + " Only"


# ── Tax calculation ─────────────────────────────────────────
def calc_item_tax(amount: float, gst_rate: float, is_igst: bool) -> dict:
    if is_igst:
        igst = round(amount * gst_rate / 100, 2)
        return dict(cgst_rate=0, cgst_amount=0, sgst_rate=0, sgst_amount=0,
                    igst_rate=gst_rate, igst_amount=igst,
                    total_tax=igst, total_amount=round(amount + igst, 2))
    half = gst_rate / 2
    cgst = round(amount * half / 100, 2)
    sgst = round(amount * half / 100, 2)
    return dict(cgst_rate=half, cgst_amount=cgst, sgst_rate=half, sgst_amount=sgst,
                igst_rate=0, igst_amount=0,
                total_tax=cgst + sgst, total_amount=round(amount + cgst + sgst, 2))


def compute_totals(items: list, is_igst: bool) -> dict:
    """
    items: list of dicts with keys: qty, rate, gst_rate
    Returns full tax summary dict.
    """
    subtotal = 0.0
    cgst_total = sgst_total = igst_total = 0.0
    by_rate: dict = {}

    for it in items:
        amt = round(float(it.get('qty', 0)) * float(it.get('rate', 0)), 2)
        rate = float(it.get('gst_rate', 18))
        tax = calc_item_tax(amt, rate, is_igst)
        subtotal += amt
        cgst_total += tax['cgst_amount']
        sgst_total += tax['sgst_amount']
        igst_total += tax['igst_amount']
        key = str(rate)
        if key not in by_rate:
            by_rate[key] = {'rate': rate, 'taxable': 0, 'cgst': 0, 'sgst': 0, 'igst': 0}
        by_rate[key]['taxable'] += amt
        by_rate[key]['cgst'] += tax['cgst_amount']
        by_rate[key]['sgst'] += tax['sgst_amount']
        by_rate[key]['igst'] += tax['igst_amount']

    subtotal = round(subtotal, 2)
    cgst_total = round(cgst_total, 2)
    sgst_total = round(sgst_total, 2)
    igst_total = round(igst_total, 2)
    total_tax = round(cgst_total + sgst_total + igst_total, 2)
    raw_grand = subtotal + total_tax
    grand_total = round(raw_grand)
    round_off = round(grand_total - raw_grand, 2)

    return {
        'subtotal': subtotal,
        'cgst_total': cgst_total,
        'sgst_total': sgst_total,
        'igst_total': igst_total,
        'total_tax': total_tax,
        'round_off': round_off,
        'grand_total': grand_total,
        'by_rate': by_rate,
        'amount_in_words': amount_in_words(grand_total),
        'is_igst': is_igst,
    }
