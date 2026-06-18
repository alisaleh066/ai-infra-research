# PROGRESS.md

Living log. Updated after every build/verify cycle. Format: done / failed / next + self-score.

## Self-scores (latest)
| Project | Self-score | Gates | Status |
|---------|-----------|-------|--------|
| 1 — Valuation (MU)      | 9 /10 | pass | model+tests+docs done; dashboard view at M4 |
| 2 — Bottleneck Map      | 9 /10 | pass | scoring+tests+docs done; dashboard view at M4 |
| 3 — Real Estate + ROI   | – /10 | – | not started |

---

## Cycle log

### M0 — Scaffold + docs + skills
- **done:** folder tree, git init, `.gitignore`, pinned `requirements.txt`, `.env.example`,
  `CLAUDE.md`, `projects.md`, `PLAN.md`, `DATA_SOURCES.md`, `PROGRESS.md`,
  README + CONCLUSIONS skeletons.
- **next:** build the 3 custom skills, then start Project 1 (fetch MU data → model → tests).
- **blocked:** none.

### M1 — Project 1: Equity Valuation (MU)
- **done:** real MU FY2022–FY2025 financials cached from SEC EDGAR; `valuation_engine.py`
  (DCF/WACC/sensitivity/comps/Monte Carlo); `MU_valuation.xlsx` with 122 linked formulas
  (blue inputs, Assumptions tab); JSON + Monte Carlo PNG exported; 13 unit tests pass;
  model-auditor PASS (zero formula errors); **LibreOffice recalc confirms Excel == engine**
  (DCF $88.45/sh, WACC 9.86%, comps $120.52, Monte Carlo median $88, P5–P95 $53–$144).
- **self-score:** 9/10 (−1: dashboard view deferred to unified build at M4).
- **next:** Project 2 — Bottleneck Map.
- **blocked:** none. Note: FMP quote/statements paywalled (402) and FMP price anomalous →
  fundamentals sourced from EDGAR, price/beta flagged as assumptions.

### M2 — Project 2: Bottleneck Map
- **done:** `scoring.py` (transparent weighted tightness metric); `layers.json` (7 layers +
  capital-flow series, provenance tagged); `build.py` exports `bottleneck.json`; 14 unit tests
  pass (bounds, monotonicity per metric, weighting, ranking, weights validation). Binding
  constraint resolves to **CoWoS advanced packaging (92.2)** — the known real bottleneck.
- **self-score:** 9/10 (−1: interactive dashboard view deferred to M4).
- **next:** Project 3 — UK real estate.
- **blocked:** none.
