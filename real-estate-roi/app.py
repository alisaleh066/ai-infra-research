"""Streamlit UI for the institutional real-estate ROI / waterfall model.

Launch:  app.bat   (or:  python -m streamlit run app.py)
Move the sliders -> project & LP/GP returns and the promote update live.
"""
from __future__ import annotations

import dataclasses

import pandas as pd
import streamlit as st

from underwrite import Deal, equity_cash_flows, underwrite
from waterfall import WaterfallTiers, run_waterfall

st.set_page_config(page_title="RE ROI / Waterfall", page_icon="🏢", layout="wide")
st.title("Real-Estate ROI — institutional waterfall")
st.caption("Value-add underwriting + LP/GP equity waterfall (return of capital → preferred return "
           "→ promote tiers). Every input is visible. Not investment advice.")

s = st.sidebar
s.header("Deal inputs")
price = s.number_input("Purchase price", 1_000_000, 500_000_000, 10_000_000, 500_000)
noi = s.number_input("In-place NOI", 10_000, 50_000_000, 600_000, 10_000)
going_in = s.slider("Going-in cap", 0.03, 0.10, 0.06, 0.0025)
exit_cap = s.slider("Exit cap", 0.03, 0.10, 0.0575, 0.0025)
uplift = s.slider("NOI uplift (value-add)", 0.0, 0.8, 0.30, 0.05)
stab_yrs = s.slider("Stabilize years", 1, 5, 2, 1)
growth = s.slider("Post-stabilize NOI growth", 0.0, 0.06, 0.03, 0.005)
reno = s.number_input("Renovation capex", 0, 100_000_000, 1_500_000, 100_000)
ltv = s.slider("LTV", 0.0, 0.85, 0.65, 0.05)
rate = s.slider("Interest rate (IO)", 0.02, 0.12, 0.065, 0.0025)
hold = s.slider("Hold (years)", 3, 10, 5, 1)
s.header("Waterfall")
pref = s.slider("Preferred return (hurdle 1)", 0.04, 0.12, 0.08, 0.005)
promote = s.slider("Promote above pref", 0.0, 0.5, 0.20, 0.05)

d = Deal(purchase_price=price, in_place_noi=noi, going_in_cap=going_in, exit_cap=exit_cap,
         hold_years=hold, noi_uplift_pct=uplift, stabilize_years=stab_yrs,
         post_stabilize_growth=growth, renovation_capex=reno, ltv=ltv, interest_rate=rate)
tiers = WaterfallTiers([(pref, promote), (pref + 0.04, promote + 0.10), (pref + 0.07, promote + 0.20)])

u = underwrite(d)
w = run_waterfall(u["cash_flows"], tiers)

c = st.columns(4)
c[0].metric("Project IRR", f"{u['project_irr']:.1%}")
c[1].metric("LP IRR", f"{w['lp_irr']:.1%}", f"{-w['promote_drag']:.1%} promote drag")
c[2].metric("Equity multiple", f"{u['equity_multiple']:.2f}x")
c[3].metric("Min DSCR", f"{u['min_dscr']:.2f}x")

c2 = st.columns(4)
c2[0].metric("Equity invested", f"{u['equity']:,.0f}")
c2[1].metric("Debt yield", f"{u['debt_yield']:.1%}")
c2[2].metric("GP promote", f"{w['gp_promote']:,.0f}")
c2[3].metric("GP share of profit", f"{w['gp_share_of_profit']:.1%}")

left, right = st.columns(2)
with left:
    st.markdown("**Cash flows (equity / LP / GP)**")
    df = pd.DataFrame({
        "Year": list(range(hold + 1)),
        "Equity CF": [round(x) for x in u["cash_flows"]],
        "LP": [round(x) for x in w["lp_cash_flows"]],
        "GP promote": [round(x) for x in w["gp_cash_flows"]],
    }).set_index("Year")
    st.dataframe(df.style.format("{:,.0f}"), use_container_width=True)
with right:
    st.markdown("**LP IRR — exit cap × NOI uplift**")
    caps = [round(exit_cap + x, 4) for x in (-0.0075, -0.0025, 0, 0.0025, 0.0075)]
    ups = [0.10, 0.20, 0.30, 0.40, 0.50]
    grid = [[run_waterfall(equity_cash_flows(dataclasses.replace(d, exit_cap=ec, noi_uplift_pct=up)), tiers)["lp_irr"]
             for up in ups] for ec in caps]
    gdf = pd.DataFrame(grid, index=[f"{c:.2%}" for c in caps], columns=[f"{u_:.0%}" for u_ in ups])
    st.dataframe(gdf.style.format("{:.1%}").background_gradient(cmap="YlOrBr"), use_container_width=True)

# downside stress
stress = dataclasses.replace(d, exit_cap=exit_cap + 0.0075, noi_uplift_pct=max(uplift - 0.15, 0),
                             interest_rate=rate + 0.015)
su = underwrite(stress)
st.warning(f"Downside stress (exit cap +0.75pp, uplift −15pp, rate +1.5pp): "
           f"project IRR {su['project_irr']:.1%}, equity multiple {su['equity_multiple']:.2f}x, "
           f"min DSCR {su['min_dscr']:.2f}x.")
