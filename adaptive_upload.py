from __future__ import annotations

import shutil
from difflib import get_close_matches
from pathlib import Path

import pandas as pd

from config import BUS_ROUTES, DATA_DIR, FUEL_PRICE_RS

UPLOAD_DATA_DIR = DATA_DIR.parent / "uploaded_data"

DATASET_FILES = {
    "attendance": "Attendance_Raw.csv",
    "master": "Employee_Master.csv",
    "canteen": "Canteen_Data.csv",
    "bus": "Bus_Data.csv",
    "routes": "Bus_Routes.csv",
    "coordinates": "Bus_Stop_Coordinates.csv",
    "production": "Production_Data.csv",
}

ALIASES = {
    "Date": ["date", "day", "attendance date", "punch date", "work date"],
    "EmployeeID": ["employeeid", "employee id", "emp id", "empid", "worker id", "staff id", "id"],
    "Shift": ["shift", "shift name", "shift code", "duty shift"],
    "InTime": ["intime", "in time", "check in", "check-in", "punch in", "login time", "entry time"],
    "OutTime": ["outtime", "out time", "check out", "check-out", "punch out", "logout time", "exit time"],
    "EmployeeName": ["employee name", "name", "worker name", "staff name"],
    "Gender": ["gender", "sex"],
    "Department": ["department", "dept", "division"],
    "SubDepartment": ["subdepartment", "sub department", "sub dept", "section"],
    "EmployeeType": ["employee type", "type", "employment type", "category"],
    "Location": ["location", "place", "town", "home location", "area"],
    "PrimaryShift": ["primary shift", "default shift", "regular shift"],
    "DateOfJoining": ["date of joining", "doj", "joining date", "join date"],
    "BusID": ["bus id", "busid", "vehicle id"],
    "Route": ["route", "route name", "bus route"],
    "Capacity": ["capacity", "seats", "seat capacity"],
    "Occupancy": ["occupancy", "passengers", "riders", "employee count"],
    "Utilization_Pct": ["utilization pct", "utilization %", "utilisation %", "occupancy %"],
    "RouteDistance_Km": ["route distance km", "distance km", "distance"],
    "FuelEfficiency_Kmpl": ["fuel efficiency kmpl", "kmpl", "mileage"],
    "FuelUsed_Litres": ["fuel used litres", "fuel litres", "litres"],
    "FuelCost_Rs": ["fuel cost", "fuel cost rs", "fuel amount"],
    "CostPerEmployee_Rs": ["cost per employee", "cost per rider"],
    "Latitude": ["latitude", "lat"],
    "Longitude": ["longitude", "lon", "lng", "long"],
    "Attendees": ["attendees", "present count", "present employees"],
    "MealsPrepared": ["meals prepared", "prepared", "food prepared"],
    "MealsConsumed": ["meals consumed", "consumed", "food consumed"],
    "MealsWasted": ["meals wasted", "wasted", "food wasted"],
    "WastePercent": ["waste percent", "waste %", "wastage %"],
    "CostPerMeal": ["cost per meal", "meal cost"],
    "TotalCost": ["total cost", "canteen cost"],
    "WastageCost": ["wastage cost", "waste cost"],
    "HistoricalAvgMeals": ["historical avg meals", "rolling avg meals", "average meals"],
    "ProductionUnits": ["production units", "units", "output", "quantity"],
}

REQUIRED = {
    "attendance": ["Date", "EmployeeID", "Shift", "InTime", "OutTime"],
    "master": ["EmployeeID", "EmployeeName", "Gender", "Department", "SubDepartment", "EmployeeType", "Location", "PrimaryShift", "DateOfJoining"],
    "canteen": ["Date", "Shift", "Attendees", "MealsPrepared", "MealsConsumed"],
    "bus": ["Date", "BusID", "Route", "Capacity", "Occupancy"],
    "routes": ["BusID", "Route", "Capacity", "FuelEfficiency_Kmpl", "RouteDistance_Km"],
    "coordinates": ["Location", "Latitude", "Longitude"],
    "production": ["Date", "Department", "ProductionUnits"],
}


def clean_name(name: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else " " for ch in str(name)).strip()


def canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = {clean_name(col): col for col in df.columns}
    rename = {}
    for canonical, aliases in ALIASES.items():
        options = [clean_name(canonical), *[clean_name(alias) for alias in aliases]]
        for option in options:
            if option in normalized:
                rename[normalized[option]] = canonical
                break
        if canonical not in rename.values():
            match = get_close_matches(clean_name(canonical), normalized.keys(), n=1, cutoff=0.82)
            if match:
                rename[normalized[match[0]]] = canonical
    return df.rename(columns=rename)


def infer_dataset_kind(name: str, df: pd.DataFrame) -> str | None:
    lower_name = name.lower()
    for kind in ["attendance", "master", "canteen", "bus", "routes", "coordinates", "production"]:
        if kind in lower_name or DATASET_FILES[kind].lower().replace("_", "").replace(".csv", "") in lower_name.replace("_", ""):
            return kind
    scores = {}
    columns = set(canonicalize_columns(df).columns)
    for kind, required in REQUIRED.items():
        scores[kind] = len(columns.intersection(required)) / len(required)
    best = max(scores, key=scores.get)
    return best if scores[best] >= 0.45 else None


def read_uploaded_file(uploaded_file) -> list[tuple[str, pd.DataFrame]]:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return [(uploaded_file.name, pd.read_csv(uploaded_file))]
    if suffix in {".xlsx", ".xls"}:
        workbook = pd.read_excel(uploaded_file, sheet_name=None)
        return [(f"{uploaded_file.name}:{sheet_name}", sheet_df) for sheet_name, sheet_df in workbook.items()]
    return []


def prepare_upload_workspace() -> Path:
    UPLOAD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename in DATASET_FILES.values():
        source = DATA_DIR / filename
        if source.exists():
            shutil.copy2(source, UPLOAD_DATA_DIR / filename)
    return UPLOAD_DATA_DIR


def normalize_dataset(kind: str, df: pd.DataFrame) -> pd.DataFrame:
    df = canonicalize_columns(df).copy()
    if kind == "attendance":
        return df[["Date", "EmployeeID", "Shift", "InTime", "OutTime"]].dropna(subset=["Date", "EmployeeID"])
    if kind == "canteen":
        df = ensure_canteen_columns(df)
    elif kind == "bus":
        df = ensure_bus_columns(df)
    elif kind == "master":
        df = ensure_master_columns(df)
    elif kind == "production":
        df = ensure_production_columns(df)
    return df


def ensure_master_columns(df: pd.DataFrame) -> pd.DataFrame:
    defaults = {
        "EmployeeName": "Unknown",
        "Gender": "Unknown",
        "Department": "Unknown",
        "SubDepartment": "Unknown",
        "EmployeeType": "Unknown",
        "Location": "Unknown",
        "PrimaryShift": "A",
        "DateOfJoining": pd.Timestamp.today().date().isoformat(),
    }
    for column, value in defaults.items():
        if column not in df.columns:
            df[column] = value
    return df[REQUIRED["master"]]


def ensure_canteen_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["MealsWasted"] = df.get("MealsWasted", (df["MealsPrepared"] - df["MealsConsumed"]).clip(lower=0))
    df["WastePercent"] = df.get("WastePercent", df["MealsWasted"] / df["MealsPrepared"].clip(lower=1) * 100)
    df["CostPerMeal"] = df.get("CostPerMeal", 35)
    df["TotalCost"] = df.get("TotalCost", df["MealsPrepared"] * df["CostPerMeal"])
    df["WastageCost"] = df.get("WastageCost", df["MealsWasted"] * df["CostPerMeal"])
    if "HistoricalAvgMeals" not in df.columns:
        df["HistoricalAvgMeals"] = df.groupby("Shift")["MealsPrepared"].transform(lambda s: s.shift(1).rolling(30, min_periods=1).mean()).fillna(df["MealsPrepared"])
    return df


def ensure_bus_columns(df: pd.DataFrame) -> pd.DataFrame:
    route_defaults = pd.DataFrame(BUS_ROUTES).set_index("Route")
    if "RouteDistance_Km" not in df.columns:
        df["RouteDistance_Km"] = df["Route"].map(route_defaults["RouteDistance_Km"]).fillna(10)
    if "FuelEfficiency_Kmpl" not in df.columns:
        df["FuelEfficiency_Kmpl"] = df["Route"].map(route_defaults["FuelEfficiency_Kmpl"]).fillna(5)
    df["Utilization_Pct"] = df.get("Utilization_Pct", df["Occupancy"] / df["Capacity"].clip(lower=1) * 100)
    df["FuelUsed_Litres"] = df.get("FuelUsed_Litres", (df["RouteDistance_Km"] * 2) / df["FuelEfficiency_Kmpl"].clip(lower=1))
    df["FuelCost_Rs"] = df.get("FuelCost_Rs", df["FuelUsed_Litres"] * FUEL_PRICE_RS)
    df["CostPerEmployee_Rs"] = df.get("CostPerEmployee_Rs", df["FuelCost_Rs"] / df["Occupancy"].clip(lower=1))
    return df


def ensure_production_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df[["Date", "Department", "ProductionUnits"]]


def save_uploaded_files(uploaded_files) -> dict:
    upload_dir = prepare_upload_workspace()
    imported = []
    skipped = []
    for uploaded_file in uploaded_files:
        for name, frame in read_uploaded_file(uploaded_file):
            kind = infer_dataset_kind(name, frame)
            if kind is None:
                skipped.append(f"{name}: could not identify table type")
                continue
            try:
                normalized = normalize_dataset(kind, frame)
                missing = [column for column in REQUIRED[kind] if column not in normalized.columns]
                if missing:
                    skipped.append(f"{name}: missing {', '.join(missing)}")
                    continue
            except Exception as exc:
                skipped.append(f"{name}: {exc}")
                continue
            normalized.to_csv(upload_dir / DATASET_FILES[kind], index=False)
            imported.append(f"{name} -> {DATASET_FILES[kind]}")
    return {"data_dir": upload_dir, "imported": imported, "skipped": skipped}
