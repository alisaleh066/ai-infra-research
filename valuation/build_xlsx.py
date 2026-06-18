"""build_xlsx — construct the Micron valuation workbook with linked formulas.

Conventions (xlsx skill): blue = inputs, black = formulas, dedicated Assumptions tab, units in
headers, parentheses for negatives, zero formula errors. Sheets: Assumptions, WACC, Model
(income statement + FCFF + balance sheet + cash flow), DCF, Sensitivity, Comps.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "valuation" / "output" / "MU_valuation.xlsx"

BLUE = Font(color="1D4ED8")                         # inputs
BLACK = Font(color="0F172A")                        # formulas / labels
BOLD = Font(color="0F172A", bold=True)
HEADWHITE = Font(color="FFFFFF", bold=True)
NAVY = PatternFill("solid", fgColor="0F172A")
SLATE = PatternFill("solid", fgColor="E2E8F0")
TITLE = Font(color="0F172A", bold=True, size=14)
MONEY = '#,##0;(#,##0)'
PCT = '0.0%'
PS = '"$"#,##0.00'
NUM2 = '0.00'
THIN = Side(style="thin", color="CBD5E1")
BORD = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HIST = ["B", "C", "D", "E"]                          # FY2022-FY2025
PROJ = ["F", "G", "H", "I", "J"]                     # Yr1-Yr5


def _inp(ws, coord, value, fmt=None):
    c = ws[coord]; c.value = value; c.font = BLUE
    if fmt:
        c.number_format = fmt
    return c


def _fml(ws, coord, formula, fmt=None):
    c = ws[coord]; c.value = formula; c.font = BLACK
    if fmt:
        c.number_format = fmt
    return c


def _lbl(ws, coord, text, bold=False):
    c = ws[coord]; c.value = text; c.font = BOLD if bold else BLACK
    return c


def _hdr(ws, coord, text):
    c = ws[coord]; c.value = text; c.font = HEADWHITE; c.fill = NAVY
    c.alignment = Alignment(horizontal="center")
    return c


def _title(ws, text):
    ws["A1"].value = text; ws["A1"].font = TITLE


def build(f, a, dcf, comps, waccs, growths, grid, summary) -> Path:
    inc, bs, cf = f["income_statement"], f["balance_sheet"], f["cash_flow"]
    wb = Workbook()

    # ----------------------------------------------------------------- Assumptions
    A = wb.active; A.title = "Assumptions"
    A.column_dimensions["A"].width = 34
    for col in "BCDEFGHIJ":
        A.column_dimensions[col].width = 12
    _title(A, "Micron (MU) — Valuation Assumptions")
    A["A2"].value = "Blue = input (editable). Figures sourced from SEC EDGAR unless flagged ASSUMPTION."
    A["A2"].font = Font(italic=True, color="64748B")

    rows = [
        ("A4", "Tax rate", "B4", a.tax_rate, PCT),
        ("A5", "Risk-free rate", "B5", a.risk_free, PCT),
        ("A6", "Equity risk premium", "B6", a.erp, PCT),
        ("A7", "Beta [ASSUMPTION]", "B7", a.beta, NUM2),
        ("A8", "Pre-tax cost of debt", "B8", a.pretax_kd, PCT),
        ("A9", "Share price (USD) [ASSUMPTION]", "B9", summary["market_price_ASSUMPTION"], PS),
        ("A10", "Shares outstanding (m)", "B10", a.shares, MONEY),
        ("A11", "Terminal growth", "B11", a.terminal_growth, PCT),
        ("A12", "D&A (% revenue)", "B12", a.da_pct_rev, PCT),
        ("A13", "Capex (% revenue) [ASSUMPTION]", "B13", a.capex_pct_rev, PCT),
        ("A14", "Incr. NWC (% of rev change) [ASSUMPTION]", "B14", a.nwc_pct_rev_change, PCT),
    ]
    for la, lt, ca, cv, fmt in rows:
        _lbl(A, la, lt); _inp(A, ca, cv, fmt)

    _lbl(A, "A15", "Revenue growth Yr1-Yr5 [ASSUMPTION]", bold=True)
    for i, g in enumerate(a.rev_growth):
        _inp(A, f"B{16+i}", g, PCT); _lbl(A, f"A{16+i}", f"  growth Yr{i+1}")
    _lbl(A, "A21", "EBIT margin Yr1-Yr5 [ASSUMPTION]", bold=True)
    for i, m in enumerate(a.ebit_margin):
        _inp(A, f"B{22+i}", m, PCT); _lbl(A, f"A{22+i}", f"  margin Yr{i+1}")

    _lbl(A, "A28", "LT debt FY2025 ($m) — EDGAR"); _inp(A, "B28", bs["long_term_debt"]["2025"], MONEY)
    _lbl(A, "A29", "Cash FY2025 ($m) — EDGAR"); _inp(A, "B29", bs["cash_and_equivalents"]["2025"], MONEY)
    _lbl(A, "A30", "Base revenue FY2025 ($m) — EDGAR"); _inp(A, "B30", inc["revenue"]["2025"], MONEY)

    # ----------------------------------------------------------------- WACC
    W = wb.create_sheet("WACC")
    W.column_dimensions["A"].width = 26; W.column_dimensions["B"].width = 14
    _title(W, "WACC build")
    pairs = [
        ("A4", "Risk-free rate", "B4", "=Assumptions!B5", PCT),
        ("A5", "Beta", "B5", "=Assumptions!B7", NUM2),
        ("A6", "Equity risk premium", "B6", "=Assumptions!B6", PCT),
        ("A7", "Cost of equity", "B7", "=B4+B5*B6", PCT),
        ("A8", "Pre-tax cost of debt", "B8", "=Assumptions!B8", PCT),
        ("A9", "Tax rate", "B9", "=Assumptions!B4", PCT),
        ("A10", "After-tax cost of debt", "B10", "=B8*(1-B9)", PCT),
        ("A11", "Equity value ($m)", "B11", "=Assumptions!B9*Assumptions!B10", MONEY),
        ("A12", "Debt value ($m)", "B12", "=Assumptions!B28", MONEY),
        ("A13", "Equity weight", "B13", "=B11/(B11+B12)", PCT),
        ("A14", "Debt weight", "B14", "=B12/(B11+B12)", PCT),
        ("A15", "WACC", "B15", "=B13*B7+B14*B10", PCT),
    ]
    for la, lt, ca, cf_, fmt in pairs:
        _lbl(W, la, lt); _fml(W, ca, cf_, fmt)
    W["A15"].font = BOLD; W["B15"].font = BOLD

    # ----------------------------------------------------------------- Model
    M = wb.create_sheet("Model")
    M.column_dimensions["A"].width = 30
    for col in "BCDEFGHIJ":
        M.column_dimensions[col].width = 12
    _title(M, "Micron (MU) — Income statement, FCFF, balance sheet & cash flow ($m)")
    heads = ["FY2022", "FY2023", "FY2024", "FY2025", "Yr1", "Yr2", "Yr3", "Yr4", "Yr5"]
    for col, h in zip("BCDEFGHIJ", heads):
        _hdr(M, f"{col}3", h)

    yrs = ["2022", "2023", "2024", "2025"]
    # Income statement
    _lbl(M, "A4", "Revenue ($m)", bold=True)
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}4", inc["revenue"][y], MONEY)
    growth_cells = ["B16", "B17", "B18", "B19", "B20"]
    prev = "E"
    for col, gc in zip(PROJ, growth_cells):
        _fml(M, f"{col}4", f"={prev}4*(1+Assumptions!{gc})", MONEY); prev = col
    _lbl(M, "A5", "Gross profit ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}5", inc["gross_profit"][y], MONEY)
    _lbl(M, "A6", "R&D ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}6", inc["rd_expense"][y], MONEY)
    _lbl(M, "A7", "SG&A ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}7", inc["sga_expense"][y], MONEY)
    _lbl(M, "A8", "EBIT ($m)", bold=True)
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}8", inc["operating_income"][y], MONEY)
    margin_cells = ["B22", "B23", "B24", "B25", "B26"]
    for col, mc in zip(PROJ, margin_cells):
        _fml(M, f"{col}8", f"={col}4*Assumptions!{mc}", MONEY)
    _lbl(M, "A9", "EBIT margin (%)")
    for col in HIST + PROJ:
        _fml(M, f"{col}9", f"={col}8/{col}4", PCT)
    _lbl(M, "A10", "Net income ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}10", inc["net_income"][y], MONEY)
    _lbl(M, "A11", "EPS diluted ($)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}11", inc["eps_diluted"][y], NUM2)

    # FCFF build (projection)
    _lbl(M, "A13", "Free cash flow to firm (projection)", bold=True)
    _lbl(M, "A14", "NOPAT ($m)")
    for col in PROJ:
        _fml(M, f"{col}14", f"={col}8*(1-Assumptions!B4)", MONEY)
    _lbl(M, "A15", "D&A ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}15", cf["depreciation_amort"][y], MONEY)
    for col in PROJ:
        _fml(M, f"{col}15", f"={col}4*Assumptions!B12", MONEY)
    _lbl(M, "A16", "Capex ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}16", cf["capex"][y], MONEY)
    for col in PROJ:
        _fml(M, f"{col}16", f"={col}4*Assumptions!B13", MONEY)
    _lbl(M, "A17", "Incr. NWC ($m)")
    prev = "E"
    for col in PROJ:
        _fml(M, f"{col}17", f"=({col}4-{prev}4)*Assumptions!B14", MONEY); prev = col
    _lbl(M, "A18", "FCFF ($m)", bold=True)
    for col in PROJ:
        _fml(M, f"{col}18", f"={col}14+{col}15-{col}16-{col}17", MONEY)

    # Balance sheet (historical actuals)
    _lbl(M, "A20", "Balance sheet (FY actuals)", bold=True)
    bs_rows = [("A21", "Total assets ($m)", "total_assets"),
               ("A22", "Cash & equivalents ($m)", "cash_and_equivalents"),
               ("A23", "Long-term debt ($m)", "long_term_debt"),
               ("A24", "Stockholders' equity ($m)", "stockholders_equity")]
    for la, lt, key in bs_rows:
        _lbl(M, la, lt)
        for col, y in zip(HIST, yrs):
            _inp(M, f"{col}{la[1:]}", bs[key][y], MONEY)

    # Cash flow (historical actuals)
    _lbl(M, "A26", "Cash flow (FY actuals)", bold=True)
    _lbl(M, "A27", "Cash from operations ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}27", cf["cfo"][y], MONEY)
    _lbl(M, "A28", "Capex ($m)")
    for col, y in zip(HIST, yrs):
        _inp(M, f"{col}28", cf["capex"][y], MONEY)
    _lbl(M, "A29", "Free cash flow (CFO - capex) ($m)")
    for col in HIST:
        _fml(M, f"{col}29", f"={col}27-{col}28", MONEY)

    # ----------------------------------------------------------------- DCF
    D = wb.create_sheet("DCF")
    D.column_dimensions["A"].width = 30
    for col in "BCDEF":
        D.column_dimensions[col].width = 13
    _title(D, "Discounted cash flow (FCFF)")
    _lbl(D, "A3", "Year")
    for col, yr in zip("BCDEF", [1, 2, 3, 4, 5]):
        _fml(D, f"{col}3", str(yr)); D[f"{col}3"].value = yr; D[f"{col}3"].font = BLACK
    _lbl(D, "A4", "FCFF ($m)")
    for col, mcol in zip("BCDEF", PROJ):
        _fml(D, f"{col}4", f"=Model!{mcol}18", MONEY)
    _lbl(D, "A5", "Discount factor")
    for col in "BCDEF":
        _fml(D, f"{col}5", f"=1/(1+WACC!$B$15)^{col}3", NUM2)
    _lbl(D, "A6", "PV of FCFF ($m)")
    for col in "BCDEF":
        _fml(D, f"{col}6", f"={col}4*{col}5", MONEY)
    _lbl(D, "A8", "Sum PV of FCFF ($m)"); _fml(D, "B8", "=SUM(B6:F6)", MONEY)
    _lbl(D, "A9", "Terminal value ($m)")
    _fml(D, "B9", "=F4*(1+Assumptions!B11)/(WACC!B15-Assumptions!B11)", MONEY)
    _lbl(D, "A10", "PV of terminal value ($m)"); _fml(D, "B10", "=B9*F5", MONEY)
    _lbl(D, "A11", "Enterprise value ($m)", bold=True); _fml(D, "B11", "=B8+B10", MONEY)
    _lbl(D, "A12", "Less: net debt ($m)"); _fml(D, "B12", "=Assumptions!B28-Assumptions!B29", MONEY)
    _lbl(D, "A13", "Equity value ($m)", bold=True); _fml(D, "B13", "=B11-B12", MONEY)
    _lbl(D, "A14", "Shares (m)"); _fml(D, "B14", "=Assumptions!B10", MONEY)
    _lbl(D, "A15", "Value per share ($)", bold=True); _fml(D, "B15", "=B13/B14", PS)
    D["B15"].fill = SLATE
    _lbl(D, "A16", "TV as % of EV"); _fml(D, "B16", "=B10/B11", PCT)

    # ----------------------------------------------------------------- Sensitivity
    S = wb.create_sheet("Sensitivity")
    S.column_dimensions["A"].width = 14
    for col in "BCDEFG":
        S.column_dimensions[col].width = 12
    _title(S, "Value per share — WACC (rows) x terminal growth (cols)")
    _lbl(S, "B3", "WACC \\ g", bold=True)
    for col, g in zip("CDEFG", growths):
        _inp(S, f"{col}3", g, PCT)
    deltas = [-0.015, -0.0075, 0.0, 0.0075, 0.015]
    for r, dval in zip(range(4, 9), deltas):
        sign = f"+{dval}" if dval >= 0 else f"{dval}"
        _fml(S, f"B{r}", f"=WACC!$B$15{sign if dval != 0 else ''}", PCT)
        if dval == 0:
            S[f"B{r}"].value = "=WACC!$B$15"
        for col in "CDEFG":
            formula = (f"=(SUMPRODUCT(DCF!$B$4:$F$4,1/(1+$B{r})^DCF!$B$3:$F$3)"
                       f"+(DCF!$F$4*(1+{col}$3)/($B{r}-{col}$3))/(1+$B{r})^5"
                       f"-(Assumptions!$B$28-Assumptions!$B$29))/Assumptions!$B$10")
            _fml(S, f"{col}{r}", formula, PS)
    S["E6"].fill = SLATE  # base case (WACC centre, terminal growth = 2.5%)

    # ----------------------------------------------------------------- Comps
    C = wb.create_sheet("Comps")
    C.column_dimensions["A"].width = 34; C.column_dimensions["B"].width = 14
    _title(C, "Comparable-company valuation")
    C["A2"].value = "Peer multiples are ASSUMPTION inputs (semis-sector typical) — replace with live peers."
    C["A2"].font = Font(italic=True, color="64748B")
    _lbl(C, "A4", "EBITDA FY2025 ($m)"); _fml(C, "B4", "=Model!E8+Model!E15", MONEY)
    _lbl(C, "A5", "EV/EBITDA multiple (x) [ASSUMPTION]"); _inp(C, "B5", 8.0, NUM2)
    _lbl(C, "A6", "Implied EV ($m)"); _fml(C, "B6", "=B4*B5", MONEY)
    _lbl(C, "A7", "Less: net debt ($m)"); _fml(C, "B7", "=Assumptions!B28-Assumptions!B29", MONEY)
    _lbl(C, "A8", "Equity value ($m)"); _fml(C, "B8", "=B6-B7", MONEY)
    _lbl(C, "A9", "Value/share — EV/EBITDA ($)"); _fml(C, "B9", "=B8/Assumptions!B10", PS)
    _lbl(C, "A11", "EPS FY2025 ($)"); _fml(C, "B11", "=Model!E11", NUM2)
    _lbl(C, "A12", "P/E multiple (x) [ASSUMPTION]"); _inp(C, "B12", 15.0, NUM2)
    _lbl(C, "A13", "Value/share — P/E ($)"); _fml(C, "B13", "=B11*B12", PS)
    _lbl(C, "A14", "Comps midpoint ($)", bold=True); _fml(C, "B14", "=AVERAGE(B9,B13)", PS)
    C["B14"].fill = SLATE

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    return OUT
