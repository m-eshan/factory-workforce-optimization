from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from config import DATA_DIR, END_DATE, OT_THRESHOLD_HOURS, SHIFT_TIMES, START_DATE


def get_active_data_dir(data_dir: Path | None = None) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    try:
        import streamlit as st

        active = st.session_state.get("active_data_dir")
        if active:
            return Path(active)
    except Exception:
        pass
    return DATA_DIR


def load_csv(name: str, data_dir: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(get_active_data_dir(data_dir) / name)


def time_to_minutes(series: pd.Series) -> pd.Series:
    parts = series.astype(str).str.split(":", expand=True).astype(int)
    return parts[0] * 60 + parts[1]


def derive_hours(attendance_df: pd.DataFrame) -> pd.DataFrame:
    df = attendance_df.copy()
    in_minutes = time_to_minutes(df["InTime"])
    out_minutes = time_to_minutes(df["OutTime"])
    duration = out_minutes - in_minutes
    duration = np.where(duration <= 0, duration + 1440, duration)
    df["HoursWorked"] = duration / 60
    df["OTHours"] = (df["HoursWorked"] - OT_THRESHOLD_HOURS).clip(lower=0)
    return df


def load_attendance_raw(data_dir: Path | None = None) -> pd.DataFrame:
    df = load_csv("Attendance_Raw.csv", data_dir)
    allowed = ["Date", "EmployeeID", "Shift", "InTime", "OutTime"]
    return df[allowed]


def load_employee_master(data_dir: Path | None = None) -> pd.DataFrame:
    return load_csv("Employee_Master.csv", data_dir)


def load_enriched_attendance(data_dir: Path | None = None) -> pd.DataFrame:
    attendance_df = derive_hours(load_attendance_raw(data_dir))
    master_df = load_employee_master(data_dir)
    merged = pd.merge(attendance_df, master_df, on="EmployeeID", how="left")
    merged["Date"] = pd.to_datetime(merged["Date"])
    return merged


def detect_absences(attendance_df: pd.DataFrame | None = None, master_df: pd.DataFrame | None = None) -> pd.DataFrame:
    attendance_df = load_attendance_raw() if attendance_df is None else attendance_df
    master_df = load_employee_master() if master_df is None else master_df
    attendance_dates = pd.to_datetime(attendance_df["Date"])
    dates = pd.date_range(attendance_dates.min(), attendance_dates.max(), freq="D")
    full = pd.MultiIndex.from_product([master_df["EmployeeID"], dates], names=["EmployeeID", "Date"]).to_frame(index=False)
    present = attendance_df[["EmployeeID", "Date"]].copy()
    present["Date"] = pd.to_datetime(present["Date"])
    present["Present"] = True
    absence_df = full.merge(present, on=["EmployeeID", "Date"], how="left")
    absence_df["Present"] = absence_df["Present"].fillna(False)
    absence_df = absence_df[~absence_df["Present"]].drop(columns="Present")
    return absence_df.merge(master_df, on="EmployeeID", how="left")


def load_all_data(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    data_dir = get_active_data_dir(data_dir)
    return {
        "master": load_employee_master(data_dir),
        "attendance_raw": load_attendance_raw(data_dir),
        "attendance": load_enriched_attendance(data_dir),
        "canteen": parse_dates(load_csv("Canteen_Data.csv", data_dir)),
        "bus": parse_dates(load_csv("Bus_Data.csv", data_dir)),
        "routes": load_csv("Bus_Routes.csv", data_dir),
        "coordinates": load_csv("Bus_Stop_Coordinates.csv", data_dir),
        "production": parse_dates(load_csv("Production_Data.csv", data_dir)),
    }


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    if "Date" in df.columns:
        df = df.copy()
        df["Date"] = pd.to_datetime(df["Date"])
    return df


def daily_attendance_counts(attendance_df: pd.DataFrame, total_employees: int) -> pd.DataFrame:
    counts = attendance_df.groupby("Date")["EmployeeID"].nunique().rename("PresentCount").reset_index()
    all_dates = pd.DataFrame({"Date": pd.date_range(attendance_df["Date"].min(), attendance_df["Date"].max(), freq="D")})
    counts = all_dates.merge(counts, on="Date", how="left").fillna({"PresentCount": 0})
    counts["Attendance_Pct"] = counts["PresentCount"] / total_employees * 100
    return counts


def weekly_department_ot(attendance_df: pd.DataFrame) -> pd.DataFrame:
    df = attendance_df.copy()
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
    df["Year"] = df["Date"].dt.year
    return df.groupby(["Year", "Week", "Department"], as_index=False)["OTHours"].sum()


def date_filter(df: pd.DataFrame, selected_date) -> pd.DataFrame:
    selected = pd.Timestamp(selected_date)
    return df[df["Date"] == selected]


def expected_shift_hours(shift: str) -> float:
    start = pd.Timestamp(f"2026-01-01 {SHIFT_TIMES[shift]['start']}")
    end_date = "2026-01-02" if shift == "C" else "2026-01-01"
    end = pd.Timestamp(f"{end_date} {SHIFT_TIMES[shift]['end']}")
    return (end - start).total_seconds() / 3600
