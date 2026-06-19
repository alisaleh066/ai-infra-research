"""Tests for the analysis/score library (no network). Run: python -m pytest -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import analysis as an  # noqa: E402


def fund(**series) -> dict:
    """Build a 2-year fundamentals dict. Pass concept=(fy2023, fy2024)."""
    f = {"ticker": "T", "name": "T", "years": [2023, 2024], "missing_flags": []}
    for k, (a, b) in series.items():
        f[k] = {2023: a, 2024: b}
    return f


# ---------------------------------------------------------------- ratios / DuPont
def test_ratios_basic():
    f = fund(revenue=(900, 1000), gross_profit=(360, 400), operating_income=(180, 200),
             net_income=(90, 100), total_assets=(1900, 2000), equity=(900, 1000))
    r = an.ratios(f)
    assert r["gross_margin"] == pytest.approx(0.40)
    assert r["operating_margin"] == pytest.approx(0.20)
    assert r["net_margin"] == pytest.approx(0.10)
    assert r["roe"] == pytest.approx(0.10)


def test_dupont_identity_equals_roe():
    f = fund(revenue=(900, 1000), net_income=(90, 100), total_assets=(1900, 2000), equity=(900, 1000))
    d = an.dupont(f)
    assert d["roe"] == pytest.approx(d["net_margin"] * d["asset_turnover"] * d["equity_multiplier"])
    assert d["roe"] == pytest.approx(100 / 1000)


# ---------------------------------------------------------------- ROIC vs WACC
def test_roic_vs_wacc_value_creation():
    f = fund(operating_income=(900, 1000), long_term_debt=(2000, 2000),
             short_term_debt=(0, 0), equity=(3000, 3000), cash=(500, 500))
    out = an.roic_vs_wacc(f, wacc=0.10, tax_rate=0.21)
    assert out["roic"] == pytest.approx(1000 * 0.79 / (2000 + 3000 - 500))
    assert out["creates_value"] is True
    assert out["value_spread"] == pytest.approx(out["roic"] - 0.10)


# ---------------------------------------------------------------- Piotroski
def test_piotroski_strong_vs_weak():
    strong = fund(net_income=(50, 120), cfo=(60, 200), total_assets=(1000, 1000),
                  long_term_debt=(300, 200), current_assets=(400, 600),
                  current_liabilities=(300, 300), shares=(100, 100),
                  gross_profit=(300, 450), revenue=(800, 1000))
    weak = fund(net_income=(120, -20), cfo=(100, -30), total_assets=(1000, 1100),
                long_term_debt=(200, 400), current_assets=(600, 400),
                current_liabilities=(300, 400), shares=(100, 120),
                gross_profit=(450, 300), revenue=(1000, 900))
    assert an.piotroski_f(strong)["score"] > an.piotroski_f(weak)["score"]
    assert 0 <= an.piotroski_f(strong)["score"] <= 9


def test_piotroski_needs_two_years():
    one = {"ticker": "T", "name": "T", "years": [2024], "missing_flags": [],
           "net_income": {2024: 1}}
    assert an.piotroski_f(one)["score"] is None


# ---------------------------------------------------------------- Altman Z
def test_altman_safe_and_distress_zones():
    safe = fund(total_assets=(1000, 1000), total_liabilities=(400, 400),
                current_assets=(500, 500), current_liabilities=(200, 200),
                retained_earnings=(400, 400), operating_income=(200, 200), revenue=(1200, 1200))
    distress = fund(total_assets=(1000, 1000), total_liabilities=(900, 900),
                    current_assets=(100, 100), current_liabilities=(300, 300),
                    retained_earnings=(-300, -300), operating_income=(-50, -50), revenue=(300, 300))
    assert an.altman_z(safe, market_cap=2000)["zone"] == "safe"
    assert an.altman_z(distress, market_cap=50)["zone"] == "distress"
    assert an.altman_z(safe, market_cap=None)["z"] is None


# ---------------------------------------------------------------- Beneish
def test_beneish_returns_score_and_flags_fraud_pattern():
    stable = fund(receivables=(100, 102), revenue=(1000, 1010), gross_profit=(400, 404),
                  current_assets=(500, 505), ppe_net=(300, 303), total_assets=(1000, 1010),
                  da=(50, 50), sga=(100, 101), total_liabilities=(400, 404),
                  net_income=(100, 101), cfo=(110, 111))
    fraud = fund(receivables=(100, 260), revenue=(1000, 1400), gross_profit=(400, 380),
                 current_assets=(500, 520), ppe_net=(300, 300), total_assets=(1000, 1500),
                 da=(50, 40), sga=(100, 95), total_liabilities=(400, 800),
                 net_income=(100, 260), cfo=(110, 90))
    m_stable = an.beneish_m(stable)["m"]
    m_fraud = an.beneish_m(fraud)["m"]
    assert m_stable is not None and m_fraud is not None
    assert m_fraud > m_stable                       # fraud pattern scores higher (worse)


# ---------------------------------------------------------------- Sloan
def test_sloan_quality_buckets():
    assert an.sloan_accruals(fund(net_income=(0, 200), cfo=(0, 50),
                                  total_assets=(0, 1000)))["quality"] == "low"   # 0.15
    assert an.sloan_accruals(fund(net_income=(0, 50), cfo=(0, 100),
                                  total_assets=(0, 1000)))["quality"] == "high"  # -0.05


# ---------------------------------------------------------------- Reverse DCF
def test_reverse_dcf_solves_and_is_monotonic_in_price():
    f = fund(revenue=(900, 1000), operating_income=(180, 200), da=(50, 60), capex=(60, 70),
             shares=(100, 100), long_term_debt=(200, 200), short_term_debt=(0, 0), cash=(50, 50))
    low = an.reverse_dcf(f, price=20.0, wacc=0.10)["implied_growth"]
    high = an.reverse_dcf(f, price=40.0, wacc=0.10)["implied_growth"]
    assert low is not None and high is not None
    assert high > low                               # a higher price implies higher expected growth


def test_reverse_dcf_no_price():
    assert an.reverse_dcf(fund(revenue=(1, 1)), price=None, wacc=0.10)["implied_growth"] is None
