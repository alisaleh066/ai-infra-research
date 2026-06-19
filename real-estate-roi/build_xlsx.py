"""build_xlsx — institutional RE deal workbook: Assumptions, Underwriting, Waterfall, Sensitivity.

Underwriting is fully formula-linked (NOI ramp, debt, levered cash flows, live IRR). The waterfall
split is iterative (computed in waterfall.py), so the per-year LP/GP distributions are written as
values with a conservation-check formula and live IRR() formulas on the LP and project rows.
Conventions: black text throughout, formula-linked, units in headers, parentheses for negatives.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

OUTDIR = Path(__file__).resolve().parent / "output"

BLUE = Font(color="0F172A")   # inputs rendered black (was blue) per preference
BLACK = Font(color="0F172A")
BOLD = Font(color="0F172A", bold=True)
HEADWHITE = Font(color="FFFFFF", bold=True)
NAVY = PatternFill("solid", fgColor="0F172A")
SLATE = PatternFill("solid", fgColor="E2E8F0")
TITLE = Font(color="0F172A", bold=True, size=14)
ITAL = Font(italic=True, color="64748B")
MONEY = '#,##0;(#,##0)'
PCT = '0.0%'
PCT2 = '0.00%'
NUM2 = '0.00'
MULT = '0.00"x"'


def _inp(ws, c, v, fmt=None):
    ws[c].value = v; ws[c].font = BLUE
    if fmt: ws[c].number_format = fmt


def _fml(ws, c, v, fmt=None):
    ws[c].value = v; ws[c].font = BLACK
    if fmt: ws[c].number_format = fmt


def _lbl(ws, c, t, bold=False):
    ws[c].value = t; ws[c].font = BOLD if bold else BLACK


def _hdr(ws, c, t):
    ws[c].value = t; ws[c].font = HEADWHITE; ws[c].fill = NAVY
    ws[c].alignment = Alignment(horizontal="center")


def build(d, tiers, u, w, sens, ccy="") -> Path:
    N = d.hold_years
    wb = Workbook()

    # --------------------------------------------------------- Assumptions
    A = wb.active; A.title = "Assumptions"
    A.column_dimensions["A"].width = 32; A.column_dimensions["B"].width = 14
    A["A1"].value = f"Value-add deal — Assumptions ({ccy or 'currency-agnostic'})"; A["A1"].font = TITLE
    A["A2"].value = "Edit these inputs and the Underwriting tab recalculates."; A["A2"].font = ITAL
    rows = [
        ("Purchase price", d.purchase_price, MONEY),
        ("In-place NOI", d.in_place_noi, MONEY),
        ("Going-in cap rate", d.going_in_cap, PCT2),
        ("Exit cap rate", d.exit_cap, PCT2),
        ("Hold (years)", d.hold_years, "0"),
        ("NOI uplift (value-add)", d.noi_uplift_pct, PCT),
        ("Stabilize (years)", d.stabilize_years, "0"),
        ("Post-stabilize NOI growth", d.post_stabilize_growth, PCT2),
        ("Renovation capex", d.renovation_capex, MONEY),
        ("Acquisition costs (%)", d.acquisition_costs_pct, PCT),
        ("Selling costs (%)", d.selling_costs_pct, PCT),
        ("LTV", d.ltv, PCT),
        ("Interest rate (IO)", d.interest_rate, PCT2),
    ]
    rk = {}
    for i, (lbl, val, fmt) in enumerate(rows):
        rr = 4 + i
        _lbl(A, f"A{rr}", lbl); _inp(A, f"B{rr}", val, fmt); rk[lbl] = f"Assumptions!B{rr}"

    # --------------------------------------------------------- Underwriting (linked)
    U = wb.create_sheet("Underwriting")
    U.column_dimensions["A"].width = 28
    for i in range(N + 2):
        U.column_dimensions[get_column_letter(2 + i)].width = 13
    U["A1"].value = "Underwriting (levered)"; U["A1"].font = TITLE
    _lbl(U, "A3", "Stabilized NOI"); _fml(U, "B3", f"={rk['In-place NOI']}*(1+{rk['NOI uplift (value-add)']})", MONEY)
    _lbl(U, "A4", "Total cost"); _fml(U, "B4", f"={rk['Purchase price']}*(1+{rk['Acquisition costs (%)']})+{rk['Renovation capex']}", MONEY)
    _lbl(U, "A5", "Loan"); _fml(U, "B5", f"={rk['LTV']}*{rk['Purchase price']}", MONEY)
    _lbl(U, "A6", "Equity invested"); _fml(U, "B6", "=B4-B5", MONEY)
    _lbl(U, "A7", "Debt service (IO)"); _fml(U, "B7", f"=B5*{rk['Interest rate (IO)']}", MONEY)
    _lbl(U, "A8", "Debt yield"); _fml(U, "B8", f"={rk['In-place NOI']}/B5", PCT)
    _lbl(U, "A9", "LTC"); _fml(U, "B9", "=B5/B4", PCT)

    # year grid
    hrow = 11
    _lbl(U, f"A{hrow}", "Year", bold=True)
    for t in range(N + 1):
        _hdr(U, f"{get_column_letter(2+t)}{hrow}", str(t))
    stab = "$B$3"
    inplace = rk["In-place NOI"]; sy = rk["Stabilize (years)"]; g = rk["Post-stabilize NOI growth"]
    # NOI row
    noi_row = hrow + 1
    _lbl(U, f"A{noi_row}", "NOI")
    for t in range(1, N + 1):
        col = get_column_letter(2 + t)
        f = (f"=IF({t}<={sy},{inplace}+({stab}-{inplace})*{t}/{sy},"
             f"{stab}*(1+{g})^({t}-{sy}))")
        _fml(U, f"{col}{noi_row}", f, MONEY)
    # DSCR row
    dscr_row = noi_row + 1
    _lbl(U, f"A{dscr_row}", "DSCR")
    for t in range(1, N + 1):
        col = get_column_letter(2 + t)
        _fml(U, f"{col}{dscr_row}", f"={col}{noi_row}/$B$7", MULT)
    # Equity cash flow row
    cf_row = dscr_row + 1
    _lbl(U, f"A{cf_row}", "Equity cash flow", bold=True)
    _fml(U, f"B{cf_row}", "=-B6", MONEY)
    for t in range(1, N + 1):
        col = get_column_letter(2 + t)
        base = f"={col}{noi_row}-$B$7"
        if t == N:
            # exit: forward NOI / exit cap, net of selling costs and loan
            fwd = (f"({stab}*(1+{g})^({t}+1-{sy}))")
            exit_term = f"+({fwd}/{rk['Exit cap rate']}*(1-{rk['Selling costs (%)']})-B5)"
            _fml(U, f"{col}{cf_row}", base + exit_term, MONEY)
        else:
            _fml(U, f"{col}{cf_row}", base, MONEY)
    # metrics
    mrow = cf_row + 2
    last_col = get_column_letter(2 + N)
    _lbl(U, f"A{mrow}", "Project IRR", bold=True)
    _fml(U, f"B{mrow}", f"=IRR(B{cf_row}:{last_col}{cf_row})", PCT2); U[f"B{mrow}"].fill = SLATE
    _lbl(U, f"A{mrow+1}", "Equity multiple", bold=True)
    _fml(U, f"B{mrow+1}", f"=SUM(C{cf_row}:{last_col}{cf_row})/B6", MULT); U[f"B{mrow+1}"].fill = SLATE

    # --------------------------------------------------------- Waterfall
    Wf = wb.create_sheet("Waterfall")
    Wf.column_dimensions["A"].width = 28
    for i in range(N + 2):
        Wf.column_dimensions[get_column_letter(2 + i)].width = 13
    Wf["A1"].value = "LP / GP equity waterfall"; Wf["A1"].font = TITLE
    Wf["A2"].value = ("Tiers: " + " · ".join(f"{int(h*100)}%→GP {int(p*100)}%" for h, p in tiers.hurdles)
                      + ".  Below first hurdle: LP 100% (capital + preferred).")
    Wf["A2"].font = ITAL
    _lbl(Wf, "A4", "Year", bold=True)
    for t in range(N + 1):
        _hdr(Wf, f"{get_column_letter(2+t)}4", str(t))
    _lbl(Wf, "A5", "Equity cash flow")
    for t in range(N + 1):
        col = get_column_letter(2 + t)
        _fml(Wf, f"{col}5", f"=Underwriting!{col}{cf_row}", MONEY)
    _lbl(Wf, "A6", "LP distribution")
    _lbl(Wf, "A7", "GP promote")
    for t in range(N + 1):
        col = get_column_letter(2 + t)
        _inp(Wf, f"{col}6", round(w["lp_cash_flows"][t], 2), MONEY)
        _inp(Wf, f"{col}7", round(w["gp_cash_flows"][t], 2), MONEY)
    _lbl(Wf, "A8", "Check (LP+GP−CF)")
    for t in range(N + 1):
        col = get_column_letter(2 + t)
        _fml(Wf, f"{col}8", f"={col}6+{col}7-{col}5", MONEY)
    lc = get_column_letter(2 + N)
    _lbl(Wf, "A10", "Project IRR", bold=True); _fml(Wf, "B10", f"=IRR(B5:{lc}5)", PCT2)
    _lbl(Wf, "A11", "LP IRR", bold=True); _fml(Wf, "B11", f"=IRR(B6:{lc}6)", PCT2); Wf["B11"].fill = SLATE
    _lbl(Wf, "A12", "LP equity multiple"); _fml(Wf, "B12", f"=SUM(C6:{lc}6)/-B6", MULT)
    _lbl(Wf, "A13", "GP promote (total)", bold=True); _fml(Wf, "B13", f"=SUM(C7:{lc}7)", MONEY); Wf["B13"].fill = SLATE
    _lbl(Wf, "A14", "GP share of profit"); _fml(Wf, "B14", f"=B13/SUM(C5:{lc}5)", PCT)

    # --------------------------------------------------------- Sensitivity
    S = wb.create_sheet("Sensitivity")
    S.column_dimensions["A"].width = 12
    for c in "BCDEFG":
        S.column_dimensions[c].width = 11
    S["A1"].value = "LP IRR — exit cap (rows) × NOI uplift (cols)"; S["A1"].font = TITLE
    S["A2"].value = "Computed by waterfall.py (LP IRR is iterative)."; S["A2"].font = ITAL
    _lbl(S, "B3", "exit\\uplift", bold=True)
    for j, up in enumerate(sens["uplifts"]):
        _inp(S, f"{chr(67+j)}3", up, PCT)
    for i, ec in enumerate(sens["exit_caps"]):
        rr = 4 + i
        _inp(S, f"B{rr}", ec, PCT2)
        for j in range(len(sens["uplifts"])):
            _inp(S, f"{chr(67+j)}{rr}", round(sens["lp_irr_grid"][i][j], 4), PCT2)

    OUTDIR.mkdir(exist_ok=True)
    out = OUTDIR / "deal_underwriting.xlsx"
    wb.save(out)
    return out
