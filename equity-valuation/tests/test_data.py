"""Data-layer tests (no network): XBRL parsing, tag-fallback merge, no-fabrication."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data  # noqa: E402


def _facts(tagvals: dict) -> dict:
    """Build a minimal companyfacts dict. tagvals: {tag: [(start,end,val,filed,form)]}."""
    us = {}
    for tag, items in tagvals.items():
        us[tag] = {"units": {"USD": [
            {"start": s, "end": e, "val": v, "filed": f, "form": fm, "fp": "FY"}
            for (s, e, v, f, fm) in items
        ]}}
    return {"facts": {"us-gaap": us}}


def test_annual_series_keys_by_period_end_not_filing():
    # one 10-K filed in 2025 contains FY2023, FY2024 comparatives — must NOT collapse to one year
    facts = _facts({"Revenues": [
        ("2023-01-01", "2023-12-31", 100, "2025-02-01", "10-K"),
        ("2024-01-01", "2024-12-31", 120, "2025-02-01", "10-K"),
    ]})
    s = data._annual_series(facts, "Revenues")
    assert s == {2023: 100, 2024: 120}


def test_annual_series_skips_non_annual_durations():
    facts = _facts({"Revenues": [
        ("2024-10-01", "2024-12-31", 30, "2025-02-01", "10-K"),   # quarterly -> skip
        ("2024-01-01", "2024-12-31", 120, "2025-02-01", "10-K"),  # annual -> keep
    ]})
    assert data._annual_series(facts, "Revenues") == {2024: 120}


def test_annual_series_prefers_latest_filing_for_restatement():
    facts = _facts({"Revenues": [
        ("2023-01-01", "2023-12-31", 100, "2024-02-01", "10-K"),
        ("2023-01-01", "2023-12-31", 105, "2025-02-01", "10-K"),  # restated, later filing wins
    ]})
    assert data._annual_series(facts, "Revenues") == {2023: 105}


def test_pick_merges_tags_recent_coverage_first():
    # mimic NVDA: recent years under Revenues, old years under the long tag
    facts = _facts({
        "RevenueFromContractWithCustomerExcludingAssessedTax": [
            ("2019-01-01", "2019-12-31", 50, "2020-02-01", "10-K"),
            ("2020-01-01", "2020-12-31", 60, "2021-02-01", "10-K"),
        ],
        "Revenues": [
            ("2024-01-01", "2024-12-31", 200, "2025-02-01", "10-K"),
            ("2025-01-01", "2025-12-31", 300, "2026-02-01", "10-K"),
        ],
    })
    merged = data._pick(facts, "revenue")
    assert merged[2024] == 200 and merged[2025] == 300 and merged[2019] == 50


def test_pick_returns_empty_when_no_tag_present():
    assert data._pick(_facts({}), "revenue") == {}
