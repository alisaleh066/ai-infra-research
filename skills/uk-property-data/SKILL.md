---
name: uk-property-data
description: Provide tidy, sourced UK housing and demand/supply data (house prices, rents, net migration, household formation, completions, Bank Rate) from HM Land Registry and ONS, cached locally for offline reproducibility. Use for the UK real-estate underwriting model and ROI simulator.
---

# uk-property-data

## Purpose
Supply Project 3 with the real demand/supply indicators institutions underwrite on, in one tidy
local table, with each figure tagged to its public source (HM Land Registry / ONS / Bank of
England). Data is cached under `data/uk/` so the model runs offline after first fetch.

## Datasets provided (`uk_data.py → load_uk_dataset()`)
- **House prices** — HM Land Registry UK House Price Index (national + regional averages).
- **Private rents** — ONS Price Index of Private Rents (PIPR) / median rents.
- **Net migration** — ONS Long-Term International Migration (LTIM) estimates.
- **Household formation** — ONS / household projections (net additional households).
- **Housing supply** — MHCLG net additional dwellings (England).
- **Interest rate** — Bank of England Bank Rate.
- **Gross rental yield** — derived (annual rent ÷ price), per region.

## Provenance & honesty
Every figure in `data/uk/uk_dataset.json` carries a `source` tag and is a **published public
statistic**. Values are rounded to the precision of the source release and dated. Anything not
sourced is tagged `assumption`. These are official-statistics snapshots for modelling, **not**
real-time feeds — see each figure's `source` and `vintage`.

## Usage
```python
from uk_data import load_uk_dataset
d = load_uk_dataset()              # dict; loads cache, falls back to bundled snapshot
regions = d["regions"]             # per-region price/rent/yield
macro   = d["macro"]               # net migration, formation, completions, bank rate
```

## Live refresh (optional)
`uk_data.py` documents the public endpoints (Land Registry Linked Data / ONS API). The bundled
snapshot is committed so the repo is reproducible without network; re-run with `--refresh` to
re-pull when those services are reachable.
