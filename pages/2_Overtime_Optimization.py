from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from config import DEFAULT_MONTHLY_SALARY, DEPT_WEEKLY_OT_THRESHOLD, OT_MULTIPLIER
from utils.data_loader import load_all_data, weekly_department_ot
from utils.export_utils import export_dataframe_excel
from utils.ml_models import isolation_scores, train_overtime_forecast
from utils.ui_helpers import apply_global_style, manager_note, readable_chart
from utils.upload_ui import render_data_upload_panel

st.set_page_config(page_title="Overtime Optimization", layout="wide")
apply_global_style()
render_data_upload_panel()
st.title("Overtime: Extra Hours and Staff Details")
st.caption("See overtime cost by department and identify the exact employees who worked extra hours.")

data = load_all_data()
attendance = data["attendance"].copy()
hourly_rate = DEFAULT_MONTHLY_SALARY / 26 / 8
attendance["OTCost_Rs"] = attendance["OTHours"] * hourly_rate * OT_MULTIPLIER
weekly_ot = weekly_department_ot(attendance)
forecast = train_overtime_forecast(weekly_ot)
daily_ot = attendance.groupby("Date", as_index=False)["OTHours"].sum()
daily_ot = isolation_scores(daily_ot, "OTHours")
overtime_rows = attendance[attendance["OTHours"] > 0].copy()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total OT Hours", f"{attendance['OTHours'].sum():,.1f}")
col2.metric("OT Cost", f"Rs {attendance['OTCost_Rs'].sum():,.0f}")
col3.metric("Staff with OT", f"{overtime_rows['EmployeeID'].nunique():,}")
col4.metric("Forecast Error", f"{forecast['mae']:.1f} hours")

if overtime_rows.empty:
    manager_note("No overtime records found in the selected data.", "good")
else:
    top_employee = overtime_rows.groupby(["EmployeeID", "EmployeeName"], as_index=False)["OTHours"].sum().sort_values("OTHours", ascending=False).iloc[0]
    manager_note(f"Highest overtime staff member is {top_employee['EmployeeName']} ({top_employee['EmployeeID']}) with {top_employee['OTHours']:.1f} OT hours in this data.", "warn")

left, right = st.columns(2)
with left:
    dept_ot = attendance.groupby("Department", as_index=False)["OTHours"].sum()
    st.plotly_chart(readable_chart(px.bar(dept_ot, x="Department", y="OTHours", title="Department-wise Overtime", labels={"OTHours": "Overtime Hours"}, text_auto=".1f")), use_container_width=True)
with right:
    shift_ot = attendance.groupby("Shift", as_index=False)["OTHours"].sum()
    st.plotly_chart(readable_chart(px.bar(shift_ot, x="Shift", y="OTHours", title="Shift-wise Overtime", labels={"OTHours": "Overtime Hours"}, text_auto=".1f")), use_container_width=True)

fig = px.line(daily_ot, x="Date", y="OTHours", markers=True, title="Daily Overtime Hours With Unusual Days", labels={"OTHours": "Overtime Hours"})
fig.add_scatter(x=daily_ot.loc[daily_ot["IsAnomaly"], "Date"], y=daily_ot.loc[daily_ot["IsAnomaly"], "OTHours"], mode="markers", name="Unusual OT day")
st.plotly_chart(readable_chart(fig), use_container_width=True)

st.subheader("Staff Who Worked Overtime")
st.caption("This table shows the exact date, employee, in-time, out-time, total hours worked, extra hours, and estimated overtime cost.")

filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    selected_departments = st.multiselect("Department", sorted(overtime_rows["Department"].dropna().unique()), default=sorted(overtime_rows["Department"].dropna().unique()))
with filter_col2:
    selected_shifts = st.multiselect("Shift", sorted(overtime_rows["Shift"].dropna().unique()), default=sorted(overtime_rows["Shift"].dropna().unique()))
with filter_col3:
    min_ot = st.number_input("Minimum extra hours", min_value=0.0, max_value=float(max(overtime_rows["OTHours"].max(), 0)), value=0.1, step=0.5)

date_col1, date_col2 = st.columns(2)
with date_col1:
    start_date = st.date_input("From date", overtime_rows["Date"].min().date())
with date_col2:
    end_date = st.date_input("To date", overtime_rows["Date"].max().date())

filtered_ot = overtime_rows[
    (overtime_rows["Department"].isin(selected_departments))
    & (overtime_rows["Shift"].isin(selected_shifts))
    & (overtime_rows["OTHours"] >= min_ot)
    & (overtime_rows["Date"] >= pd.Timestamp(start_date))
    & (overtime_rows["Date"] <= pd.Timestamp(end_date))
].copy()

filtered_ot["Date"] = filtered_ot["Date"].dt.date
filtered_ot["HoursWorked"] = filtered_ot["HoursWorked"].round(2)
filtered_ot["OTHours"] = filtered_ot["OTHours"].round(2)
filtered_ot["OTCost_Rs"] = filtered_ot["OTCost_Rs"].round(0).astype(int)

detail_columns = [
    "Date",
    "EmployeeID",
    "EmployeeName",
    "Department",
    "SubDepartment",
    "Shift",
    "InTime",
    "OutTime",
    "HoursWorked",
    "OTHours",
    "OTCost_Rs",
]
st.dataframe(
    filtered_ot[detail_columns].sort_values(["Date", "OTHours"], ascending=[False, False]),
    use_container_width=True,
    hide_index=True,
)

summary = filtered_ot.groupby(["EmployeeID", "EmployeeName", "Department"], as_index=False).agg(
    OT_Days=("Date", "count"),
    Total_OT_Hours=("OTHours", "sum"),
    Estimated_OT_Cost_Rs=("OTCost_Rs", "sum"),
).sort_values("Total_OT_Hours", ascending=False)
summary["Total_OT_Hours"] = summary["Total_OT_Hours"].round(2)
st.subheader("Employee Overtime Summary")
st.dataframe(summary.head(30), use_container_width=True, hide_index=True)

excel_bytes = export_dataframe_excel({"Overtime_Details": filtered_ot[detail_columns], "Employee_OT_Summary": summary, "Weekly_Breaches": weekly_ot[weekly_ot["OTHours"] > DEPT_WEEKLY_OT_THRESHOLD]})
st.download_button("Download Overtime Staff Report", excel_bytes, file_name="overtime_staff_report.xlsx")

breaches = weekly_ot[weekly_ot["OTHours"] > DEPT_WEEKLY_OT_THRESHOLD]
st.subheader("Weekly Department Limit Breaches")
if breaches.empty:
    manager_note("No department crossed the weekly overtime limit.", "good")
else:
    st.dataframe(breaches, use_container_width=True, hide_index=True)
