# projectsf — three independent investment-analysis tools

Three self-contained projects, each runnable on its own (own README, dependencies, launchers,
tests). Built for Windows + Anaconda Python. No API keys required.

| # | Project | What it does |
|---|---------|--------------|
| 1 | [`equity-valuation/`](equity-valuation/) | Value **any US-listed stock** from live data — DCF + WACC + sensitivity + comps + Monte Carlo, on **audited SEC EDGAR** fundamentals + a live price. Outputs an editable Excel model. |
| 2 | [`ai-bottleneck-map/`](ai-bottleneck-map/) | Score the **AI-infrastructure supply chain** on a transparent *tightness* metric, find the **binding constraint**, and show where capital migrates. |
| 3 | [`real-estate-roi/`](real-estate-roi/) | **Institutional real-estate ROI**: value-add underwriting + an **LP/GP equity waterfall** (preferred return + promote tiers) — IRR, equity multiple, cash-on-cash, DSCR, debt yield. |

## Running anything (Windows)
Each project has the same launchers — **double-click**, no setup hassle:
- **`setup.bat`** — installs that project's dependencies (uses your Anaconda Python directly).
- **`run.bat`** — runs it (Project 1: `run.bat AAPL`).
- **`app.bat`** — optional Streamlit web app.

> Why launchers? PowerShell 5.1 doesn't support `&&`, and `python`/`pip`/`pytest` aren't on your
> PATH by default — the `.bat` files call Anaconda's Python by full path and `cd` into the right
> folder, so they work even double-clicked from anywhere. If you prefer typing commands, each
> project's README lists PATH-independent PowerShell commands and the Anaconda-Prompt equivalents.

## Principles
- **Real data, no fabrication.** Fundamentals come from SEC EDGAR; anything a filing doesn't
  provide is flagged, never invented. Modelling assumptions are explicit and editable.
- **Tested.** Every non-trivial calculation has unit tests; the Excel models reconcile to the
  Python engines under a real recalculation.
- Research / portfolio artifacts — **not investment advice.**

See each project's README for methodology, commands, and limitations.
