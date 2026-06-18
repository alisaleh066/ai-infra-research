---
name: financial-data-fetcher
description: Fetch and cache company fundamentals, prices and macro series, wrapping the connected market-data MCPs (edgartools / stocks / eodhd / finnhub / alpha-vantage) with a documented fallback chain and a strict no-fabrication policy. Use whenever a project needs financial/market data.
---

# financial-data-fetcher

## Purpose
A single, auditable entry point for market data so every project sources numbers the same way
and **never fabricates a figure**. Fundamentals come from SEC EDGAR (audited); prices/macro from
market-data MCPs with fallbacks. Everything is cached to `data/` so the repo runs offline after
the first fetch.

## Fallback chain (highest-trust first)
1. **Fundamentals** → SEC EDGAR (`edgartools` MCP) → cache. This is the source of truth for
   income statement / balance sheet / cash flow.
2. **Company metadata** (CIK, sector) → `stocks` (FMP) profile.
3. **Price / quote** → `stocks` → `eodhd` → `alpha-vantage`. If all unavailable or a returned
   value fails a sanity check, store it as a **labelled ASSUMPTION**, never as fact.
4. **Macro** (rates, CPI) → `eodhd` macro / FRED-style series.

## No-fabrication rule
If a value cannot be fetched or fails a sanity bound, call `assumption(value, note)` which tags
it so the model and UI render it as "input — replace with your figure" (blue in Excel). Record
the source and retrieval date in `DATA_SOURCES.md`.

## Sanity checks (applied to fetched prices)
- equity price must be `> 0` and within a configured plausibility band; otherwise → assumption.
  (At build time the FMP profile returned MU at $1,144 — rejected by this rule.)

## API (`fetcher.py`)
- `load_cache(name)` / `save_cache(name, obj)` — JSON cache under `data/`.
- `assumption(value, note)` → `{"value":..., "is_assumption": True, "note":...}`.
- `sourced(value, source, retrieved)` → tagged sourced value.
- `sanity_price(value, low, high)` → value or `None` if out of band.

## How agents use it
The actual MCP calls are made by the agent (tools `mcp__edgartools__*`, `mcp__stocks__*`, …);
this module standardises caching, tagging and the no-fabrication contract around those calls.
Raw MCP pulls are saved to `data/` and tidy derived data committed for offline reproducibility.
