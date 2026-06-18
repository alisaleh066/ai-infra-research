# projects.md — the three sub-projects, explained

This monorepo holds **three independent but thematically linked** investment-research
projects, plus one dashboard that presents them together. The unifying thesis:

> **The returns from the AI build-out accrue less to the model companies and more to the
> physical bottlenecks that gate compute — memory, advanced packaging, power, and the raw
> materials beneath them — and, in parallel, to the real assets (housing, land) whose value
> is set by transparent demand/supply fundamentals.** This platform values one node in that
> chain, maps where the chain is tight, and underwrites a real asset on first-principles drivers.

Build order is **strictly sequential**: Project 1 → 2 → 3. Each must self-score **≥ 8/10**
against its Definition of Done and pass the engineering gates (see `CLAUDE.md`) before the next.

---

## Project 1 — Equity Valuation Engine  (`/valuation`)
**Company:** Micron Technology (**MU**) — the most investable pure-ish play on HBM memory, a
binding constraint in AI training hardware.

**One-line thesis:** *HBM scarcity re-rates Micron's earnings power; a disciplined DCF and comps
cross-check tells us how much of that is already in the price.*

**What it contains**
- A **linked three-statement model** (income statement → balance sheet → cash flow) in Excel.
- A **DCF** with an explicit **WACC build-up** and a two-way **sensitivity table**
  (WACC × terminal growth) plus a football-field summary.
- A **comparable-company analysis** (EV/EBITDA, EV/Sales, P/E vs semis peers).
- A **Python Monte Carlo** layer that perturbs the key value drivers (revenue growth, gross
  margin, WACC, terminal growth) and exports a fair-value **distribution** chart + summary JSON.
- A **thesis-vs-portfolio** panel reconciling the valuation against live holdings *(falls back
  to a flagged sample positions file — no Trading212 MCP connected at build time)*.

**Methodology / data:** fundamentals from SEC EDGAR + market-data MCPs, cached locally. Any
value that cannot be fetched is a clearly-labelled assumption (blue in Excel, surfaced in UI).

**Definition of Done (≥8/10):** xlsx opens with **zero formula errors** (model-auditor pass);
`python valuation/build.py` runs clean and writes the xlsx + Monte Carlo PNG + JSON; all P1
tests pass (DCF, WACC, sensitivity, comps, Monte Carlo stats); the dashboard valuation view
renders from the JSON; README states methodology, limitations, and the written thesis.

---

## Project 2 — Bottleneck Map  (`/bottleneck_map`)  *(the visual hero)*
**One-line thesis:** *Follow the binding constraint: as compute scales, scarcity and capital
migrate upstream — GPUs → HBM → advanced packaging (CoWoS) → power & grid → copper & uranium.*

**What it contains**
- A model of the AI-infrastructure supply chain as ordered **layers**, each scored on a
  transparent, documented **"tightness" metric** (utilisation, lead times, capex response,
  concentration — each input sourced or flagged).
- An interactive **supply-chain flow / heatmap** (nodes = layers, colour = tightness, hover =
  underlying metrics) and a **capital-flow-over-time** chart showing where investment migrates.
- A written **thesis** linking the visual to the investment conclusion.

**Definition of Done (≥8/10):** scoring tests pass (bounds, monotonicity, weighting);
`python bottleneck_map/build.py` writes the scored JSON; the diagram is interactive with correct
colour mapping; thesis written; every number sourced or flagged.

---

## Project 3 — UK Real-Estate Underwriting + ROI Simulator  (`/real_estate`)
**One-line thesis:** *A UK residential asset's return is driven by transparent demand/supply
fundamentals — net migration, household formation, completions, rates — not by a black box;
flex the drivers and watch IRR respond.*

**(a) Acquisition model:** rent roll → cap-rate valuation → debt sizing (LTV/DSCR) → 5-year
levered cash flows → **IRR / equity multiple**, with a two-way **sensitivity grid**
(exit cap × rent growth). Excel deliverable + a TypeScript mirror for the dashboard.

**(b) Transparent ROI simulator:** sliders for the real indicators institutions underwrite —
**net migration / population growth, household formation, housing supply & completions, interest
rates, employment, rental yields**. The user flexes each assumption (especially the
migration/demand input) and sees ROI / IRR respond, with **every driver visible and documented**.

> **Critical guardrail:** this is a **transparent, assumption-driven** model, **not** a
> "news-predicts-price" black box. Immigration is **one explicit, adjustable demand driver** —
> never a hidden signal. Nothing here claims to forecast returns from news sentiment.

**Methodology / data:** HM Land Registry Price Paid + ONS (population, migration, household
formation, completions, rents), fetched and cached via the `uk-property-data` skill.

**Definition of Done (≥8/10):** xlsx zero formula errors; `python real_estate/build.py` runs
clean; all P3 tests pass (IRR, equity multiple, debt sizing/DSCR, cap-rate valuation, sensitivity
grid, simulator driver→output response); the simulator runs client-side from documented formulas
on real UK data; README states methodology and limitations.

---

## The dashboard  (`/dashboard`)
A single Next.js + Tailwind site with one institutional design system. Landing view links the
three modules each with its one-line thesis. Each module has a dedicated view:
- **Valuation:** DCF output + football-field/sensitivity heatmap + Monte Carlo distribution +
  thesis-vs-portfolio panel.
- **Bottleneck Map:** interactive supply-chain diagram + capital-flow chart.
- **Real estate:** IRR / equity-multiple summary + two-way sensitivity heatmap + the live ROI
  simulator with a slider per demand/supply driver.

Runs with one command; static-exportable for GitHub Pages / Vercel; no browser-storage APIs.
