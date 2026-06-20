# projectsf — three independent investment-analysis tools

<!-- After publishing, set <you> to your GitHub username so this badge goes live (see PUBLISH.md). -->
![tests](https://github.com/<you>/projectsf/actions/workflows/tests.yml/badge.svg)

Three self-contained projects, each runnable on its own (own README, dependencies, launchers,
tests). Built for Windows + Anaconda Python. No API keys required.

| # | Project | What it does |
|---|---------|--------------|
| 1 | [`equity-valuation/`](equity-valuation/) | Value **any US-listed stock** from live data — DCF + WACC + sensitivity + comps + Monte Carlo, on **audited SEC EDGAR** fundamentals + a live price. Outputs an editable Excel model. |
| 2 | [`ai-bottleneck-map/`](ai-bottleneck-map/) | Score the **AI-infrastructure supply chain** on a transparent *tightness* metric, find the **binding constraint**, and show where capital migrates. |
| 3 | [`real-estate-roi/`](real-estate-roi/) | **Institutional real-estate ROI**: value-add underwriting + an **LP/GP equity waterfall** (preferred return + promote tiers) — IRR, equity multiple, cash-on-cash, DSCR, debt yield. |

## Easiest start: `START.bat`
**Double-click `START.bat` in this folder** — one menu launches any of the three projects (run or
web app), so you never need to remember which folder or file. (Run each project's `setup.bat` once
first to install its dependencies.)

## Running a project directly (Windows)
Each project also has the same launchers — **double-click**, no setup hassle:
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

## The view, not just the tools
Each project ends in a **written recommendation** — a variant perception, kill criteria, and
catalysts, not just a number:
- [`INVESTMENT_THESIS.md`](INVESTMENT_THESIS.md) — the through-line tying all three to a live process.
- [`equity-valuation/THESIS_MU.md`](equity-valuation/THESIS_MU.md) — IC memo on Micron (base/bull/bear).
- [`ai-bottleneck-map/THESIS.md`](ai-bottleneck-map/THESIS.md) — where the constraint binds and capital migrates.
- [`real-estate-roi/THESIS.md`](real-estate-roi/THESIS.md) — when the LP/GP waterfall makes you take or pass a deal.

See each project's README for methodology, commands, and limitations.
