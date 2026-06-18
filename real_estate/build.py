"""build.py — Project 3 entry point: UK underwriting + ROI simulator export + Excel model.

Run:  python real_estate/build.py
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "real_estate"))
sys.path.insert(0, str(ROOT / "skills" / "uk-property-data"))

from re_engine import (  # noqa: E402
    Deal, DriverBaselines, SimulatorCoefficients, sensitivity_grid, simulate, underwrite,
)
from uk_data import load_uk_dataset  # noqa: E402
import build_xlsx  # noqa: E402

OUT = ROOT / "real_estate" / "output"
DASH = ROOT / "dashboard" / "public" / "data"

# Representative deal: a small North West multi-unit residential block (higher-yield region).
BASE_DEAL = Deal(
    units_monthly_rent=[950, 950, 950, 950, 900, 900],   # 6 units (GBP/month)
    vacancy_rate=0.05,
    opex_ratio=0.25,
    entry_cap_rate=0.060,
    exit_cap_rate=0.060,
    rent_growth=0.030,
    ltv=0.65,
    interest_rate=0.0575,                                  # base case (overridden by simulator)
    purchase_costs_pct=0.05,
    selling_costs_pct=0.015,
    hold_years=5,
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DASH.mkdir(parents=True, exist_ok=True)
    uk = load_uk_dataset()

    base = underwrite(BASE_DEAL)

    # Two-way sensitivity: exit cap (rows) x rent growth (cols)
    exit_caps = [0.050, 0.055, 0.060, 0.065, 0.070]
    rent_growths = [0.010, 0.020, 0.030, 0.040, 0.050]
    grid = sensitivity_grid(BASE_DEAL, exit_caps, rent_growths)

    # ROI simulator: default drivers from the latest UK data snapshot
    macro = uk["macro"]
    default_drivers = {
        "net_migration": macro["net_migration"][-1]["value"],
        "household_formation": macro["net_additional_households_per_yr"]["value"],
        "completions": macro["net_additional_dwellings_england"][-1]["value"],
        "employment_rate": macro["employment_rate_pct"]["value"],
        "bank_rate_pct": macro["bank_rate_pct"][-1]["value"],
    }
    baselines = DriverBaselines()
    coeffs = SimulatorCoefficients()
    sim_default = simulate(BASE_DEAL, default_drivers, baselines, coeffs)

    # Driver slider ranges for the dashboard
    driver_ranges = {
        "net_migration": {"min": 0, "max": 900000, "step": 10000, "unit": "people/yr",
                          "label": "Net migration"},
        "household_formation": {"min": 80000, "max": 300000, "step": 5000, "unit": "hh/yr",
                                "label": "Household formation"},
        "completions": {"min": 120000, "max": 400000, "step": 5000, "unit": "dwellings/yr",
                        "label": "Housing completions (supply)"},
        "employment_rate": {"min": 68, "max": 80, "step": 0.1, "unit": "%",
                            "label": "Employment rate"},
        "bank_rate_pct": {"min": 0.5, "max": 8, "step": 0.25, "unit": "%",
                          "label": "Bank Rate"},
    }

    summary = {
        "deal": {
            "region": "North West (illustrative 6-unit block)",
            "units": len(BASE_DEAL.units_monthly_rent),
            "gross_rent_pa": sum(BASE_DEAL.units_monthly_rent) * 12,
            **{k: getattr(BASE_DEAL, k) for k in
               ("vacancy_rate", "opex_ratio", "entry_cap_rate", "ltv",
                "purchase_costs_pct", "selling_costs_pct", "hold_years")},
        },
        "base_case": {
            "noi": base["noi"], "valuation": base["valuation"], "loan": base["loan"],
            "equity": base["equity"], "dscr": base["dscr"], "irr": base["irr"],
            "equity_multiple": base["equity_multiple"], "cash_flows": base["cash_flows"],
        },
        "sensitivity": {"exit_caps": exit_caps, "rent_growths": rent_growths, "grid": grid},
        "simulator": {
            "baselines": asdict(baselines),
            "coefficients": {k: v for k, v in asdict(coeffs).items() if k != "results"},
            "default_drivers": default_drivers,
            "driver_ranges": driver_ranges,
            "default_result": {k: sim_default[k] for k in
                               ("irr", "equity_multiple", "dscr", "implied_rent_growth",
                                "implied_exit_cap", "implied_debt_rate", "demand_pressure")},
            "data_vintage": uk["vintage"],
        },
        "notes": "Underwriting is assumption-driven and transparent. The simulator maps observable "
                 "demand/supply drivers to rent growth/exit cap via explicit elasticities — "
                 "immigration is one visible driver, never a hidden signal. UK data: Land Registry + ONS.",
    }

    for d in (OUT, DASH):
        (d / "real_estate.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    xlsx_path = build_xlsx.build(BASE_DEAL, base, exit_caps, rent_growths, grid)

    print(f"NOI                : £{base['noi']:,.0f}")
    print(f"Valuation (cap)    : £{base['valuation']:,.0f}")
    print(f"Equity in          : £{base['equity']:,.0f}")
    print(f"DSCR               : {base['dscr']:.2f}x")
    print(f"Base IRR           : {base['irr']:.2%}")
    print(f"Equity multiple    : {base['equity_multiple']:.2f}x")
    print(f"Simulator default IRR (UK data drivers): {sim_default['irr']:.2%} "
          f"(rent growth {sim_default['implied_rent_growth']:.2%}, "
          f"exit cap {sim_default['implied_exit_cap']:.2%})")
    print(f"Wrote: {OUT/'real_estate.json'}")
    print(f"Wrote: {xlsx_path}")


if __name__ == "__main__":
    main()
