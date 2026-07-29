from __future__ import annotations

import math
import sys
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from geopy.distance import geodesic
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import ANOMALY_CONTAMINATION, BUS_ROUTES, EMPLOYEE_COUNT, FUEL_PRICE_RS
from utils.data_loader import daily_attendance_counts, load_all_data


def _add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"])
    out["day_of_week"] = out["Date"].dt.dayofweek
    out["month"] = out["Date"].dt.month
    out["festival_flag"] = out["Date"].isin(pd.to_datetime(["2026-01-14", "2026-01-15", "2026-03-08", "2026-04-14"])).astype(int)
    out["monsoon_flag"] = out["month"].isin([10, 11, 12]).astype(int)
    return out


def train_attendance_forecast(daily_counts: pd.DataFrame) -> dict:
    df = _add_date_features(daily_counts)
    df["rolling_7day_avg_attendance"] = df["PresentCount"].shift(1).rolling(7, min_periods=1).mean().fillna(df["PresentCount"].mean())
    features = ["day_of_week", "month", "festival_flag", "monsoon_flag", "rolling_7day_avg_attendance"]
    return _fit_rf(df, features, "PresentCount")


def train_canteen_forecast(canteen_df: pd.DataFrame) -> dict:
    df = _add_date_features(canteen_df)
    df["rolling_7day_avg_attendance"] = df.groupby("Shift")["Attendees"].transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean()).fillna(df["Attendees"].mean())
    features = ["day_of_week", "month", "festival_flag", "monsoon_flag", "rolling_7day_avg_attendance", "Attendees"]
    x = df[features]
    y = df["MealsConsumed"]
    transformer = ColumnTransformer([("scale_attendees", MinMaxScaler(), ["Attendees"])], remainder="passthrough")
    model = Pipeline([("features", transformer), ("rf", RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42))])
    return _fit_model(model, x, y, features)


def _fit_rf(df: pd.DataFrame, features: list[str], target: str) -> dict:
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    return _fit_model(model, df[features], df[target], features)


def _fit_model(model, x: pd.DataFrame, y: pd.Series, features: list[str]) -> dict:
    if len(x) < 8:
        return {"model": model, "features": features, "mae": 0, "rmse": 0, "r2": 0}
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, shuffle=False)
    model.fit(x_train, y_train)
    pred = model.predict(x_test)
    return {
        "model": model,
        "features": features,
        "mae": float(mean_absolute_error(y_test, pred)),
        "rmse": float(math.sqrt(mean_squared_error(y_test, pred))),
        "r2": float(r2_score(y_test, pred)) if len(y_test) > 1 else 0,
        "last_prediction": float(pred[-1]) if len(pred) else None,
    }
  



def train_overtime_forecast(weekly_ot_df: pd.DataFrame) -> dict:
    df = weekly_ot_df.sort_values(["Department", "Year", "Week"]).copy()
    df["trailing_4week_OT_avg"] = df.groupby("Department")["OTHours"].transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean()).fillna(df["OTHours"].mean())
    df["TargetNextWeekOT"] = df.groupby("Department")["OTHours"].shift(-1)
    df = df.dropna(subset=["TargetNextWeekOT"])
    features = ["Week", "Department", "trailing_4week_OT_avg"]
    model = Pipeline(
        [
            ("prep", ColumnTransformer([("dept", OneHotEncoder(handle_unknown="ignore"), ["Department"])], remainder="passthrough")),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )
    result = _fit_model(model, df[features], df["TargetNextWeekOT"], features)
    preds = result["model"].predict(df[features]) if len(df) else np.array([])
    result["mape"] = float(np.mean(np.abs((df["TargetNextWeekOT"] - preds) / df["TargetNextWeekOT"].replace(0, np.nan))) * 100) if len(df) else 0
    return result


def isolation_scores(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    out = df.copy()
    values = out[[value_col]].fillna(0)
    if len(out) < 10:
        out["AnomalyScore"] = 0.0
        out["IsAnomaly"] = False
        return out
    model = IsolationForest(contamination=ANOMALY_CONTAMINATION, random_state=42)
    model.fit(values)
    out["AnomalyScore"] = model.decision_function(values)
    out["IsAnomaly"] = model.predict(values) == -1
    return out


def cluster_bus_stops(employee_locations: pd.DataFrame, n_clusters: int = 5) -> dict:
    coords = employee_locations[["Latitude", "Longitude"]].dropna()
    clusters = min(n_clusters, len(coords))
    if clusters < 2:
        return {"labels": [], "centers": pd.DataFrame(), "silhouette": 0, "inertia": []}
    model = KMeans(n_clusters=clusters, random_state=42, n_init=10)
    labels = model.fit_predict(coords)
    silhouette = silhouette_score(coords, labels) if len(set(labels)) > 1 else 0
    inertia = []
    for k in range(2, min(10, len(coords)) + 1):
        inertia.append({"k": k, "inertia": float(KMeans(n_clusters=k, random_state=42, n_init=10).fit(coords).inertia_)})
    centers = pd.DataFrame(model.cluster_centers_, columns=["Latitude", "Longitude"])
    centers["Cluster"] = range(len(centers))
    centers["PointCount"] = pd.Series(labels).value_counts().sort_index().values
    return {"labels": labels, "centers": centers, "silhouette": float(silhouette), "inertia": inertia}


def adaptive_bus_recommendation(employee_locations: pd.DataFrame, capacity: int = 24, n_clusters: int = 5) -> dict:
    result = cluster_bus_stops(employee_locations, n_clusters)
    centers = result["centers"].copy()
    if centers.empty:
        result["recommended_buses"] = 0
        result["merge_count"] = 0
        return result
    low_clusters = centers[centers["PointCount"] < capacity * 0.4]
    result["recommended_buses"] = max(1, len(centers) - len(low_clusters))
    result["merge_count"] = int(len(low_clusters))
    return result


def nearest_location(lat: float, lon: float, coordinates_df: pd.DataFrame) -> str:
    stops = coordinates_df.copy()
    stops["Distance"] = stops.apply(lambda r: geodesic((lat, lon), (r["Latitude"], r["Longitude"])).km, axis=1)
    return str(stops.sort_values("Distance").iloc[0]["Location"])


def shortest_route(stop_list: list[str], coordinates_df: pd.DataFrame) -> dict:
    factory = "Factory (SRIHER Industrial Zone)"
    ordered_stops = order_stops_nearest_neighbor(stop_list, coordinates_df)
    nodes = list(dict.fromkeys(ordered_stops + [factory]))
    coords = coordinates_df.set_index("Location")[["Latitude", "Longitude"]].to_dict("index")
    graph = nx.Graph()
    for source in nodes:
        for target in nodes:
            if source == target or source not in coords or target not in coords:
                continue
            graph.add_edge(source, target, weight=geodesic(tuple(coords[source].values()), tuple(coords[target].values())).km)
    if not ordered_stops:
        return {"path": [factory], "distance_km": 0, "fuel_cost_rs": 0}
    path = ordered_stops + [factory]
    distance = 0.0
    for source, target in zip(path, path[1:]):
        distance += nx.dijkstra_path_length(graph, source, target, weight="weight")
    return {"path": path, "distance_km": float(distance), "fuel_cost_rs": float((distance * 2 / 5.0) * FUEL_PRICE_RS)}


def order_stops_nearest_neighbor(stop_list: list[str], coordinates_df: pd.DataFrame) -> list[str]:
    factory = "Factory (SRIHER Industrial Zone)"
    unique_stops = [stop for stop in dict.fromkeys(stop_list) if stop != factory]
    coords = coordinates_df.set_index("Location")[["Latitude", "Longitude"]].to_dict("index")
    remaining = [stop for stop in unique_stops if stop in coords]
    if not remaining:
        return []
    current = min(remaining, key=lambda stop: geodesic(tuple(coords[stop].values()), tuple(coords[factory].values())).km)
    ordered = [current]
    remaining.remove(current)
    while remaining:
        current = min(remaining, key=lambda stop: geodesic(tuple(coords[ordered[-1]].values()), tuple(coords[stop].values())).km)
        ordered.append(current)
        remaining.remove(current)
    return ordered


def route_merge_recommendations(bus_df: pd.DataFrame) -> pd.DataFrame:
    df = bus_df.sort_values(["Route", "Date"]).copy()
    df["Trailing30Util"] = df.groupby("Route")["Utilization_Pct"].transform(lambda s: s.rolling(30, min_periods=5).mean())
    return df[df["Trailing30Util"] < 50][["Date", "Route", "Trailing30Util"]].drop_duplicates(["Date", "Route"])


if __name__ == "__main__":
    data = load_all_data()
    daily_counts = daily_attendance_counts(data["attendance"], EMPLOYEE_COUNT)
    result = train_attendance_forecast(daily_counts)
    print("MAE:", result.get("mae"))
    print("RMSE:", result.get("rmse"))
    print("R2:", result.get("r2"))
