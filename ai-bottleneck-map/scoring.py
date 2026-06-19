"""scoring — transparent "tightness" scoring for AI-infrastructure supply-chain layers.

Each layer carries four sub-metrics, each already normalised to [0, 1] where **higher = tighter**:
  - utilization        : capacity utilisation (sold-out → 1)
  - lead_time          : normalised lead time to add supply (years-long → 1)
  - supply_inelasticity: how slowly supply can respond to price (inelastic → 1)
  - concentration      : supplier concentration / fragility (few players → 1)

Tightness = 100 · Σ wᵢ·mᵢ  (weights sum to 1). Pure, unit-tested functions; no I/O.
"""
from __future__ import annotations

from typing import Mapping

DEFAULT_WEIGHTS: dict[str, float] = {
    "utilization": 0.30,
    "lead_time": 0.25,
    "supply_inelasticity": 0.25,
    "concentration": 0.20,
}
METRICS = tuple(DEFAULT_WEIGHTS)


def normalize(value: float, lo: float, hi: float) -> float:
    """Min-max normalise into [0, 1] (clamped). hi must differ from lo."""
    if hi == lo:
        raise ValueError("hi and lo must differ")
    return max(0.0, min(1.0, (value - lo) / (hi - lo)))


def validate_weights(weights: Mapping[str, float]) -> None:
    if abs(sum(weights.values()) - 1.0) > 1e-9:
        raise ValueError(f"weights must sum to 1.0 (got {sum(weights.values())})")
    missing = set(METRICS) - set(weights)
    if missing:
        raise ValueError(f"weights missing metrics: {sorted(missing)}")


def layer_tightness(metrics: Mapping[str, float],
                    weights: Mapping[str, float] = DEFAULT_WEIGHTS) -> float:
    """Weighted tightness score in [0, 100]. Each metric must be in [0, 1]."""
    validate_weights(weights)
    for m in METRICS:
        v = metrics[m]
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"metric {m}={v} out of [0,1]")
    return 100.0 * sum(weights[m] * metrics[m] for m in METRICS)


def score_layers(layers: list[dict],
                 weights: Mapping[str, float] = DEFAULT_WEIGHTS) -> list[dict]:
    """Attach a tightness score to each layer; return sorted tightest-first."""
    scored = []
    for layer in layers:
        s = layer_tightness(layer["metrics"], weights)
        scored.append({**layer, "tightness": round(s, 1)})
    return sorted(scored, key=lambda x: x["tightness"], reverse=True)


def binding_constraint(scored: list[dict]) -> dict:
    """The tightest layer — the current binding constraint."""
    return max(scored, key=lambda x: x["tightness"])
