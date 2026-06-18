# Project 3 — UK Real-Estate Underwriting + ROI Simulator

Two linked pieces: **(a)** a property acquisition model (rent roll → cap-rate valuation → debt
sizing → 5-yr levered cash flows → IRR / equity multiple + a two-way sensitivity grid), and
**(b)** a **transparent ROI simulator** that maps the real demand/supply indicators institutions
underwrite on to the deal's return — with every driver visible and adjustable.

## Thesis
A UK residential asset's return is set by **transparent fundamentals**, not a black box. Demand
comes from **net migration, household formation and employment**; supply from **completions**;
financing and exit value from **interest rates** (Bank Rate → debt cost and exit cap). The
simulator makes the causal chain explicit:

```
drivers ─▶ net demand pressure ─▶ implied rent growth ─▶ NOI growth ─▶ IRR
   (migration, formation,            (explicit              ▲
    employment, completions)          elasticities)         │
Bank Rate ─▶ debt cost + exit cap ───────────────────────────┘
```

With the latest UK data (net migration ~431k vs a ~250k long-run baseline), the simulator implies
~4.2% rent growth and lifts the base deal's IRR from ~11.9% to ~18.7%. Crank migration down toward
baseline, or push completions up, and the IRR falls — visibly, through documented coefficients.

> **This is NOT a "news-predicts-price" model.** Immigration is **one explicit, adjustable demand
> driver**, never a hidden signal. Nothing here forecasts returns from news sentiment. Every
> elasticity is a stated assumption in `SimulatorCoefficients` — change it and the response is
> fully traceable.

## Method
- **Underwriting**: NOI = effective gross income × (1 − opex); valuation = NOI / entry cap; loan =
  LTV × value; interest-only debt; DSCR = NOI / debt service; exit = grown NOI / exit cap less
  selling costs and loan; IRR and equity multiple on the 5-yr equity cash flows.
- **Simulator**: `demand_pressure = wₘ·migrationΔ + w_f·formationΔ + w_e·employmentΔ − completionsΔ`
  (each a proportional deviation from baseline); `rent_growth = base + sensitivity · demand_pressure`;
  `exit_cap = base + rate_sensitivity · (BankRate − baseline)`; `debt_rate = BankRate + margin`.

## Files
| File | What |
|------|------|
| `re_engine.py` | Underwriting + simulator (pure, 15 tests) |
| `build_xlsx.py` | Builds `output/UK_underwriting.xlsx` (linked formulas, live `IRR()`) |
| `build.py` | Runs the model + simulator, exports `output/real_estate.json`, builds the xlsx |

## Run
```bash
python real_estate/build.py
pytest -q tests/test_real_estate.py
python skills/model-auditor/auditor.py real_estate/output/UK_underwriting.xlsx
```

## Verification done
- 15 unit tests pass (NOI/valuation, debt/DSCR, IRR known-values, equity multiple, sensitivity
  monotonicity, simulator: zero pressure at baseline, migration↑→IRR↑, supply↑→rent growth↓,
  rate↑→exit cap↑, and a test proving migration is one explicit term that can be zeroed out).
- `model-auditor`: zero formula errors.
- **LibreOffice recalc** reproduces the engine (IRR 11.92%, equity multiple 1.67x, DSCR 1.61x).

## Data & honesty
Demand/supply drivers come from **HM Land Registry + ONS** via the `uk-property-data` skill (see
`data/uk/uk_dataset.json`, provenance-tagged official statistics). The deal itself (a North West
6-unit block) is an **illustrative input** — replace rents/price/leverage with a real deal.
Simulator elasticities are documented assumptions.

## Limitations
- Interest-only debt with bullet repayment at exit (typical UK BTL); no amortisation schedule.
- Elasticities are calibrated assumptions, not econometric estimates — they make the *direction
  and transparency* the deliverable, not a precise point forecast.
- Single-asset, single-scenario base case; the sensitivity grid + simulator are the intended
  decision tools.

> Research/portfolio artifact — **not investment advice.**
