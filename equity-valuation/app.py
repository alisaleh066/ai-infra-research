"""Streamlit UI for the equity valuation engine.

Launch:  app.bat   (or:  python -m streamlit run app.py)
Type any US-listed ticker -> live DCF + comps + Monte Carlo.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import value as valuemod
import analyze as analyzemod

st.set_page_config(page_title="Equity Valuation", page_icon="📈", layout="wide")
st.title("Equity Valuation — any US-listed stock")
st.caption("Audited fundamentals from SEC EDGAR + live price from Yahoo. Assumptions derived from "
           "company history; edit them in the generated Excel. Not investment advice.")

col = st.columns([1, 1, 2])
ticker = col[0].text_input("Ticker", value="MU").strip().upper()
price_override = col[1].text_input("Price override (optional)", value="")
go = col[2].button("Value it", type="primary")

if go and ticker:
    with st.spinner(f"Fetching {ticker} and building the model..."):
        try:
            po = float(price_override) if price_override else None
            s = valuemod.run(ticker, po)
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not value {ticker}: {e}")
            st.stop()

    st.subheader(f"{s['company']} ({s['ticker']}) — FY {s['fiscal_years']}")
    m = st.columns(5)
    m[0].metric("DCF / share", f"${s['dcf_value_per_share']:,.2f}")
    m[1].metric("Comps midpoint", f"${s['comps']['midpoint']:,.2f}")
    m[2].metric("WACC", f"{s['wacc']:.2%}")
    m[3].metric("Price", f"${s['price']:,.2f}" if s["price"] else "n/a")
    if s["upside_vs_price"] is not None:
        m[4].metric("Upside vs price", f"{s['upside_vs_price']:+.1%}")

    left, right = st.columns(2)
    with left:
        st.markdown("**Monte Carlo fair value** (10,000 paths)")
        st.image(f"output/{s['ticker']}_montecarlo.png")
        mc = s["monte_carlo"]
        st.write(f"Median ${mc['median']:,.2f} · P5 ${mc['p5']:,.2f} · P95 ${mc['p95']:,.2f}")
    with right:
        st.markdown("**Sensitivity — value/share (WACC × terminal growth)**")
        sens = s["sensitivity"]
        df = pd.DataFrame(
            sens["grid"],
            index=[f"{w:.1%}" for w in sens["waccs"]],
            columns=[f"{g:.1%}" for g in sens["growths"]],
        )
        st.dataframe(df.style.format("${:,.0f}").background_gradient(cmap="YlOrBr"))

    st.markdown("**Assumptions (edit in the Excel to refine)**")
    st.json(s["assumptions"], expanded=False)
    if s["data_flags"] or s["assumption_notes"]:
        st.warning("Flags: " + ", ".join(s["data_flags"] + s["assumption_notes"]))
    st.success(f"Saved Excel + JSON to output/{s['ticker']}_valuation.*")
    st.caption(s["sources"])

    # ---------- Financial-statement & quality analysis (analyze.py) ----------
    st.divider()
    st.subheader("Financial-statement & quality analysis")
    with st.spinner("Running ratios, DuPont, F-Score, Altman Z, Beneish M, Sloan, reverse DCF..."):
        rep = analyzemod.analyze(ticker)
    rw, pf, az = rep["roic_vs_wacc"], rep["piotroski"], rep["altman_z"]
    bm, sl, rd = rep["beneish_m"], rep["sloan"], rep["reverse_dcf"]
    q = st.columns(4)
    q[0].metric("ROIC vs WACC",
                f"{(rw['roic'] or 0)*100:.0f}% / {rw['wacc']*100:.0f}%",
                "creates value" if rw.get("creates_value") else "below WACC")
    q[1].metric("Piotroski F", f"{pf.get('score')}/9", pf.get("verdict", ""))
    q[2].metric("Altman Z", f"{az.get('z', 'n/a')}", az.get("zone", ""))
    q[3].metric("Beneish M", f"{bm.get('m', 'n/a')}", bm.get("flag", ""))
    q2 = st.columns(4)
    r = rep["ratios"]
    q2[0].metric("Gross margin", f"{(r['gross_margin'] or 0)*100:.0f}%")
    q2[1].metric("Net margin", f"{(r['net_margin'] or 0)*100:.0f}%")
    q2[2].metric("Accruals quality", sl.get("quality", "n/a"))
    rg = rd.get("implied_growth")
    q2[3].metric("Reverse-DCF growth", f"{rg*100:.0f}%" if rg is not None else "n/a",
                 "implied by price")
    with st.expander("Read the full research note"):
        st.markdown(Path(f"output/{rep['ticker']}_research.md").read_text(encoding="utf-8"))
    st.success(f"Saved research note + analysis to output/{rep['ticker']}_research.md / _analysis.xlsx")
