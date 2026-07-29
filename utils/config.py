from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

START_DATE = "2026-01-01"
END_DATE = "2026-06-30"
EMPLOYEE_COUNT = 500

SHIFT_TIMES = {
    "A": {"start": "06:00", "end": "14:00"},
    "B": {"start": "14:00", "end": "22:00"},
    "C": {"start": "22:00", "end": "06:00"},
}

OT_THRESHOLD_HOURS = 8.0
OT_MULTIPLIER = 1.5
DEFAULT_MONTHLY_SALARY = 18500
DEPT_WEEKLY_OT_THRESHOLD = 40
FUEL_PRICE_RS = 96
ANOMALY_CONTAMINATION = 0.05

WEI_DEFAULT_WEIGHTS = {
    "attendance": 0.20,
    "ot": 0.20,
    "bus": 0.20,
    "canteen": 0.20,
    "productivity": 0.20,
}

FESTIVAL_DATES = ["2026-01-14", "2026-01-15", "2026-03-08", "2026-04-14"]
HIGH_OT_WINDOWS = [
    ("2026-02-10", "2026-02-14"),
    ("2026-03-15", "2026-03-19"),
    ("2026-05-05", "2026-05-09"),
]

DEPARTMENTS = ["Biscuit", "Wafer", "Maintenance"]
SUBDEPARTMENTS = {
    "Biscuit": ["Production", "Packing", "Quality"],
    "Wafer": ["Production", "Packing", "Quality"],
    "Maintenance": ["Utilities", "Electrical", "Mechanical", "TF"],
}
EMPLOYEE_TYPES = ["Contract", "BIL", "MAPS", "Operator"]
EMPLOYEE_TYPE_WEIGHTS = [0.55, 0.20, 0.15, 0.10]
GENDER_WEIGHTS = [0.65, 0.35]

LOCATIONS = [
    "Perundurai",
    "Erode",
    "Chithode",
    "Nasiyanur",
    "Villarasampatti",
    "Kodumudi",
    "Gobichettipalayam",
    "Bhavani",
    "Kavindapadi",
    "Modakurichi",
]
LOCATION_WEIGHTS = [5, 7, 4, 5, 4, 3, 4, 5, 3, 4]

BUS_ROUTES = [
    {"BusID": "BUS01", "Route": "Perundurai", "Capacity": 24, "FuelEfficiency_Kmpl": 5.0, "RouteDistance_Km": 12},
    {"BusID": "BUS02", "Route": "Erode", "Capacity": 36, "FuelEfficiency_Kmpl": 4.8, "RouteDistance_Km": 18},
    {"BusID": "BUS03", "Route": "Chithode", "Capacity": 24, "FuelEfficiency_Kmpl": 5.2, "RouteDistance_Km": 8},
    {"BusID": "BUS04", "Route": "Nasiyanur", "Capacity": 32, "FuelEfficiency_Kmpl": 4.9, "RouteDistance_Km": 15},
    {"BusID": "BUS05", "Route": "Gobichettipalayam", "Capacity": 24, "FuelEfficiency_Kmpl": 4.5, "RouteDistance_Km": 28},
]

LOCATION_ROUTE_MAP = {
    "Perundurai": "Perundurai",
    "Villarasampatti": "Perundurai",
    "Erode": "Erode",
    "Bhavani": "Erode",
    "Chithode": "Chithode",
    "Kavindapadi": "Chithode",
    "Nasiyanur": "Nasiyanur",
    "Modakurichi": "Nasiyanur",
    "Gobichettipalayam": "Gobichettipalayam",
    "Kodumudi": "Gobichettipalayam",
}

BUS_STOP_COORDINATES = [
    ("Perundurai", 11.2757, 77.5872),
    ("Erode", 11.3410, 77.7172),
    ("Chithode", 11.3100, 77.6700),
    ("Nasiyanur", 11.2900, 77.6300),
    ("Villarasampatti", 11.2600, 77.5600),
    ("Kodumudi", 11.1940, 77.8650),
    ("Gobichettipalayam", 11.4540, 77.4360),
    ("Bhavani", 11.4440, 77.6840),
    ("Kavindapadi", 11.2390, 77.6970),
    ("Modakurichi", 11.3390, 77.6220),
    ("Factory (SRIHER Industrial Zone)", 11.2800, 77.6000),
]

PRODUCTION_BASE_UNITS = {"Biscuit": 45000, "Wafer": 20000, "Maintenance": 5000}
