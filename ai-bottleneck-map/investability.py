"""investability.py — turn the bottleneck map into actionable names.

Maps each supply-chain layer to its investable US-listed tickers, ordered by layer tightness, so
the output reads: "the tightest layer is X -> own it via these names." With --quality it reaches
into the sibling `equity-valuation` project and pulls a quick fundamental snapshot per ticker
(ROIC vs a hurdle, Piotroski F-Score, a quality rating) — making the three projects one system.

    python investability.py            # mapping only (fast, offline once cached)
    python investability.py --quality  # + live fundamental snapshot per ticker
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scoring import score_layers, DEFAULT_WEIGHTS  # noqa: E402

# Investable US-listed names per layer (ADRs where the leader isn't US-listed).
INVESTABLE = {
    "gpu": ["NVDA", "AMD"],
    "hbm": ["MU"],                       # SK Hynix / Samsung are not US-listed
    "cowos": ["TSM", "AMKR"],            # TSMC (ADR) + Amkor (OSAT packaging)
    "foundry": ["TSM", "INTC", "GFS"],
    "power": ["VST", "CEG", "GEV", "ETN"],
    "copper": ["FCX", "SCCO"],
    "uranium": ["CCJ", "LEU"],
}
HURDLE = 0.10  # quality screen hurdle for ROIC vs WACC (documented assumption)


def _quality(tickers: list[str]) -> dict:
    """Optional fundamental snapshot via the equity-valuation project (graceful if unavailable)."""
    eq = HERE.parent / "equity-valuation"
    if not eq.exists():
        return {}
    sys.path.insert(0, str(eq))
    try:
        import data as eqdata          # noqa: E402
        import analysis as eqan        # noqa: E402
    except Exception:                  # noqa: BLE001
        return {}
    out = {}
    for t in tickers:
        try:
            f = eqdata.fetch_fundamentals(t)
            rep = {
                "roic_vs_wacc": eqan.roic_vs_wacc(f, HURDLE),
                "piotroski": eqan.piotroski_f(f),
                "altman_z": eqan.altman_z(f, None),
                "beneish_m": eqan.beneish_m(f),
                "sloan": eqan.sloan_accruals(f),
                "upside": None,
            }
            roic = rep["roic_vs_wacc"].get("roic")
            out[t] = {
                "roic": round(roic, 4) if roic is not None else None,
                "f_score": rep["piotroski"].get("score"),
                "quality_rating": eqan.recommend(rep)["rating"],
            }
        except Exception as e:  # noqa: BLE001
            out[t] = {"flag": f"unavailable: {e}"}
    return out


def build(with_quality: bool = False) -> dict:
    raw = json.loads((HERE / "layers.json").read_text(encoding="utf-8"))
    scored = score_layers(raw["layers"], DEFAULT_WEIGHTS)   # tightest first
    rows = []
    for layer in scored:
        tickers = INVESTABLE.get(layer["id"], [])
        row = {"layer": layer["name"], "id": layer["id"], "tightness": layer["tightness"],
               "tickers": tickers}
        if with_quality:
            row["quality"] = _quality(tickers)
        rows.append(row)
    out = {"hurdle": HURDLE, "with_quality": with_quality, "layers": rows}
    (HERE / "output").mkdir(exist_ok=True)
    (HERE / "output" / "investability.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def main() -> None:
    wq = "--quality" in sys.argv
    out = build(with_quality=wq)
    print("Investability — own the bottleneck (tightest layer first):\n")
    for r in out["layers"]:
        line = f"  {r['tightness']:5.1f}  {r['layer']:<28} {', '.join(r['tickers']) or '-'}"
        print(line)
        if wq:
            for t, q in r.get("quality", {}).items():
                if "flag" in q:
                    print(f"           {t}: {q['flag']}")
                else:
                    roic = f"{q['roic']*100:.0f}%" if q["roic"] is not None else "n/a"
                    print(f"           {t}: ROIC {roic} vs {int(HURDLE*100)}% hurdle · "
                          f"F-Score {q['f_score']}/9 · quality {q['quality_rating']}")
    print(f"\nWrote: {HERE/'output'/'investability.json'}")
    if not wq:
        print("Tip: add --quality for a live fundamental snapshot per ticker.")


if __name__ == "__main__":
    main()
