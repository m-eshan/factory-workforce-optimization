from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config import WEI_DEFAULT_WEIGHTS
from utils.anomaly_fusion import build_daily_anomaly_fusion
from utils.data_loader import daily_attendance_counts, load_all_data
from utils.export_utils import export_dataframe_excel, export_pdf_report
from utils.ml_models import route_merge_recommendations
from utils.ui_helpers import apply_global_style, manager_note, readable_chart
from utils.upload_ui import render_data_upload_panel
from utils.wei_calculator import build_wei_daily

st.set_page_config(page_title="Executive Dashboard", layout="wide")
apply_global_style()
render_data_upload_panel()
st.title("Factory Overview for Managers")
st.caption("Simple daily view of attendance, overtime, buses, canteen waste, productivity, and overall workforce health.")

data = load_all_data()
attendance = data["attendance"]
canteen = data["canteen"]
bus = data["bus"]
production = data["production"]

st.sidebar.subheader("Score Settings")
st.sidebar.caption("Adjust these only if your factory wants to give more importance to one area.")
weights = {}
for key, default in WEI_DEFAULT_WEIGHTS.items():
    labels = {"attendance": "Attendance", "ot": "Overtime control", "bus": "Bus use", "canteen": "Canteen control", "productivity": "Production"}
    weights[key] = st.sidebar.slider(labels.get(key, key.title()), 0.0, 1.0, default, 0.05)
total_weight = sum(weights.values()) or 1
weights = {key: value / total_weight for key, value in weights.items()}
wei_threshold = st.sidebar.slider("Alert if score is below", 0, 100, 60)

wei = build_wei_daily(attendance, bus, canteen, production, weights, len(data["master"]))
daily_att = daily_attendance_counts(attendance, len(data["master"]))
fusion = build_daily_anomaly_fusion(daily_att, attendance, canteen, bus)
latest_date = wei["Date"].max()
latest = wei[wei["Date"] == latest_date].iloc[0]

day_att = attendance[attendance["Date"] == latest_date]
day_canteen = canteen[canteen["Date"] == latest_date]
day_bus = bus[bus["Date"] == latest_date]

cols = st.columns(6)
cols[0].metric("Attendance", f"{latest['Attendance_Pct']:.1f}%")
cols[1].metric("People with OT", f"{(day_att['OTHours'] > 0).sum():,}")
cols[2].metric("Meal Waste", f"{day_canteen['WastePercent'].mean():.1f}%")
cols[3].metric("Bus Seat Use", f"{day_bus['Utilization_Pct'].mean():.1f}%")
cols[4].metric("Today Cost", f"Rs {(day_canteen['TotalCost'].sum() + day_bus['FuelCost_Rs'].sum()):,.0f}")
cols[5].metric("Overall Score", f"{latest['WEI']:.1f}")

if latest["WEI"] < wei_threshold:
    manager_note(f"Attention needed: overall score is {latest['WEI']:.1f}/100 on {latest_date.date()}, below your alert level.", "warn")
else:
    manager_note(f"Overall workforce health is {latest['WEI']:.1f}/100 on {latest_date.date()}. Higher is better.", "good")

component_cols = ["Attendance_Pct", "OT_Efficiency_Pct", "Bus_Utilization_Pct", "Canteen_Efficiency_Pct", "Dept_Productivity_Pct"]
component_labels = {
    "Attendance_Pct": "Attendance",
    "OT_Efficiency_Pct": "OT Control",
    "Bus_Utilization_Pct": "Bus Use",
    "Canteen_Efficiency_Pct": "Canteen Control",
    "Dept_Productivity_Pct": "Productivity",
}

st.plotly_chart(
    readable_chart(px.line(wei, x="Date", y="WEI", markers=True, title="Overall Workforce Health Score", labels={"WEI": "Score out of 100"})),
    use_container_width=True,
)
component_view = wei[["Date", *component_cols]].rename(columns=component_labels)
st.plotly_chart(
    readable_chart(px.line(component_view, x="Date", y=list(component_labels.values()), title="Which Area Is Helping or Hurting the Score")),
    use_container_width=True,
)

left, right = st.columns(2)
with left:
    st.plotly_chart(readable_chart(px.histogram(wei, x="WEI", nbins=20, title="How Often Each Score Range Occurs", labels={"WEI": "Score out of 100"})), use_container_width=True)
with right:
    weekly = wei.set_index("Date")["WEI"].resample("W").mean().reset_index().rename(columns={"WEI": "Weekly Average Score"})
    monthly = wei.set_index("Date")["WEI"].resample("ME").mean().reset_index().rename(columns={"WEI": "Monthly Average Score"})
    st.subheader("Weekly and Monthly Averages")
    st.dataframe(pd.concat({"Weekly": weekly.tail(8), "Monthly": monthly}, names=["Period"]), use_container_width=True)

st.subheader("Important Alerts")
alerts = fusion[fusion["HighPriority"]].sort_values("Date", ascending=False)
if alerts.empty:
    manager_note("No high-priority combined alerts found. Single-area unusual days are still tracked in the data.", "good")
else:
    st.dataframe(alerts.head(20), use_container_width=True)

st.subheader("AI Recommendations in Plain English")
recommendations = []
low_routes = route_merge_recommendations(bus)
if not low_routes.empty:
    route = low_routes.iloc[-1]
    recommendations.append(f"Bus route {route['Route']} has been below 50% use recently. Consider combining it with a nearby route.")
if not alerts.empty:
    alert = alerts.iloc[0]
    recommendations.append(f"Combined issue found on {pd.Timestamp(alert['Date']).date()}: {alert['ContributingModules']}. Check these areas together, not separately.")
worst_component = latest[component_cols].astype(float).idxmin()
friendly_component = component_labels.get(worst_component, worst_component)
avg_attendance = daily_att["PresentCount"].tail(7).mean()
recommendations.append(f"Lowest area today is {friendly_component}. Start there for the fastest improvement.")
recommendations.append(f"Last 7-day average attendance is {avg_attendance:.0f} people. Use this as tomorrow's staffing guide.")
recommendations.append("Meal planning should follow actual shift attendance plus a small buffer, not a fixed historical average.")
for item in recommendations:
    manager_note(item)

st.subheader("Download Overall Report")
summary_table = wei.tail(10)[["Date", "WEI", *component_cols]].rename(columns=component_labels)
report_lines = [
    f"Latest overall score: {latest['WEI']:.1f} out of 100",
    f"Latest date: {latest_date.date()}",
    f"High-priority combined alerts: {len(alerts)}",
    f"Main improvement area: {friendly_component}",
    "AI methods used: attendance forecasting, overtime forecasting, anomaly detection, bus grouping, and workforce score calculation.",
]
excel_bytes = export_dataframe_excel({"WEI_Daily": wei, "Anomaly_Fusion": fusion, "Manager_Summary": pd.DataFrame({"Recommendation": recommendations})})
pdf_bytes = export_pdf_report("Factory Executive Report", report_lines + recommendations, summary_table)
download_col1, download_col2 = st.columns(2)
download_col1.download_button("Download Full Excel Report", excel_bytes, file_name="factory_executive_report.xlsx")
download_col2.download_button("Download Manager PDF Report", pdf_bytes, file_name="factory_executive_report.pdf")
