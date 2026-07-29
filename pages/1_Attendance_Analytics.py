from __future__ import annotations

import plotly.express as px
import streamlit as st

from utils.data_loader import daily_attendance_counts, detect_absences, load_all_data
from utils.ml_models import isolation_scores, train_attendance_forecast
from utils.ui_helpers import apply_global_style, manager_note, readable_chart
from utils.upload_ui import render_data_upload_panel

st.set_page_config(page_title="Attendance Analytics", layout="wide")
apply_global_style()
render_data_upload_panel()
st.title("Attendance: Who Came to Work?")
st.caption("This page shows daily attendance, unusual low-attendance days, and absent employees found from missing punch records.")

data = load_all_data()
attendance = data["attendance"]
daily = daily_attendance_counts(attendance, len(data["master"]))
forecast = train_attendance_forecast(daily)
daily_scored = isolation_scores(daily, "PresentCount")
absences = detect_absences(data["attendance_raw"], data["master"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Average Attendance", f"{daily['Attendance_Pct'].mean():.1f}%")
col2.metric("People Present per Day", f"{daily['PresentCount'].mean():.0f}")
col3.metric("Forecast Error", f"{forecast['mae']:.1f} people")
col4.metric("Unusual Days", int(daily_scored["IsAnomaly"].sum()))

if daily_scored["IsAnomaly"].sum() > 0:
    manager_note("The marked dots are days where attendance was unusual compared with the normal pattern.", "warn")
else:
    manager_note("No unusual attendance days were detected in this data.", "good")

fig = px.line(daily_scored, x="Date", y="Attendance_Pct", markers=True, title="Daily Attendance %", labels={"Attendance_Pct": "Attendance %"})
fig.add_scatter(x=daily_scored.loc[daily_scored["IsAnomaly"], "Date"], y=daily_scored.loc[daily_scored["IsAnomaly"], "Attendance_Pct"], mode="markers", name="Unusual day")
st.plotly_chart(readable_chart(fig), use_container_width=True)

left, right = st.columns(2)
with left:
    shift = attendance.groupby(["Date", "Shift"], as_index=False)["EmployeeID"].nunique()
    st.plotly_chart(readable_chart(px.line(shift, x="Date", y="EmployeeID", color="Shift", title="People Present by Shift", labels={"EmployeeID": "People Present"})), use_container_width=True)
with right:
    dept = attendance.groupby(["Department", "Gender"], as_index=False)["EmployeeID"].nunique()
    st.plotly_chart(readable_chart(px.bar(dept, x="Department", y="EmployeeID", color="Gender", barmode="group", title="Employees by Department and Gender", labels={"EmployeeID": "Employees"})), use_container_width=True)

st.subheader("Absent Employees Found from Missing Punch Records")
st.caption("There is no stored Absent flag. If an employee has no punch row on a date, the app counts that as absence.")
st.dataframe(absences.head(50), use_container_width=True)
