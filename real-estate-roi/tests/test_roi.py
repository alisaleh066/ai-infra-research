"""Tests for underwriting + the LP/GP waterfall. Run: python -m pytest -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from underwrite import Deal, equity_cash_flows, irr, npv, underwrite  # noqa: E402
from waterfall import run_waterfall  # noqa: E402


def deal(**over) -> Deal:
    d = dict(purchase_price=10_000_000, in_place_noi=600_000, going_in_cap=0.06,
             exit_cap=0.06, hold_years=5, noi_uplift_pct=0.25, stabilize_years=2,
             post_stabilize_growth=0.03, renovation_capex=1_000_000,
             acquisition_costs_pct=0.02, selling_costs_pct=0.015, ltv=0.65, interest_rate=0.06)
    d.update(over)
    return Deal(**d)


# ----------------------------------------------------------------- IRR / NPV
def test_irr_known():
    assert irr([-100, 110]) == pytest.approx(0.10, abs=1e-6)


def test_npv_zero_at_irr():
    cfs = [-100, 30, 30, 30, 30, 30]
    assert npv(irr(cfs), cfs) == pytest.approx(0.0, abs=1e-6)


# ----------------------------------------------------------------- Underwriting
def test_noi_ramp_and_stabilize():
    d = deal()
    assert d.noi_at(1) == pytest.approx(600_000 + (750_000 - 600_000) * 0.5)
    assert d.noi_at(2) == pytest.approx(750_000)                       # stabilized
    assert d.noi_at(3) == pytest.approx(750_000 * 1.03)               # +growth


def test_debt_metrics():
    d = deal()
    u = underwrite(d)
    assert u["loan"] == pytest.approx(0.65 * 10_000_000)
    assert u["ltc"] == pytest.approx(u["loan"] / (10_000_000 * 1.02 + 1_000_000))
    assert u["debt_yield"] == pytest.approx(600_000 / (0.65 * 10_000_000))
    assert u["equity"] == pytest.approx(10_000_000 * 1.02 + 1_000_000 - 0.65 * 10_000_000)


def test_project_returns_positive_for_good_deal():
    u = underwrite(deal())
    assert u["project_irr"] > 0
    assert u["equity_multiple"] > 1
    assert len(u["cash_flows"]) == 6


def test_higher_exit_cap_lowers_irr():
    assert underwrite(deal(exit_cap=0.07))["project_irr"] < underwrite(deal(exit_cap=0.055))["project_irr"]


# ----------------------------------------------------------------- Waterfall
def test_waterfall_conservation_per_period():
    cfs = equity_cash_flows(deal())
    w = run_waterfall(cfs)
    for t in range(len(cfs)):
        assert w["lp_cash_flows"][t] + w["gp_cash_flows"][t] == pytest.approx(cfs[t], abs=1e-6)


def test_waterfall_total_conservation():
    cfs = equity_cash_flows(deal())
    w = run_waterfall(cfs)
    assert sum(w["lp_cash_flows"]) + sum(w["gp_cash_flows"]) == pytest.approx(sum(cfs), abs=1e-6)


def test_no_promote_when_return_below_pref():
    # weak deal returning under the 8% pref -> GP promote must be ~0
    cfs = [-1_000_000, 30_000, 30_000, 30_000, 30_000, 1_050_000]  # ~5% IRR
    w = run_waterfall(cfs)
    assert w["project_irr"] < 0.08
    assert w["gp_promote"] == pytest.approx(0.0, abs=1.0)


def test_promote_positive_and_lp_irr_below_project_when_strong():
    cfs = [-1_000_000, 80_000, 80_000, 80_000, 80_000, 2_200_000]  # strong, well above hurdles
    w = run_waterfall(cfs)
    assert w["gp_promote"] > 0
    assert w["lp_irr"] < w["project_irr"]            # promote drag
    assert w["promote_drag"] > 0


def test_higher_return_raises_gp_share():
    weak = run_waterfall([-1_000_000, 50_000, 50_000, 50_000, 50_000, 1_300_000])
    strong = run_waterfall([-1_000_000, 90_000, 90_000, 90_000, 90_000, 2_600_000])
    assert strong["gp_share_of_profit"] > weak["gp_share_of_profit"]


def test_lp_achieving_exactly_pref_gets_no_promote():
    # craft cash flows that yield exactly 8% IRR -> all in band 0, GP = 0
    cfs = [-1_000_000.0]
    bal = 1_000_000.0
    for _ in range(5):
        bal *= 1.08
    cfs += [0, 0, 0, 0, bal]
    w = run_waterfall(cfs)
    assert w["project_irr"] == pytest.approx(0.08, abs=1e-4)
    assert w["gp_promote"] == pytest.approx(0.0, abs=1.0)
    assert w["lp_irr"] == pytest.approx(0.08, abs=1e-4)
