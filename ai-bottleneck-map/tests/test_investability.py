"""Tests for the investability mapping (no network — quality layer off)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import investability as inv  # noqa: E402


def test_mapping_is_tightest_first_with_tickers():
    out = inv.build(with_quality=False)
    layers = out["layers"]
    # sorted by tightness descending
    tights = [r["tightness"] for r in layers]
    assert tights == sorted(tights, reverse=True)
    # every layer has its ticker list and the binding layer (CoWoS) is first
    assert layers[0]["id"] == "cowos"
    assert all("tickers" in r for r in layers)
    assert "MU" in inv.INVESTABLE["hbm"]


def test_all_layers_have_at_least_one_ticker():
    for layer_id, tickers in inv.INVESTABLE.items():
        assert len(tickers) >= 1, layer_id
