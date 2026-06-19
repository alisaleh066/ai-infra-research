"""Engine tests for the DCF/WACC/sensitivity/comps/Monte Carlo. Run: python -m pytest -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from valuation import (  # noqa: E402
    DCFAssumptions, MonteCarloSpec, comps_valuation, cost_of_equity, enterprise_value,
    monte_carlo, project_fcff, sensitivity_grid, terminal_value, value_per_share, wacc,
)


def base(**over) -> DCFAssumptions:
    d = dict(
        base_revenue=1000.0, rev_growth=[0.10, 0.08, 0.06, 0.05, 0.04],
        ebit_margin=[0.30] * 5, tax_rate=0.20, da_pct_rev=0.10, capex_pct_rev=0.10,
        nwc_pct_rev_change=0.05, terminal_growth=0.025, risk_free=0.04, erp=0.05,
        beta=1.0, pretax_kd=0.05, equity_value=9000.0, debt_value=1000.0, cash=200.0, shares=100.0,
    )
    d.update(over)
    return DCFAssumptions(**d)


def test_capm():
    assert cost_of_equity(0.04, 1.0, 0.05) == pytest.approx(0.09)


def test_wacc():
    assert wacc(base()) == pytest.approx(0.085, abs=1e-9)


def test_wacc_requires_capital():
    with pytest.raises(ValueError):
        wacc(base(equity_value=0.0, debt_value=0.0))


def test_fcff_first_year():
    rows = project_fcff(base())
    rev1 = 1100.0
    assert rows[0]["fcff"] == pytest.approx(rev1 * 0.30 * 0.8 + rev1 * 0.10 - rev1 * 0.10 - 100 * 0.05)
    assert len(rows) == 5


def test_horizon_mismatch():
    with pytest.raises(ValueError):
        base(rev_growth=[0.1, 0.1], ebit_margin=[0.3])


def test_terminal_value():
    assert terminal_value(100.0, 0.10, 0.02) == pytest.approx(100 * 1.02 / 0.08)
    with pytest.raises(ValueError):
        terminal_value(100, 0.02, 0.02)


def test_dcf_bridge():
    a = base(); r = enterprise_value(a)
    assert r["equity_value"] == pytest.approx(r["enterprise_value"] - a.debt_value + a.cash)
    assert r["value_per_share"] == pytest.approx(r["equity_value"] / a.shares)
    assert 0 < r["tv_pct_of_ev"] < 1


def test_monotonic_wacc_and_growth():
    a = base()
    assert value_per_share(a, wacc_rate=0.08) > value_per_share(a, wacc_rate=0.12)
    assert value_per_share(a, terminal_growth=0.03) > value_per_share(a, terminal_growth=0.01)


def test_sensitivity_shape():
    grid = sensitivity_grid(base(), [0.08, 0.09, 0.10], [0.01, 0.02, 0.03])
    for row in grid:
        assert row[0] < row[1] < row[2]
    for j in range(3):
        assert grid[0][j] > grid[1][j] > grid[2][j]


def test_comps():
    r = comps_valuation(1000, 5.0, 500, 100, 8.0, 12.0)
    assert r["value_per_share_ev_ebitda"] == pytest.approx(75.0)
    assert r["value_per_share_pe"] == pytest.approx(60.0)
    assert r["midpoint"] == pytest.approx(67.5)


def test_monte_carlo_reproducible():
    a = base()
    r1 = monte_carlo(a, MonteCarloSpec(n=2000, seed=7))
    r2 = monte_carlo(a, MonteCarloSpec(n=2000, seed=7))
    assert r1["median"] == pytest.approx(r2["median"])
    assert r1["p5"] < r1["median"] < r1["p95"]
