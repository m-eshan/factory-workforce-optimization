from __future__ import annotations

import pandas as pd

from config import OT_THRESHOLD_HOURS, WEI_DEFAULT_WEIGHTS


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, float(value)))


def compute_daily_wei(date, attendance_df, ot_df, bus_df, canteen_df, production_df, weights=None, total_employees=None):
    weights = weights or WEI_DEFAULT_WEIGHTS
    total_employees = total_employees or attendance_df["EmployeeID"].nunique()
    selected = pd.Timestamp(date)
    day_att = attendance_df[attendance_df["Date"] == selected]
    present_count = day_att["EmployeeID"].nunique()
    attendance_pct = present_count / max(total_employees, 1) * 100

    actual_ot = day_att["OTHours"].sum()
    threshold_ot = max(present_count * OT_THRESHOLD_HOURS * 0.12, 1)
    ot_efficiency = clamp(100 - (actual_ot / threshold_ot * 100))

    day_bus = bus_df[bus_df["Date"] == selected]
    bus_util = day_bus["Utilization_Pct"].mean() if not day_bus.empty else 0

    day_canteen = canteen_df[canteen_df["Date"] == selected]
    canteen_efficiency = clamp(100 - (day_canteen["WastePercent"].mean() if not day_canteen.empty else 0))

    day_prod = production_df[production_df["Date"] == selected]
    total_units = day_prod["ProductionUnits"].sum() if not day_prod.empty else 0
    per_employee = total_units / max(present_count, 1)
    production_df = production_df.sort_values("Date").copy()
    production_df["DailyUnits"] = production_df.groupby("Date")["ProductionUnits"].transform("sum")
    baseline = production_df.drop_duplicates("Date")["DailyUnits"].rolling(30, min_periods=5).mean().median()
    baseline_per_employee = baseline / max(total_employees, 1) if baseline and baseline > 0 else per_employee
    dept_productivity = clamp(per_employee / baseline_per_employee * 100 if baseline_per_employee else 0)

    components = {
        "Attendance_Pct": clamp(attendance_pct),
        "OT_Efficiency_Pct": ot_efficiency,
        "Bus_Utilization_Pct": clamp(bus_util),
        "Canteen_Efficiency_Pct": canteen_efficiency,
        "Dept_Productivity_Pct": dept_productivity,
    }
    wei = (
        weights["attendance"] * components["Attendance_Pct"]
        + weights["ot"] * components["OT_Efficiency_Pct"]
        + weights["bus"] * components["Bus_Utilization_Pct"]
        + weights["canteen"] * components["Canteen_Efficiency_Pct"]
        + weights["productivity"] * components["Dept_Productivity_Pct"]
    )
    return {"Date": selected, "WEI": clamp(wei), **components}


def build_wei_daily(attendance_df, bus_df, canteen_df, production_df, weights=None, total_employees=None) -> pd.DataFrame:
    dates = pd.date_range(attendance_df["Date"].min(), attendance_df["Date"].max(), freq="D")
    rows = [compute_daily_wei(date, attendance_df, attendance_df, bus_df, canteen_df, production_df, weights, total_employees) for date in dates]
    return pd.DataFrame(rows)
