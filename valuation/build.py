"""build.py — Project 1 entry point.

Loads cached MU EDGAR fundamentals, sets explicit (documented) DCF assumptions, runs the
valuation engine + Monte Carlo, builds the Excel model, and exports JSON + a distribution PNG
to valuation/output/ and dashboard/public/data/ for the dashboard.

Run:  python valuation/build.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "valuation"))
sys.path.insert(0, str(ROOT / "skills" / "financial-data-fetcher"))

from valuation_engine import (  # noqa: E402
    DCFAssumptions, MonteCarloSpec, comps_valuation, enterprise_value, monte_carlo,
    sensitivity_grid, wacc,
)
import build_xlsx  # noqa: E402

OUT = ROOT / "valuation" / "output"
DASH = ROOT / "dashboard" / "public" / "data"


def load_fundamentals() -> dict:
    return json.loads((ROOT / "data" / "mu_financials.json").read_text(encoding="utf-8"))


def build_assumptions(f: dict) -> DCFAssumptions:
    """Construct the base-case DCF assumptions from FY2025 EDGAR actuals + flagged inputs."""
    inc, bs, cf = f["income_statement"], f["balance_sheet"], f["cash_flow"]
    mk = f["market_inputs_ASSUMPTION"]
    base_rev = inc["revenue"]["2025"]                    # 37,378 (EDGAR)
    da = cf["depreciation_amort"]["2025"]
    # ASSUMPTION block — documented in valuation/README.md and DATA_SOURCES.md
    return DCFAssumptions(
        base_revenue=base_rev,
        # HBM-led upcycle fading to mid-cycle growth (ASSUMPTION)
        rev_growth=[0.22, 0.12, 0.08, 0.05, 0.04],
        # EBIT margin normalising around mid-cycle (ASSUMPTION); FY25 actual ~26.1%
        ebit_margin=[0.27, 0.28, 0.27, 0.26, 0.25],
        tax_rate=mk["tax_rate"],
        da_pct_rev=round(da / base_rev, 4),              # ~0.224 from actuals
        capex_pct_rev=0.30,                              # fades from FY25's elevated 42% (ASSUMPTION)
        nwc_pct_rev_change=0.10,                         # incremental NWC (ASSUMPTION)
        terminal_growth=0.025,
        risk_free=mk["risk_free_rate"],
        erp=mk["equity_risk_premium"],
        beta=mk["beta"],
        pretax_kd=mk["pretax_cost_of_debt"],
        equity_value=mk["share_price_usd"] * mk["shares_outstanding_m"],
        debt_value=bs["long_term_debt"]["2025"],
        cash=bs["cash_and_equivalents"]["2025"],
        shares=mk["shares_outstanding_m"],
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DASH.mkdir(parents=True, exist_ok=True)
    f = load_fundamentals()
    a = build_assumptions(f)

    # Make the sample portfolio importable by the dashboard (no Trading212 MCP connected).
    import shutil
    src_pos = ROOT / "data" / "sample_positions.json"
    if src_pos.exists():
        shutil.copyfile(src_pos, DASH / "portfolio.json")

    dcf = enterprise_value(a)
    w = dcf["wacc"]

    # Sensitivity grid: WACC +/- 1.5%, terminal growth 1.5%-3.5%
    waccs = [round(w + d, 4) for d in (-0.015, -0.0075, 0.0, 0.0075, 0.015)]
    growths = [0.015, 0.020, 0.025, 0.030, 0.035]
    grid = sensitivity_grid(a, waccs, growths)

    # Comps (peer multiples are ASSUMPTION — semis-sector typical; flagged)
    inc, cf = f["income_statement"], f["cash_flow"]
    ebitda = inc["operating_income"]["2025"] + cf["depreciation_amort"]["2025"]
    eps = inc["eps_diluted"]["2025"]
    net_debt = a.debt_value - a.cash
    comps = comps_valuation(ebitda, eps, net_debt, a.shares,
                            ev_ebitda_mult=8.0, pe_mult=15.0)  # ASSUMPTION multiples

    # Monte Carlo
    mc = monte_carlo(a, MonteCarloSpec(n=10000, seed=42))

    market_price = f["market_inputs_ASSUMPTION"]["share_price_usd"]

    summary = {
        "company": f["company"], "ticker": f["ticker"],
        "as_of": "FY2025 actuals (SEC EDGAR) + flagged market assumptions",
        "wacc": w,
        "cost_of_equity": a.risk_free + a.beta * a.erp,
        "dcf": {
            "value_per_share": dcf["value_per_share"],
            "enterprise_value_m": dcf["enterprise_value"],
            "equity_value_m": dcf["equity_value"],
            "pv_fcff_m": dcf["pv_fcff"],
            "pv_terminal_value_m": dcf["pv_terminal_value"],
            "tv_pct_of_ev": dcf["tv_pct_of_ev"],
            "projection": [
                {k: round(v, 2) for k, v in r.items()} for r in dcf["rows"]
            ],
        },
        "comps": comps,
        "sensitivity": {"waccs": waccs, "growths": growths, "grid": grid},
        "monte_carlo": {k: v for k, v in mc.items() if k != "samples"},
        "market_price_ASSUMPTION": market_price,
        "upside_vs_market": dcf["value_per_share"] / market_price - 1,
        "notes": "Fundamentals: SEC EDGAR 10-K. Price/beta/peer multiples are flagged "
                 "assumptions (see DATA_SOURCES.md). Replace with live figures to update.",
    }

    # Write JSON (output + dashboard)
    for d in (OUT, DASH):
        (d / "valuation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    # Monte Carlo samples for the dashboard histogram (separate, larger file)
    (DASH / "valuation_mc.json").write_text(
        json.dumps({"samples": mc["samples"][:5000], "stats": summary["monte_carlo"],
                    "dcf": dcf["value_per_share"], "market": market_price}, indent=2),
        encoding="utf-8")

    # Monte Carlo distribution PNG
    _plot_mc(mc["samples"], dcf["value_per_share"], market_price)

    # Excel model
    xlsx_path = build_xlsx.build(f, a, dcf, comps, waccs, growths, grid, summary)

    print(f"WACC                 : {w:.2%}")
    print(f"DCF value / share    : ${dcf['value_per_share']:.2f}")
    print(f"Comps midpoint /share: ${comps['midpoint']:.2f}")
    print(f"Monte Carlo median   : ${mc['median']:.2f}  (P5 ${mc['p5']:.2f} - P95 ${mc['p95']:.2f})")
    print(f"Market price (ASSUMP): ${market_price:.2f}  -> upside {summary['upside_vs_market']:+.1%}")
    print(f"Wrote: {OUT/'valuation.json'}")
    print(f"Wrote: {OUT/'monte_carlo.png'}")
    print(f"Wrote: {xlsx_path}")


def _plot_mc(samples, dcf_ps, market):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(samples, bins=60, color="#3b82f6", alpha=0.85, edgecolor="white", linewidth=0.3)
    ax.axvline(dcf_ps, color="#0f172a", linestyle="--", linewidth=1.6, label=f"DCF base ${dcf_ps:.0f}")
    ax.axvline(market, color="#ef4444", linestyle="-", linewidth=1.6, label=f"Market ${market:.0f}")
    ax.set_title("Micron (MU) — Monte Carlo fair value per share", fontsize=12, color="#0f172a")
    ax.set_xlabel("Value per share (USD)")
    ax.set_ylabel("Frequency")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "monte_carlo.png", dpi=130)
    fig.savefig(DASH / "monte_carlo.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
