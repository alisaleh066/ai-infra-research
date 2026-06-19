# Micron Technology (MU) — Investment Memo

*One-page IC memo. Author: Ali Saleh Al Taher. Fundamentals: SEC EDGAR (audited 10-K). Valuation:
hand-built scenario DCF (`mu_thesis_model.py`) + live peer comps (`comps_live.py`). Numbers refresh
when you run the model; figures below are from the committed run. **Not investment advice.***

## Recommendation: **Accumulate on weakness** — own the HBM bottleneck, but size for the cycle
MU is the cleanest US-listed way to own **High-Bandwidth Memory (HBM)** — the layer my
bottleneck-map work flags as one of the tightest in the AI build-out (tied with CoWoS packaging).
The scenario DCF says this is **not a cheap stock on a normalized mid-cycle**, but it is an
**asymmetric bet on HBM tightness persisting**. Base case fair value **~$60**, bull **~$127**, bear
**~$12**; probability-weighted **~$65**. The call is therefore conviction- and sizing-driven, not
"buy at any price."

## The variant perception (why the market and I may disagree)
Consensus treats Micron as a *commodity DRAM* cyclical that happens to sell some HBM. **My view:
HBM is structurally different** — it is sold out on long-term agreements, priced on a cost-plus
basis, capacity-rationed by advanced packaging, and supplied by a rational 3-player oligopoly
(Micron, SK Hynix, Samsung). If HBM is a *structurally higher-margin annuity* rather than a normal
DRAM up-cycle, mid-cycle margins settle materially above history — that is the bull case ($127) and
the source of edge. The bear case is the mirror: HBM gets commoditized as Samsung qualifies at
scale and the broader DRAM cycle rolls over (FY27).

## Three drivers that decide the outcome
1. **HBM share & pricing.** Does Micron hold ~20-25% HBM share and defend cost-plus pricing? (Bull
   vs base hinges here.)
2. **Mid-cycle EBIT margin.** History says memory margins are violently cyclical; the thesis is that
   the AI memory mix lifts the *trough-to-peak average*. Base fades margin to ~24%, bull holds ~29%.
3. **Capex discipline.** Micron spends 30-40% of revenue on capex. FCF — and therefore the DCF —
   lives or dies on capex normalizing toward maintenance rather than an arms race. This is the
   single biggest swing in the model.

## What would make me wrong (the kill criteria)
- **Samsung HBM3E/4 qualifies broadly** at hyperscalers → oligopoly cracks, pricing rolls over.
- **Hyperscaler AI capex digestion** → memory demand air-pocket (bear path: FY27 revenue −10%).
- **Capex stays elevated indefinitely** to defend share → FCF never inflects, DCF compresses toward
  the bear value even if revenue holds.
- A balance-sheet sanity check failing on the live feed (always verify price/share count on run).

## Catalysts (next 6-18 months)
HBM3E/HBM4 qualification news at major GPU customers · quarterly DRAM/NAND pricing prints ·
Micron capex guidance (the FCF tell) · hyperscaler capex commentary · memory inventory data points.

## Valuation summary (from the committed model run)
| Scenario | Prob | WACC | Fair value/share | Hinges on |
|----------|-----:|-----:|-----------------:|-----------|
| Bear | 25% | 12.5% | ~$12 | Oversupply returns FY27, margin collapses |
| Base | 50% | 11.0% | ~$60 | HBM tight into 2026, DRAM normalizes (not crashes) |
| Bull | 25% | 10.0% | ~$127 | HBM stays the binding constraint, structurally higher margin |
| **Weighted** | | | **~$65** | |

**Comps cross-check:** run `python comps_live.py MU` for live peer-median EV/EBITDA & P/E (memory +
broad semis). Treat the DCF as the anchor and comps as a sanity check — and verify the price feed,
since a bad quote makes every multiple meaningless.

## Position sizing (how I'd actually hold it)
A volatile, high-beta single name with a wide outcome distribution → a **conviction position, not a
core holding**: scale in on cyclical weakness, trim into euphoria, and re-underwrite at every capex
guide. In my own GBP book this sits as the single-name expression of a broader "long the AI memory
bottleneck" theme (the rest expressed via diversified semis exposure). See `../INVESTMENT_THESIS.md`.
