"""Tests for the screener ranking (no network)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import screen  # noqa: E402


def test_rank_orders_by_score_then_upside_none_last():
    rows = [
        {"ticker": "A", "score": 2, "upside": 0.1},
        {"ticker": "B", "score": 5, "upside": -0.2},
        {"ticker": "C", "score": None, "upside": None},
        {"ticker": "D", "score": 5, "upside": 0.3},
    ]
    ranked = [r["ticker"] for r in screen._rank(rows)]
    assert ranked[0] == "D"      # score 5, higher upside
    assert ranked[1] == "B"      # score 5, lower upside
    assert ranked[2] == "A"      # score 2
    assert ranked[-1] == "C"     # missing score sorts last


def test_watchlist_nonempty():
    assert len(screen.WATCHLIST) >= 5
