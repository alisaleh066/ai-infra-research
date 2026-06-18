# Project 1 — Equity Valuation Engine: Micron Technology (MU)

A linked three-statement view + **DCF (FCFF)** with a **WACC build** and **two-way sensitivity**,
a **comparable-company** cross-check, and a **Monte Carlo** on the key value drivers. Built on
**audited SEC EDGAR** financials (FY2022–FY2025).

## Why Micron
Micron is the most investable near-pure play on **High-Bandwidth Memory (HBM)** — a binding
constraint in AI training hardware. The question this model answers is not "is AI big?" but
"how much of Micron's HBM-driven earnings power is already in the price?"

## Thesis
HBM scarcity is re-rating Micron's mid-cycle earnings: FY2025 revenue of **$37.4bn** (up from a
cyclical trough of $15.5bn in FY2023) with operating income back to **$9.8bn**. A disciplined
DCF that fades the upcycle to a mid-cycle growth/margin, against a market-derived WACC, gives an
intrinsic value we can compare to the market and to a comps cross-check. The base case here is
**deliberately conservative on capex** (Micron is highly capital-intensive — FY2025 capex was
~42% of revenue during the build-out), which is the single biggest swing factor in the valuation.

## Method
- **FCFF** = EBIT·(1−tax) + D&A − capex − ΔNWC, projected over a 5-year explicit horizon, then a
  Gordon-growth terminal value; discounted at WACC.
- **WACC** = market-weighted CAPM cost of equity + after-tax cost of debt (see the `WACC` tab).
- **Sensitivity**: value/share over WACC (±1.5%) × terminal growth (1.5%–3.5%).
- **Comps**: EV/EBITDA and P/E applied to FY2025 EBITDA / EPS (peer multiples are flagged
  assumptions — replace with live peers).
- **Monte Carlo**: 10,000 draws perturbing revenue growth, EBIT margin, WACC and terminal growth
  → a fair-value distribution (`output/monte_carlo.png`).

## Files
| File | What |
|------|------|
| `valuation_engine.py` | Pure, unit-tested calc core (DCF, WACC, sensitivity, comps, Monte Carlo) |
| `build_xlsx.py` | Builds `output/MU_valuation.xlsx` (linked formulas, blue inputs) |
| `build.py` | Entry point: runs engine + Monte Carlo, exports JSON/PNG, builds the xlsx |
| `output/MU_valuation.xlsx` | The Excel model (Assumptions, WACC, Model, DCF, Sensitivity, Comps) |
| `output/valuation.json` | Machine-readable results for the dashboard |
| `output/monte_carlo.png` | Fair-value distribution |

## Run
```bash
python valuation/build.py
pytest -q tests/test_valuation.py
python skills/model-auditor/auditor.py valuation/output/MU_valuation.xlsx
```

## Verification done
- 13 unit tests pass (WACC, FCFF, terminal value, DCF bridge, monotonicity, sensitivity shape,
  comps math, Monte Carlo reproducibility).
- `model-auditor`: **zero formula errors**, 122 linked formulas.
- **LibreOffice headless recalculation** of the workbook reproduces the engine outputs to the
  cent (DCF $88.45, WACC 9.86%, comps midpoint $120.52, sensitivity base $88.45) — i.e. the Excel
  formulas and the Python engine agree.

## Data & honesty
Income statement, balance sheet and cash flow are **audited 10-K values from SEC EDGAR**. Share
price, beta and the cost-of-capital inputs are **flagged ASSUMPTION** inputs (the FMP profile
returned an anomalous $1,144 price for MU and was rejected — see `DATA_SOURCES.md`). Peer
multiples in comps are sector-typical assumptions. All assumptions are blue in Excel and editable.

## Limitations
- The projection models EBIT directly (not a fully decomposed COGS/opex build) — standard for a
  driver-based DCF; full historical 3-statements are shown for context.
- The balance-sheet/cash-flow projection is summarised into the FCFF build rather than a full
  integrated debt schedule.
- Cyclical memory pricing makes any single point estimate fragile — hence the sensitivity table
  and Monte Carlo distribution are the intended outputs, not the single base number.
- Market price/beta are placeholders; plug in live figures to refresh upside/downside.

> Research/portfolio artifact — **not investment advice.**
