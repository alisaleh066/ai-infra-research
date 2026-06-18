# Project 2 — AI-Infrastructure Bottleneck Map

Maps the AI-infrastructure supply chain as ordered layers, scores each on a transparent
**tightness** metric, and shows where the **binding constraint** sits and how **capital migrates
upstream** as each constraint binds.

## Thesis
Compute demand is effectively unlimited relative to the physical chain that produces it. The
return, therefore, accrues to whichever layer is **tightest** — where supply cannot respond at
any price in the near term. As the market spends to relieve one constraint, scarcity (and
capital) moves to the next layer up: **GPUs → HBM → advanced packaging (CoWoS) → leading-edge
foundry → power & grid → copper & uranium.**

The model's conclusion (with the default weights) is that **advanced packaging (CoWoS) is the
current binding constraint** (tightness ≈ 92), narrowly ahead of HBM and leading-edge foundry —
consistent with widely-reported CoWoS capacity being the gating factor on accelerator shipments.
The **capital-flow view** shows packaging, HBM and power growing fastest as a share of total
spend — i.e. capital chasing the binding constraints upstream, exactly where the investable
opportunity migrates.

## The tightness metric (transparent)
Tightness = 100 · Σ wᵢ·mᵢ over four sub-metrics, each normalised to [0,1] (higher = tighter):

| Metric | Weight | Meaning |
|--------|-------:|---------|
| utilization | 0.30 | capacity utilisation (sold-out → 1) |
| lead_time | 0.25 | time to add supply (years-long → 1) |
| supply_inelasticity | 0.25 | how slowly supply responds to price |
| concentration | 0.20 | supplier concentration / fragility |

Weights are explicit and editable in `scoring.py`; the score is a plain weighted average, not a
black box. `validate_weights` enforces that weights sum to 1 and cover every metric.

## Files
| File | What |
|------|------|
| `scoring.py` | Pure, tested tightness-scoring engine |
| `layers.json` | The 7 layers + curated sub-metrics + capital-flow series (provenance tagged) |
| `build.py` | Scores layers, computes capital-migration shares, exports `output/bottleneck.json` |

## Run
```bash
python bottleneck_map/build.py
pytest -q tests/test_bottleneck.py
```

## Data & honesty
Sub-metric levels are **curated estimates** informed by public earnings commentary and industry
reporting (TSMC CoWoS capacity, HBM "sold out" commentary, grid/transformer lead times, copper
mine timelines, uranium supply) — they are **directional, not measured**, and tagged `curated`.
The capital-flow series is **illustrative** (tagged `illustrative`), showing relative intensity
and migration, not audited capex totals. The *method* is the deliverable; swap in measured inputs
to harden the numbers.

## Limitations
- Tightness is a relative ranking under a chosen weighting, not an absolute scarcity measure.
- Sub-metrics are point-in-time estimates; the real chain shifts quarter to quarter.
- Capital-flow magnitudes are indices, not exact spend.

> Research/portfolio artifact — **not investment advice.**
