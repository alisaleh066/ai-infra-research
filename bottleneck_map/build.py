"""build.py — Project 2 entry point: score the supply-chain layers and export JSON.

Run:  python bottleneck_map/build.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bottleneck_map"))

from scoring import DEFAULT_WEIGHTS, binding_constraint, score_layers  # noqa: E402

OUT = ROOT / "bottleneck_map" / "output"
DASH = ROOT / "dashboard" / "public" / "data"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DASH.mkdir(parents=True, exist_ok=True)
    raw = json.loads((ROOT / "bottleneck_map" / "layers.json").read_text(encoding="utf-8"))
    scored = score_layers(raw["layers"], DEFAULT_WEIGHTS)
    binder = binding_constraint(scored)

    # capital migration: share of capital by layer over time (normalised per year)
    cf = raw["capital_flow"]
    years = cf["years"]
    series = cf["series"]
    shares = {lid: [] for lid in series}
    for i, _ in enumerate(years):
        total = sum(series[lid][i] for lid in series)
        for lid in series:
            shares[lid].append(round(series[lid][i] / total, 4))

    summary = {
        "weights": DEFAULT_WEIGHTS,
        "tag": raw["tag"],
        "provenance": raw["provenance"],
        "layers": scored,
        "binding_constraint": {"id": binder["id"], "name": binder["name"],
                               "tightness": binder["tightness"]},
        "capital_flow": {"years": years, "absolute": series, "shares": shares,
                         "tag": cf["tag"], "note": cf["_note"]},
    }
    for d in (OUT, DASH):
        (d / "bottleneck.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Tightness ranking (tightest first):")
    for s in scored:
        print(f"  {s['tightness']:5.1f}  {s['name']}")
    print(f"\nBinding constraint: {binder['name']} ({binder['tightness']:.1f})")
    print(f"Wrote: {OUT/'bottleneck.json'}")


if __name__ == "__main__":
    main()
