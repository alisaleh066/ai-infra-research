"""build_xlsx — UK real-estate acquisition model workbook (linked formulas, live IRR).

Conventions: blue = inputs, black = formulas, Assumptions tab, units in headers, parentheses for
negatives. The Underwriting tab is fully linked (incl. Excel IRR). The Sensitivity tab presents
the engine-computed IRR grid (IRR has no closed form; the interactive two-way grid lives in the
dashboard, recomputed live).
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "real_estate" / "output" / "UK_underwriting.xlsx"

BLUE = Font(color="1D4ED8")
BLACK = Font(color="0F172A")
BOLD = Font(color="0F172A", bold=True)
HEADWHITE = Font(color="FFFFFF", bold=True)
NAVY = PatternFill("solid", fgColor="0F172A")
SLATE = PatternFill("solid", fgColor="E2E8F0")
TITLE = Font(color="0F172A", bold=True, size=14)
GBP = '"£"#,##0;("£"#,##0)'
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


def build(deal, base, exit_caps, rent_growths, grid) -> Path:
    wb = Workbook()

    # Assumptions
    A = wb.active; A.title = "Assumptions"
    A.column_dimensions["A"].width = 30; A.column_dimensions["B"].width = 14
    A["A1"].value = "UK Real-Estate Acquisition — Assumptions"; A["A1"].font = TITLE
    A["A2"].value = "Blue = input. North West 6-unit block (illustrative)."
    A["A2"].font = Font(italic=True, color="64748B")
    _lbl(A, "A3", "Rent roll — monthly rent per unit (GBP)", bold=True)
    for i, r in enumerate(deal.units_monthly_rent):
        _lbl(A, f"A{4+i}", f"  Unit {i+1}"); _inp(A, f"B{4+i}", r, GBP)
    rows = [
        ("Vacancy rate", deal.vacancy_rate, PCT),
        ("Opex ratio (% of EGI)", deal.opex_ratio, PCT),
        ("Entry cap rate", deal.entry_cap_rate, PCT2),
        ("Exit cap rate", deal.exit_cap_rate, PCT2),
        ("Rent growth (pa)", deal.rent_growth, PCT2),
        ("LTV", deal.ltv, PCT),
        ("Interest rate (interest-only)", deal.interest_rate, PCT2),
        ("Purchase costs (% price)", deal.purchase_costs_pct, PCT),
        ("Selling costs (% sale)", deal.selling_costs_pct, PCT),
        ("Hold (years)", deal.hold_years, "0"),
    ]
    r0 = 4 + len(deal.units_monthly_rent) + 1
    self_rows = {}
    for j, (lbl, val, fmt) in enumerate(rows):
        rr = r0 + j
        _lbl(A, f"A{rr}", lbl); _inp(A, f"B{rr}", val, fmt)
        self_rows[lbl] = rr
    # cell refs for use in formulas
    R = self_rows
    a = lambda name: f"Assumptions!B{R[name]}"  # noqa: E731
    rent_first = 4
    rent_last = 4 + len(deal.units_monthly_rent) - 1

    # Underwriting
    U = wb.create_sheet("Underwriting")
    U.column_dimensions["A"].width = 30
    for col in "BCDEFG":
        U.column_dimensions[col].width = 13
    U["A1"].value = "Underwriting"; U["A1"].font = TITLE
    _lbl(U, "A3", "Gross rent (pa) (£)"); _fml(U, "B3", f"=SUM(Assumptions!B{rent_first}:B{rent_last})*12", GBP)
    _lbl(U, "A4", "Effective gross income (£)"); _fml(U, "B4", f"=B3*(1-{a('Vacancy rate')})", GBP)
    _lbl(U, "A5", "NOI (£)", bold=True); _fml(U, "B5", f"=B4*(1-{a('Opex ratio (% of EGI)')})", GBP)
    _lbl(U, "A6", "Valuation = NOI / entry cap (£)", bold=True)
    _fml(U, "B6", f"=B5/{a('Entry cap rate')}", GBP)
    _lbl(U, "A7", "Loan (£)"); _fml(U, "B7", f"=B6*{a('LTV')}", GBP)
    _lbl(U, "A8", "Equity invested (£)"); _fml(U, "B8", f"=B6*(1+{a('Purchase costs (% price)')})-B7", GBP)
    _lbl(U, "A9", "Debt service (pa) (£)"); _fml(U, "B9", f"=B7*{a('Interest rate (interest-only)')}", GBP)
    _lbl(U, "A10", "DSCR"); _fml(U, "B10", "=B5/B9", MULT)

    # Cash flows
    _lbl(U, "A12", "Levered equity cash flows (£)", bold=True)
    for i, col in enumerate("BCDEFG"):
        h = U[f"{col}13"]; h.value = f"Yr{i}"; h.font = HEADWHITE; h.fill = NAVY
        h.alignment = Alignment(horizontal="center")
    g = a("Rent growth (pa)"); ec = a("Exit cap rate"); sc = a("Selling costs (% sale)")
    _fml(U, "B14", "=-B8", GBP)  # yr0
    for i, col in enumerate("CDEF", start=1):  # yr1-4
        _fml(U, f"{col}14", f"=B5*(1+{g})^{i}-B9", GBP)
    # yr5: operating CF + net sale proceeds
    _fml(U, "G14",
         f"=B5*(1+{g})^5-B9+(B5*(1+{g})^6/{ec}*(1-{sc})-B7)", GBP)

    _lbl(U, "A16", "IRR (levered, 5-yr)", bold=True); _fml(U, "B16", "=IRR(B14:G14)", PCT2)
    U["B16"].fill = SLATE
    _lbl(U, "A17", "Equity multiple", bold=True); _fml(U, "B17", "=SUM(C14:G14)/-B14", MULT)
    U["B17"].fill = SLATE

    # Sensitivity (engine-computed values; IRR has no closed form)
    S = wb.create_sheet("Sensitivity")
    S.column_dimensions["A"].width = 16
    for col in "BCDEFG":
        S.column_dimensions[col].width = 11
    S["A1"].value = "IRR sensitivity — exit cap (rows) x rent growth (cols)"; S["A1"].font = TITLE
    S["A2"].value = "Values computed by re_engine.py (IRR is iterative). Interactive grid in dashboard."
    S["A2"].font = Font(italic=True, color="64748B")
    _lbl(S, "B3", "exit\\g", bold=True)
    for j, gr in enumerate(rent_growths):
        _inp(S, f"{chr(67+j)}3", gr, PCT)
    for i, ecv in enumerate(exit_caps):
        rr = 4 + i
        _inp(S, f"B{rr}", ecv, PCT2)
        for j, _ in enumerate(rent_growths):
            _fml(S, f"{chr(67+j)}{rr}", grid[i][j], PCT2)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    return OUT
