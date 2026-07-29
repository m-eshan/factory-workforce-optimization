from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config import BUS_ROUTES
from utils.data_loader import load_all_data
from utils.ml_models import adaptive_bus_recommendation, cluster_bus_stops, nearest_location, route_merge_recommendations, shortest_route
from utils.ui_helpers import apply_global_style, manager_note, readable_chart
from utils.upload_ui import render_data_upload_panel

st.set_page_config(page_title="Smart Bus Management", layout="wide")
apply_global_style()
render_data_upload_panel()
st.title("Bus Planning: Seats, Routes, and Fuel")
st.caption("Use this page to see which buses are full, which routes are costly, and how AI can group stops based on employees present today.")

data = load_all_data()
bus = data["bus"]
attendance = data["attendance"]
coords = data["coordinates"]
master = data["master"]

mode = st.radio("Planning mode", ["Manual", "AI-Suggested (All Employees)", "AI-Adaptive (Only Employees Present Today)"], horizontal=True)
selected_date = st.date_input("Date to plan", attendance["Date"].max().date())
selected_ts = pd.Timestamp(selected_date)
selected_bus = bus[bus["Date"] == selected_ts]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average Seat Use", f"{selected_bus['Utilization_Pct'].mean():.1f}%")
col2.metric("Fuel Cost Today", f"Rs {selected_bus['FuelCost_Rs'].sum():,.0f}")
col3.metric("Active Routes", selected_bus["Route"].nunique())
col4.metric("Employees Present", attendance[attendance["Date"] == selected_ts]["EmployeeID"].nunique())

st.plotly_chart(
    readable_chart(px.bar(selected_bus, x="Route", y=["Occupancy", "Capacity"], barmode="group", title="Seats Used vs Seats Available", labels={"value": "People / Seats", "variable": "Measure"})),
    use_container_width=True,
)
st.plotly_chart(
    readable_chart(px.line(bus.groupby("Date", as_index=False)["FuelCost_Rs"].sum(), x="Date", y="FuelCost_Rs", title="Daily Fuel Cost", labels={"FuelCost_Rs": "Fuel Cost Rs"})),
    use_container_width=True,
)

employee_locations = master.merge(coords, on="Location", how="left")
route_capacity = int(pd.DataFrame(BUS_ROUTES)["Capacity"].median())
if mode == "AI-Suggested (All Employees)":
    planning_locations = employee_locations
    cluster = cluster_bus_stops(planning_locations, len(BUS_ROUTES))
    manager_note("AI is grouping all registered employee home locations. This is useful for long-term route design.")
elif mode == "AI-Adaptive (Only Employees Present Today)":
    present_ids = attendance[attendance["Date"] == selected_ts]["EmployeeID"].unique()
    planning_locations = employee_locations[employee_locations["EmployeeID"].isin(present_ids)]
    cluster = adaptive_bus_recommendation(planning_locations, capacity=route_capacity, n_clusters=len(BUS_ROUTES))
    manager_note("AI is grouping only employees who are present today. This helps reduce buses on low-attendance days.")
else:
    planning_locations = employee_locations
    cluster = {"centers": pd.DataFrame(), "silhouette": 0, "inertia": [], "recommended_buses": len(BUS_ROUTES), "merge_count": 0}
    manager_note("Manual mode shows current fixed routes from the data. Choose an AI mode to see route grouping recommendations.")

map_points = coords.copy()
st.plotly_chart(
    readable_chart(px.scatter_mapbox(map_points, lat="Latitude", lon="Longitude", hover_name="Location", zoom=8, height=460, title="Bus Stops and Factory Location").update_layout(mapbox_style="open-street-map"), 460),
    use_container_width=True,
)

if not cluster["centers"].empty:
    centers = cluster["centers"].copy()
    centers["NearestStop"] = centers.apply(lambda r: nearest_location(r["Latitude"], r["Longitude"], coords), axis=1)
    recommended_buses = int(cluster.get("recommended_buses", len(centers)))
    route = shortest_route(centers["NearestStop"].tolist(), coords)
    fixed_cost = selected_bus["FuelCost_Rs"].sum()
    adaptive_cost = fixed_cost * recommended_buses / max(len(BUS_ROUTES), 1)
    savings = fixed_cost - adaptive_cost

    ai1, ai2, ai3, ai4 = st.columns(4)
    ai1.metric("Route Grouping Quality", f"{cluster['silhouette']:.2f}")
    ai2.metric("Recommended Buses", recommended_buses)
    ai3.metric("Possible Fuel Saving", f"Rs {savings:,.0f}")
    ai4.metric("Suggested Distance", f"{route['distance_km']:.1f} km")

    if recommended_buses < len(BUS_ROUTES):
        manager_note(f"AI suggests using {recommended_buses} buses instead of {len(BUS_ROUTES)} for this day because some groups are small.", "warn")
    else:
        manager_note("AI does not recommend reducing buses for this day. Current demand appears strong enough.", "good")

    display_centers = centers[["Cluster", "PointCount", "NearestStop", "Latitude", "Longitude"]].rename(columns={"PointCount": "Employees in Group", "NearestStop": "Closest Stop"})
    st.dataframe(display_centers, use_container_width=True)
    st.plotly_chart(readable_chart(px.line(pd.DataFrame(cluster["inertia"]), x="k", y="inertia", markers=True, title="AI Check: Best Number of Route Groups", labels={"k": "Number of Groups", "inertia": "Grouping Error"})), use_container_width=True)
    manager_note(f"Suggested stop order: {' -> '.join(route['path'])}. Estimated fuel cost: Rs {route['fuel_cost_rs']:.0f}.")
else:
    fixed_cost = selected_bus["FuelCost_Rs"].sum()
    adaptive_cost = fixed_cost

comparison = pd.DataFrame([
    {"Plan": "Current fixed routing", "FuelCost_Rs": fixed_cost},
    {"Plan": "AI adaptive routing", "FuelCost_Rs": adaptive_cost},
])
st.plotly_chart(readable_chart(px.bar(comparison, x="Plan", y="FuelCost_Rs", title="Current vs AI Fuel Cost", labels={"FuelCost_Rs": "Fuel Cost Rs"})), use_container_width=True)

st.subheader("Routes That May Need Merging")
merge_df = route_merge_recommendations(bus).tail(25)
if merge_df.empty:
    manager_note("No route has stayed below 50% use long enough to recommend merging.", "good")
else:
    st.dataframe(merge_df.rename(columns={"Trailing30Util": "30-day Seat Use %"}), use_container_width=True)
