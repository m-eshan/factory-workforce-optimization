from __future__ import annotations

import streamlit as st

from config import DATA_DIR
from utils.data_loader import get_active_data_dir, load_all_data
from utils.ui_helpers import apply_global_style
from utils.upload_ui import render_data_upload_panel


st.set_page_config(page_title="Factory Workforce Optimization", page_icon="Factory", layout="wide")
apply_global_style()


def data_ready() -> bool:
    required = [
        "Employee_Master.csv",
        "Attendance_Raw.csv",
        "Canteen_Data.csv",
        "Bus_Data.csv",
        "Bus_Routes.csv",
        "Bus_Stop_Coordinates.csv",
        "Production_Data.csv",
    ]
    data_dir = get_active_data_dir()
    return all((data_dir / name).exists() for name in required)


@st.cache_data(show_spinner=False)
def cached_data(data_dir_key: str):
    return load_all_data()


st.title("AI-Driven Workforce and Resource Optimization Platform")
st.caption("A simple operations dashboard for attendance, overtime, buses, canteen waste, productivity, and overall workforce health.")
render_data_upload_panel()

if not data_ready():
    st.warning("Please upload the required factory data files from the sidebar, or place the CSV files in the data folder.")
else:
    data = cached_data(str(get_active_data_dir()))
    st.success("Data is ready. Open any page from the sidebar to see the factory insights.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Employees", f"{len(data['master']):,}")
    col2.metric("Attendance Records", f"{len(data['attendance_raw']):,}")
    col3.metric("Date Range", f"{data['attendance']['Date'].min().date()} to {data['attendance']['Date'].max().date()}")
    col4.metric("Data Source", "Uploaded" if "active_data_dir" in st.session_state else "Provided")

    with st.expander("How the app reads attendance"):
        st.write(
            "Attendance files usually contain only employee ID, date, shift, in-time, and out-time. "
            "The app adds employee details from the master file automatically and calculates overtime from punch times."
        )
        st.dataframe(data["attendance_raw"].head(), use_container_width=True)

