from __future__ import annotations

import numpy as np
import pandas as pd

from utils.ml_models import isolation_scores


def compute_fused_anomaly(scores_dict: dict[str, float], threshold: float = -0.1) -> tuple[float, bool, list[str]]:
    composite_score = float(np.mean(list(scores_dict.values()))) if scores_dict else 0.0
    anomalous_modules = [key for key, value in scores_dict.items() if value < threshold]
    is_high_priority = len(anomalous_modules) >= 2
    return composite_score, is_high_priority, anomalous_modules


def build_daily_anomaly_fusion(attendance_daily: pd.DataFrame, attendance_df: pd.DataFrame, canteen_df: pd.DataFrame, bus_df: pd.DataFrame) -> pd.DataFrame:
    attendance_scores = isolation_scores(attendance_daily[["Date", "PresentCount"]], "PresentCount")[["Date", "AnomalyScore"]].rename(columns={"AnomalyScore": "attendance"})
    ot_daily = attendance_df.groupby("Date", as_index=False)["OTHours"].sum().rename(columns={"OTHours": "TotalOTHours"})
    ot_scores = isolation_scores(ot_daily, "TotalOTHours")[["Date", "AnomalyScore"]].rename(columns={"AnomalyScore": "ot"})
    canteen_daily = canteen_df.groupby("Date", as_index=False)["WastePercent"].mean()
    canteen_scores = isolation_scores(canteen_daily, "WastePercent")[["Date", "AnomalyScore"]].rename(columns={"AnomalyScore": "canteen"})
    bus_daily = bus_df.groupby("Date", as_index=False)["Utilization_Pct"].mean()
    bus_scores = isolation_scores(bus_daily, "Utilization_Pct")[["Date", "AnomalyScore"]].rename(columns={"AnomalyScore": "bus"})

    fused = attendance_scores.merge(ot_scores, on="Date", how="outer").merge(canteen_scores, on="Date", how="outer").merge(bus_scores, on="Date", how="outer").fillna(0)
    rows = []
    for row in fused.itertuples(index=False):
        scores = {"attendance": row.attendance, "ot": row.ot, "canteen": row.canteen, "bus": row.bus}
        composite, high_priority, modules = compute_fused_anomaly(scores)
        rows.append({"Date": row.Date, "CompositeScore": composite, "HighPriority": high_priority, "ContributingModules": ", ".join(modules) or "None"})
    return pd.DataFrame(rows)
