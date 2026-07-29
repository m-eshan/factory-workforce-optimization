from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.data_loader import detect_absences, load_all_data
from utils.ui_helpers import apply_global_style, readable_chart
from utils.upload_ui import render_data_upload_panel

st.set_page_config(page_title="Department Productivity", layout="wide")
apply_global_style()
render_data_upload_panel()
st.title("Department Output and Staffing")

data = load_all_data()
attendance = data["attendance"]
production = data["production"]
absences = detect_absences(data["attendance_raw"], data["master"])

present_dept = attendance.groupby(["Date", "Department"], as_index=False)["EmployeeID"].nunique().rename(columns={"EmployeeID": "PresentEmployees"})
prod = production.merge(present_dept, on=["Date", "Department"], how="left")
prod["ProductivityIndex"] = prod["ProductionUnits"] / prod["PresentEmployees"].clip(lower=1)

col1, col2, col3 = st.columns(3)
col1.metric("Avg Productivity Index", f"{prod['ProductivityIndex'].mean():.1f}")
col2.metric("Total Production Units", f"{prod['ProductionUnits'].sum():,}")
col3.metric("Absence Records", f"{len(absences):,}")

left, right = st.columns(2)
with left:
    workforce = attendance.groupby(["Department", "Shift"], as_index=False)["EmployeeID"].nunique()
    st.plotly_chart(readable_chart(px.bar(workforce, x="Department", y="EmployeeID", color="Shift", barmode="group", title="Workforce Distribution", labels={"EmployeeID": "Employees"})), use_container_width=True)
with right:
    absentee = absences.groupby("Department", as_index=False)["EmployeeID"].count()
    st.plotly_chart(readable_chart(px.bar(absentee, x="Department", y="EmployeeID", title="Absentee Count by Department", labels={"EmployeeID": "Absence Records"})), use_container_width=True)

st.plotly_chart(readable_chart(px.line(prod, x="Date", y="ProductivityIndex", color="Department", title="Productivity Index Trend", labels={"ProductivityIndex": "Units per Present Employee"})), use_container_width=True)
ot = attendance.groupby(["Department", "Shift"], as_index=False)["OTHours"].sum()
st.plotly_chart(readable_chart(px.bar(ot, x="Department", y="OTHours", color="Shift", barmode="group", title="Overtime Distribution by Department", labels={"OTHours": "Overtime Hours"})), use_container_width=True)



