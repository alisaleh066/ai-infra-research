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
_To be completed at end of Project 3 (base-case IRR / equity multiple, sensitivity to exit cap
and rent growth, how IRR responds to the migration/demand driver)._

## Cross-cutting thesis
_Synthesis across all three: where in the AI-infra + real-asset stack the risk-adjusted return
looks most asymmetric, and how the live/sample portfolio is positioned against it._
