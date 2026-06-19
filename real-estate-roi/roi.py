"""roi.py — run an institutional real-estate deal: underwriting + LP/GP waterfall.

Usage:
    python roi.py                 # uses deal.sample.json
    python roi.py mydeal.json     # your own deal config

Prints the underwriting + waterfall, writes output/<name>_roi.json and the Excel model, and
includes a two-way sensitivity grid (exit cap x NOI uplift) and a downside stress scenario.
"""
from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

from underwrite import Deal, equity_cash_flows, underwrite
from waterfall import WaterfallTiers, run_waterfall
import build_xlsx

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"


def load_deal(path: Path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    d = Deal(**cfg["deal"])
    tiers = WaterfallTiers([tuple(t) for t in cfg["waterfall_tiers"]]) if cfg.get("waterfall_tiers") else WaterfallTiers()
    return d, tiers, cfg.get("currency", "")


def sensitivity(d: Deal, tiers: WaterfallTiers, exit_caps, uplifts) -> dict:
    """LP IRR grid over exit cap (rows) x NOI uplift (cols)."""
    grid = []
    for ec in exit_caps:
        row = []
        for up in uplifts:
            d2 = dataclasses.replace(d, exit_cap=ec, noi_uplift_pct=up)
            row.append(run_waterfall(equity_cash_flows(d2), tiers)["lp_irr"])
        grid.append(row)
    return {"exit_caps": exit_caps, "uplifts": uplifts, "lp_irr_grid": grid}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "deal.sample.json"
    if not path.is_absolute():
        path = HERE / path
    d, tiers, ccy = load_deal(path)

    u = underwrite(d)
    w = run_waterfall(u["cash_flows"], tiers)

    exit_caps = [round(d.exit_cap + x, 4) for x in (-0.0075, -0.0025, 0.0, 0.0025, 0.0075)]
    uplifts = [0.10, 0.20, 0.30, 0.40, 0.50]
    sens = sensitivity(d, tiers, exit_caps, uplifts)

    # downside stress: higher exit cap, lower uplift, higher rate
    stress_deal = dataclasses.replace(d, exit_cap=d.exit_cap + 0.0075,
                                      noi_uplift_pct=max(d.noi_uplift_pct - 0.15, 0.0),
                                      interest_rate=d.interest_rate + 0.015)
    su = underwrite(stress_deal)
    sw = run_waterfall(su["cash_flows"], tiers)

    summary = {
        "currency": ccy, "deal": dataclasses.asdict(d), "tiers": tiers.hurdles,
        "underwriting": {k: v for k, v in u.items() if k != "cash_flows"},
        "equity_cash_flows": u["cash_flows"],
        "waterfall": {k: v for k, v in w.items() if k not in ("lp_cash_flows", "gp_cash_flows")},
        "lp_cash_flows": w["lp_cash_flows"], "gp_cash_flows": w["gp_cash_flows"],
        "sensitivity": sens,
        "downside_stress": {"project_irr": su["project_irr"], "equity_multiple": su["equity_multiple"],
                            "lp_irr": sw["lp_irr"], "min_dscr": su["min_dscr"],
                            "assumptions": "exit cap +0.75pp, uplift -15pp, rate +1.5pp"},
        "notes": "Assumption-driven, transparent institutional model. Edit deal.sample.json. "
                 "GP co-invest = 0 (earns only promote). Not investment advice.",
    }
    name = path.stem
    (OUT / f"{name}_roi.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    xlsx = build_xlsx.build(d, tiers, u, w, sens, ccy)

    cur = ccy + " " if ccy else ""
    print(f"=== {name} — institutional underwriting ({ccy or 'currency-agnostic'}) ===")
    print(f"Purchase price   : {cur}{d.purchase_price:,.0f}   total cost {cur}{u['total_cost']:,.0f}")
    print(f"Equity invested  : {cur}{u['equity']:,.0f}   loan {cur}{u['loan']:,.0f} (LTV {u['ltv']:.0%}, LTC {u['ltc']:.0%})")
    print(f"Debt yield       : {u['debt_yield']:.1%}   min DSCR {u['min_dscr']:.2f}x")
    print(f"Stabilized NOI   : {cur}{u['stabilized_noi']:,.0f}   exit value {cur}{u['exit_value']:,.0f}")
    print(f"--- returns ---")
    print(f"Project IRR      : {u['project_irr']:.1%}   equity multiple {u['equity_multiple']:.2f}x   avg CoC {u['avg_cash_on_cash']:.1%}")
    print(f"LP   IRR         : {w['lp_irr']:.1%}   LP equity multiple {w['lp_equity_multiple']:.2f}x")
    print(f"GP   promote     : {cur}{w['gp_promote']:,.0f}   ({w['gp_share_of_profit']:.1%} of profit)   promote drag {w['promote_drag']:.1%}")
    print(f"Downside (stress): project IRR {su['project_irr']:.1%}, LP IRR {sw['lp_irr']:.1%}, min DSCR {su['min_dscr']:.2f}x")
    print(f"\nWrote: {OUT / (name + '_roi.json')}")
    print(f"Wrote: {xlsx}")


if __name__ == "__main__":
    main()
