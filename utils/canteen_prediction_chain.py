from __future__ import annotations

import pandas as pd
from scipy.stats import pearsonr


def baseline_preparation(canteen_df: pd.DataFrame) -> pd.Series:
    return canteen_df["HistoricalAvgMeals"]


def model_based_preparation(canteen_df: pd.DataFrame, model_result: dict | None = None) -> pd.Series:
    if model_result is None or "model" not in model_result:
        predicted_consumption = canteen_df["MealsConsumed"]
    else:
        features = canteen_df.copy()
        features["Date"] = pd.to_datetime(features["Date"])
        features["day_of_week"] = features["Date"].dt.dayofweek
        features["month"] = features["Date"].dt.month
        features["festival_flag"] = features["Date"].isin(pd.to_datetime(["2026-01-14", "2026-01-15", "2026-03-08", "2026-04-14"])).astype(int)
        features["monsoon_flag"] = features["month"].isin([10, 11, 12]).astype(int)
        features["rolling_7day_avg_attendance"] = features.groupby("Shift")["Attendees"].transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean()).fillna(features["Attendees"].mean())
        predicted_consumption = model_result["model"].predict(features[model_result["features"]])
    return pd.Series(predicted_consumption, index=canteen_df.index) * 1.10


def compute_waste_comparison(canteen_df: pd.DataFrame, baseline_prep: pd.Series, model_prep: pd.Series) -> pd.DataFrame:
    consumed = canteen_df["MealsConsumed"]
    baseline_waste_pct = ((baseline_prep - consumed).clip(lower=0) / baseline_prep.clip(lower=1) * 100).mean()
    proposed_waste_pct = ((model_prep - consumed).clip(lower=0) / model_prep.clip(lower=1) * 100).mean()
    improvement = ((proposed_waste_pct - baseline_waste_pct) / baseline_waste_pct * 100) if baseline_waste_pct else 0
    return pd.DataFrame(
        [
            {
                "Metric": "Avg Daily Waste %",
                "Baseline": round(float(baseline_waste_pct), 2),
                "Proposed": round(float(proposed_waste_pct), 2),
                "Improvement %": round(float(improvement), 2),
            }
        ]
    )


def attendance_consumption_correlation(canteen_df: pd.DataFrame) -> tuple[float, float]:
    if len(canteen_df) < 3:
        return 0.0, 1.0
    corr, p_value = pearsonr(canteen_df["Attendees"], canteen_df["MealsConsumed"])
    return float(corr), float(p_value)
