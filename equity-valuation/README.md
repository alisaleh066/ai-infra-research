# Equity Valuation — value any US-listed stock from live data

Type a ticker, get a full intrinsic valuation: a **DCF** (with WACC build + sensitivity), a
**comps** cross-check, and a **Monte Carlo** fair-value distribution — built on **audited SEC
EDGAR** fundamentals + a **live price**, with an Excel model you can edit. No API key.

## Quick start (Windows — easiest)
1. Double-click **`setup.bat`** once (installs dependencies with your Anaconda Python).
2. Double-click **`run.bat`** (values MU), or from a terminal: `run.bat AAPL`.
3. Optional web app: double-click **`app.bat`** → opens in your browser.

Outputs land in `output/`: `<TICKER>_valuation.xlsx`, `<TICKER>_valuation.json`,
`<TICKER>_montecarlo.png`.

## If you prefer typing commands
These work regardless of PATH (they call Anaconda's Python directly). **PowerShell** doesn't
support `&&`, so run lines one at a time:
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" -m pip install -r requirements.txt
& "$env:USERPROFILE\anaconda3\python.exe" value.py NVDA
& "$env:USERPROFILE\anaconda3\python.exe" -m pytest -q
```
Or open **Anaconda Prompt** (where `python`/`pip`/`pytest` are already on PATH) and use them normally.

## How it works
- **`data.py`** — keyless fetchers:
  - *Fundamentals:* SEC EDGAR REST API (`company_tickers.json` → CIK → `companyfacts`). Audited
    10-K values. EDGAR requires a User-Agent header (set `SEC_EDGAR_USER_AGENT`, or use the
    built-in default). Handles XBRL tag drift (e.g. NVDA's revenue spans two different tags) by
    merging fallback tags, keyed by each value's period-end year.
  - *Price:* Yahoo Finance chart API (keyless JSON) for the latest price + ~2y history (used to
    estimate beta vs SPY). Cached under `cache/` so re-runs are fast/offline.
- **`value.py`** — derives transparent DCF assumptions from the company's **own history**
  (revenue-weighted average margin & D&A, capex faded toward maintenance, CAGR-based growth fading
  to terminal), runs the engine, writes the Excel + JSON + chart.
- **`valuation.py`** — the pure, unit-tested DCF/WACC/sensitivity/comps/Monte Carlo engine.
- **`build_xlsx.py`** — formula-linked Excel model (black text, dedicated Assumptions tab).
- **`xlsx_check.py`** — audits the workbook for formula errors.

## Automated research workup (`analyze.py`)
One command runs a full battery of recognized techniques on any ticker and writes a research note
+ Excel:
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" analyze.py NVDA
```
Outputs `output/<TICKER>_research.md` (reads like an analyst note) and `output/<TICKER>_analysis.xlsx`.
Techniques (all standard, citable): ratios + **DuPont** ROE decomposition · **ROIC vs WACC** (value
creation) · **Piotroski F-Score** · **Altman Z-Score** · **Beneish M-Score** · **Sloan accruals** ·
**reverse DCF** (growth implied by the price). Every score degrades gracefully — missing lines show
`n/a`, never fabricated. Score formulas live in `analysis.py` and are unit-tested.

## Analyst layer (the judgment, not just the machine)
- **`THESIS_MU.md`** — a one-page IC memo on Micron: recommendation, base/bull/bear price targets,
  variant perception, the 3 drivers, kill criteria, catalysts, and sizing.
- **`mu_thesis_model.py`** — a *hand-built* scenario DCF for MU (HBM-cycle driver paths, every
  assumption footnoted) — depth on one name vs the auto-derived baseline:
  `& "$env:USERPROFILE\anaconda3\python.exe" mu_thesis_model.py`
- **`comps_live.py`** — real, live peer-median multiples (EV/EBITDA, EV/Sales, P/E) from a memory/
  semis peer set: `& "$env:USERPROFILE\anaconda3\python.exe" comps_live.py MU`
- Every `value.py` run also prints a **Bear / Base / Bull** scenario band (not just Monte Carlo).

## Honesty / limitations
- **Nothing is fabricated.** Any line the filing doesn't tag is flagged (printed + in the JSON),
  never invented. Beta is clamped to a sane range; risk-free, ERP, tax and peer multiples are
  documented **assumptions** you edit in the Excel `Assumptions` tab.
- The auto-derived assumptions are a **conservative baseline**, not a target price — refine them.
  Deep cyclicals (e.g. MU) will look conservative because capex/margins are averaged across the
  cycle. US-listed only (EDGAR). Not investment advice.

## Verify
```powershell
& "$env:USERPROFILE\anaconda3\python.exe" -m pytest -q          # engine + data-parsing tests
& "$env:USERPROFILE\anaconda3\python.exe" xlsx_check.py output\MU_valuation.xlsx
```
