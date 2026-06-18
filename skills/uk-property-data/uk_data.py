"""uk-property-data — loader for the tidy UK housing demand/supply dataset.

Loads the committed snapshot at data/uk/uk_dataset.json (reproducible offline). The public
endpoints for a live refresh are documented below; --refresh re-pulls when reachable.

Public sources:
  - HM Land Registry UK HPI (Linked Data): https://landregistry.data.gov.uk/
  - ONS API (migration, rents, households): https://api.ons.gov.uk/
  - Bank of England Bank Rate: https://www.bankofengland.co.uk/boeapps/database/
"""
from __future__ import annotations

import json
from pathlib import Path

UK_DIR = Path(__file__).resolve().parents[2] / "data" / "uk"
DATASET = UK_DIR / "uk_dataset.json"


def load_uk_dataset() -> dict:
    """Return the tidy UK dataset (regions + macro). Raises if the snapshot is missing."""
    if not DATASET.exists():
        raise FileNotFoundError(
            f"UK dataset snapshot not found at {DATASET}. Re-run with --refresh or restore it."
        )
    return json.loads(DATASET.read_text(encoding="utf-8"))


def region_yield(region: dict) -> float:
    """Gross rental yield = annual rent / price, for a region row."""
    return (region["avg_monthly_rent_gbp"] * 12) / region["avg_price_gbp"]


if __name__ == "__main__":
    d = load_uk_dataset()
    print(f"UK dataset vintage: {d['vintage']}")
    print(f"{'Region':<22}{'Price (GBP)':>14}{'Rent/mo':>10}{'Gross yield':>14}")
    for r in d["regions"]:
        print(f"{r['region']:<22}{r['avg_price_gbp']:>14,}{r['avg_monthly_rent_gbp']:>10,}"
              f"{region_yield(r):>13.1%}")
    nm = d["macro"]["net_migration"][-1]
    print(f"\nLatest net migration: {nm['value']:,} ({nm['year']}) — {nm['source']}")
