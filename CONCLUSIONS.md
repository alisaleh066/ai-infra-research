# CONCLUSIONS.md — investment takeaways

> Filled in as each project completes. Numbers reference the artifacts each model produces;
> assumptions are flagged as such.

## 1. Equity Valuation — Micron (MU)
Built on audited SEC EDGAR financials (FY2022–FY2025). Base-case **DCF fair value ≈ $88/share**
at a **9.9% WACC** and 2.5% terminal growth. The **comps cross-check is higher (~$120/share)** on
sector-typical EV/EBITDA (8×) and P/E (15×) — both flagged assumptions. **Monte Carlo** (10,000
draws on growth, margin, WACC, terminal growth) gives a median ≈ $88 with a wide **P5–P95 of
~$53–$144**, reflecting memory cyclicality.

**Takeaway:** the valuation is dominated by two levers — **capex intensity** (Micron's biggest
swing) and **mid-cycle margin**. The DCF says the upside is conditional, not given: at a normalised
capex (~30% of revenue) and a fading HBM upcycle, intrinsic value sits below an (assumed) $130
market price, while the comps lens is more generous. The honest conclusion is a **wide range, not
a point** — the asymmetry depends heavily on whether HBM margins hold above mid-cycle. Plug live
price/beta/peer multiples in to refresh the upside/downside.

## 2. Bottleneck Map
Scoring the AI-infra chain on a transparent tightness metric, the **binding constraint is
advanced packaging (CoWoS, tightness ≈ 92)**, narrowly ahead of HBM (≈ 87) and leading-edge
foundry (≈ 87) — consistent with CoWoS capacity being the widely-reported gate on accelerator
shipments. Power & grid (≈ 82) is the fastest-rising constraint behind them.

**Takeaway:** the asymmetric return is upstream of the GPU, not in it. The capital-flow view shows
spend migrating toward packaging, HBM and power — so the investable read is **own the bottleneck,
not the headline chip**: TSMC-adjacent packaging, the HBM oligopoly (ties directly to Project 1's
Micron), and the power/grid layer that the next wave of capital is only now reaching.

## 3. UK Real Estate
The illustrative North West 6-unit block underwrites to a **base-case levered IRR ≈ 11.9%** and
**equity multiple ≈ 1.67x** at a 1.6x DSCR. The two-way grid shows IRR is most sensitive to **exit
cap** (re-rating risk) and **rent growth**. Running the **ROI simulator on the latest UK data**
(net migration ~431k vs a ~250k baseline) implies ~4.2% rent growth and lifts IRR to **~18.7%**.

**Takeaway:** the return is a transparent function of demand vs supply. Migration is the largest
single swing among the demand drivers, but it is **one explicit, adjustable input** — dial it back
to baseline and the IRR compresses toward the low-teens; raise completions (supply) and it falls
further. The honest message for an underwriter: UK residential return today leans heavily on the
demand side staying elevated and rates easing the exit cap — both visible, both stress-testable.

## Cross-cutting thesis
Three lenses, one conclusion: **the durable return in this cycle is upstream and physical.**

- The **bottleneck map** locates the scarcity — advanced packaging, HBM and power — not the
  headline GPU.
- The **Micron valuation** prices one of those bottlenecks (HBM) on audited numbers and finds the
  upside is real but *conditional* on capex discipline and margins holding above mid-cycle — a wide
  distribution, not a sure thing.
- The **UK real-estate model** shows the same discipline applied to a real asset: return is a
  transparent function of demand vs supply, and today leans on elevated migration and easing rates
  — both explicitly stress-testable rather than assumed.

**Where the risk-adjusted return looks most asymmetric:** the tightest, most concentrated layers
with the slowest supply response (packaging/HBM, then power) — exactly where the (sample) portfolio
is already weighted. The honest throughline across all three is **transparency over false
precision**: every figure is sourced or flagged, every model exposes its assumptions, and the
ranges (sensitivity grids, Monte Carlo, the live ROI simulator) matter more than any single number.

> Research/portfolio artifact — **not investment advice.**
