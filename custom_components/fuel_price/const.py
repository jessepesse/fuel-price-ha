DOMAIN = "fuel_price"
SCAN_INTERVAL_MINUTES = 30

FUEL_TABS = {
    "95_e10": ("fuel-95", "95 E10"),
    "98_e5":  ("fuel-98", "98 E5"),
    "diesel": ("fuel-dsl", "Diesel"),
}

CONF_CITY = "city"
CONF_BASE_URL = "base_url"
CONF_FUEL_TYPES = "fuel_types"
CONF_STATION = "station"
CONF_SOURCE_TYPE = "source_type"
CONF_SCAN_INTERVAL = "scan_interval"
TOP_N_STATIONS = 5

SOURCE_TYPE_A = "type_a"
SOURCE_TYPE_B = "type_b"

STATION_CHEAPEST = "__cheapest__"

# Column indices in type_b table: station(0), updated(1), 95_e10(2), 98_e5(3), diesel(4)
FUEL_COLUMNS = {
    "95_e10": 2,
    "98_e5": 3,
    "diesel": 4,
}
