"""Tests for the bottleneck-map tightness scoring (Project 2). Run: pytest -q"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bottleneck_map"))

from scoring import (  # noqa: E402
    DEFAULT_WEIGHTS, METRICS, binding_constraint, layer_tightness, normalize,
    score_layers, validate_weights,
)


def m(util=0.5, lead=0.5, inelas=0.5, conc=0.5) -> dict:
    return {"utilization": util, "lead_time": lead,
            "supply_inelasticity": inelas, "concentration": conc}


# --------------------------------------------------------------------------- normalize
def test_normalize_clamps():
    assert normalize(5, 0, 10) == 0.5
    assert normalize(-3, 0, 10) == 0.0
    assert normalize(99, 0, 10) == 1.0


def test_normalize_equal_bounds_raises():
    with pytest.raises(ValueError):
        normalize(1, 5, 5)


# --------------------------------------------------------------------------- bounds
def test_tightness_bounds():
    assert layer_tightness(m(0, 0, 0, 0)) == pytest.approx(0.0)
    assert layer_tightness(m(1, 1, 1, 1)) == pytest.approx(100.0)
    assert 0 <= layer_tightness(m()) <= 100


def test_tightness_midpoint_equals_50():
    assert layer_tightness(m(0.5, 0.5, 0.5, 0.5)) == pytest.approx(50.0)


# --------------------------------------------------------------------------- monotonicity
@pytest.mark.parametrize("metric", METRICS)
def test_monotonic_in_each_metric(metric):
    low = m(); high = m()
    low[metric] = 0.2
    high[metric] = 0.8
    assert layer_tightness(high) > layer_tightness(low)


# --------------------------------------------------------------------------- weighting
def test_weighting_respects_emphasis():
    # emphasise utilization -> a high-utilization layer scores higher than under equal weights
    w_util = {"utilization": 0.7, "lead_time": 0.1, "supply_inelasticity": 0.1, "concentration": 0.1}
    layer = m(util=1.0, lead=0.0, inelas=0.0, conc=0.0)
    assert layer_tightness(layer, w_util) > layer_tightness(layer, DEFAULT_WEIGHTS)


def test_validate_weights_sum():
    with pytest.raises(ValueError):
        validate_weights({"utilization": 0.5, "lead_time": 0.2,
                          "supply_inelasticity": 0.2, "concentration": 0.2})  # sums 1.1


def test_validate_weights_missing_metric():
    with pytest.raises(ValueError):
        validate_weights({"utilization": 1.0})


def test_metric_out_of_range_raises():
    with pytest.raises(ValueError):
        layer_tightness(m(util=1.5))


# --------------------------------------------------------------------------- ranking
def test_score_layers_sorted_and_binding():
    layers = [
        {"id": "a", "name": "A", "metrics": m(0.9, 0.9, 0.9, 0.9)},
        {"id": "b", "name": "B", "metrics": m(0.1, 0.1, 0.1, 0.1)},
        {"id": "c", "name": "C", "metrics": m(0.5, 0.5, 0.5, 0.5)},
    ]
    scored = score_layers(layers)
    assert [s["id"] for s in scored] == ["a", "c", "b"]      # tightest first
    assert binding_constraint(scored)["id"] == "a"


def test_real_dataset_binding_is_cowos():
    import json
    raw = json.loads((ROOT / "bottleneck_map" / "layers.json").read_text(encoding="utf-8"))
    scored = score_layers(raw["layers"])
    assert binding_constraint(scored)["id"] == "cowos"      # the known real bottleneck
