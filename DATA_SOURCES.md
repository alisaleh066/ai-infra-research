# DATA_SOURCES.md

Discovered data connectors and the provenance of every dataset in this repo. Principle:
**never fabricate a financial figure** — fetched values are sourced here; anything not
fetchable is a clearly-labelled assumption surfaced in the model + UI.

## MCP / connector discovery (at build time, 2026-06-18)
| Connector | Status | Used for |
|-----------|--------|----------|
| `edgartools` (SEC EDGAR) | ✅ connected, working | **Primary** fundamentals for MU (10-K income statement, balance sheet, cash flow) |
| `stocks` (FMP) | ⚠️ partial — free tier | Company profile/metadata only. `get_quote` + statements return **402 Payment Required** |
| `eodhd` | ✅ available | Macro series + price fallback (not required for P1) |
| `finnhub` | ✅ available | Estimates / news fallback |
| `alpha-vantage` | ✅ available | Price/FX fallback |
| **Trading212** | ❌ **not connected** | Thesis-vs-portfolio falls back to `data/sample_positions.json` (flagged) |
| UK housing/property MCP | ❌ none | Project 3 uses free public sources (Land Registry + ONS) |

## Data quality flags
- **FMP profile price anomaly:** the `stocks` profile returned MU price **$1,144** and market
  cap **$1.29T**, both implausible (real MU ≈ $130 / ≈ $145B). These fields were **rejected**.
  Share price + beta are treated as **labelled ASSUMPTION inputs** in the valuation model and
  are user-adjustable. EDGAR fundamentals were independently sanity-checked against Micron's
  known reported results (rev $30.8B→$15.5B→$25.1B→$37.4B FY22→FY25) and match.

## Project 1 — Equity Valuation (MU)
| Dataset | Source | File | Notes |
|---------|--------|------|-------|
| Income statement, balance sheet, cash flow (FY2022–FY2025) | SEC EDGAR 10-K via `edgartools` | `data/mu_financials.json` | Audited values, $m |
| Company profile (CIK, sector) | FMP via `stocks` | inline | Metadata only |
| Share price, beta, rates | **ASSUMPTION** | `data/mu_financials.json → market_inputs_ASSUMPTION` | Replace with live figures |
| Sample portfolio | placeholder (no Trading212 MCP) | `data/sample_positions.json` | Flagged in UI |

## Project 2 — Bottleneck Map
| Dataset | Source | File | Notes |
|---------|--------|------|-------|
| Supply-chain layer metrics (utilisation, lead times, capex, concentration) | Curated from public disclosures + flagged estimates | `bottleneck_map/layers.json` | Each input tagged `sourced` or `assumption` |

## Project 3 — UK Real Estate
| Dataset | Source | File | Notes |
|---------|--------|------|-------|
| House prices (Price Paid) | HM Land Registry (Open Government Licence) | `data/uk/` (cached) | Fetched via `uk-property-data` skill |
| Population / net migration / household formation / completions / rents | ONS | `data/uk/` (cached) | Fetched via `uk-property-data` skill |

All raw pulls cached under `data/` so the repo is reproducible offline after first fetch.
