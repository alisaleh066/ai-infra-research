"""Streamlit UI for the AI-infrastructure bottleneck map.

Launch:  app.bat   (or:  python -m streamlit run app.py)
Adjust the tightness-metric weights and see the ranking + binding constraint update live.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from scoring import METRICS, binding_constraint, score_layers

HERE = Path(__file__).resolve().parent
raw = json.loads((HERE / "layers.json").read_text(encoding="utf-8"))

st.set_page_config(page_title="AI Bottleneck Map", page_icon="🔗", layout="wide")
st.title("AI-Infrastructure Bottleneck Map")
st.caption("Each supply-chain layer scored on a transparent tightness metric. Adjust the weights "
           "to test the ranking. Metric levels are curated estimates — see layers.json provenance.")

st.sidebar.header("Tightness weights")
labels = {"utilization": "Utilisation", "lead_time": "Lead time",
          "supply_inelasticity": "Supply inelasticity", "concentration": "Concentration"}
raw_w = {m: st.sidebar.slider(labels[m], 0.0, 1.0, {
    "utilization": 0.30, "lead_time": 0.25, "supply_inelasticity": 0.25, "concentration": 0.20}[m],
    0.05) for m in METRICS}
total = sum(raw_w.values()) or 1.0
weights = {m: raw_w[m] / total for m in METRICS}  # normalise to sum 1
st.sidebar.caption(f"Normalised so weights sum to 1 (raw total {total:.2f}).")

scored = score_layers(raw["layers"], weights)
binder = binding_constraint(scored)

c = st.columns(3)
c[0].metric("Binding constraint", binder["name"])
c[1].metric("Tightness", f"{binder['tightness']:.1f} / 100")
c[2].metric("Layers", len(scored))

st.subheader("Tightness ranking")
df = pd.DataFrame([{
    "Layer": s["name"], "Lead player": s["lead_player"], "Tightness": s["tightness"],
    **{labels[m]: s["metrics"][m] for m in METRICS},
} for s in scored])
st.dataframe(
    df.style.format({"Tightness": "{:.1f}", **{labels[m]: "{:.0%}" for m in METRICS}})
      .background_gradient(cmap="YlOrBr", subset=["Tightness"]),
    use_container_width=True, hide_index=True,
)

st.subheader("Capital migration over time (share by layer — illustrative)")
cf = raw["capital_flow"]
names = {l["id"]: l["name"] for l in raw["layers"]}
shares = {}
for i in range(len(cf["years"])):
    tot = sum(cf["series"][lid][i] for lid in cf["series"])
    for lid in cf["series"]:
        shares.setdefault(names[lid], []).append(cf["series"][lid][i] / tot)
area = pd.DataFrame(shares, index=cf["years"])
st.area_chart(area)
st.caption(raw["provenance"])
