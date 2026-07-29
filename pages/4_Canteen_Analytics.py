from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.canteen_prediction_chain import attendance_consumption_correlation, baseline_preparation, compute_waste_comparison, model_based_preparation
from utils.data_loader import load_all_data
from utils.ml_models import isolation_scores, train_canteen_forecast
from utils.ui_helpers import apply_global_style, readable_chart
from utils.upload_ui import render_data_upload_panel

st.set_page_config(page_title="Canteen Analytics", layout="wide")
apply_global_style()
render_data_upload_panel()
st.title("Canteen: Meals Prepared, Used, and Wasted")

data = load_all_data()
canteen = data["canteen"]
model = train_canteen_forecast(canteen)
baseline = baseline_preparation(canteen)
proposed = model_based_preparation(canteen, model)
comparison = compute_waste_comparison(canteen, baseline, proposed)
corr, p_value = attendance_consumption_correlation(canteen)
scored = isolation_scores(canteen.groupby("Date", as_index=False)["WastePercent"].mean(), "WastePercent")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Waste", f"{canteen['WastePercent'].mean():.1f}%")
col2.metric("Monthly Wastage Cost", f"Rs {canteen['WastageCost'].sum() / 6:,.0f}")
col3.metric("Attendance-Meal Link", f"{corr:.3f}")
col4.metric("p-value", f"{p_value:.2e}")

st.plotly_chart(readable_chart(px.line(canteen, x="Date", y="WastePercent", color="Shift", title="Waste % Trend by Shift", labels={"WastePercent": "Waste %"})), use_container_width=True)

st.subheader("Baseline (Historical Average) vs Proposed (Attendance-Driven Prediction)")
st.dataframe(comparison, use_container_width=True)
chart = comparison.melt(id_vars="Metric", value_vars=["Baseline", "Proposed"], var_name="Scenario", value_name="Waste %")
st.plotly_chart(readable_chart(px.bar(chart, x="Scenario", y="Waste %", color="Scenario", title="Food Waste Comparison")), use_container_width=True)

fig = px.line(scored, x="Date", y="WastePercent", title="Canteen Waste Anomalies")
fig.add_scatter(x=scored.loc[scored["IsAnomaly"], "Date"], y=scored.loc[scored["IsAnomaly"], "WastePercent"], mode="markers", name="Anomaly")
st.plotly_chart(readable_chart(fig), use_container_width=True)

latest = canteen.tail(3).copy()
latest["RecommendedPreparation"] = proposed.tail(3).round().astype(int).values
st.subheader("RF Demand Forecast Recommendation")
st.dataframe(latest[["Date", "Shift", "Attendees", "MealsConsumed", "RecommendedPreparation"]], use_container_width=True)



