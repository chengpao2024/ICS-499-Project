# =====================================================
# Campus Asset Tracker - Configuration
# =====================================================

# -------------------------
# Auth / Redirects
# -------------------------
PHP_LOGIN_URL = "http://localhost/index.php"


# -------------------------
# Database
# -------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "cat_db",
    "port": 3306,
}


# -------------------------
# Asset Status
# -------------------------
STATUSES = ["available", "in-use", "maintenance"]

STATUS_LABELS = {
    "available": "Available",
    "in-use": "In Use",
    "maintenance": "Maintenance",
}

STATUS_CLASSES = {
    "available": "badge-available",
    "in-use": "badge-inuse",
    "maintenance": "badge-maintenance",
}


# -------------------------
# Editable Fields
# -------------------------
EDITABLE_FIELDS = {
    "name": "asset_name",
    "category": "asset_category",
    "location": "asset_location",
}


# -------------------------
# Sorting
# -------------------------
SORT_FIELDS = {
    "name": "asset_name",
    "asset_id": "asset_id",
}


# -------------------------
# UI Defaults
# -------------------------
DEFAULT_CATEGORIES = [
    "All Categories",
    "IT Equipment",
    "AV Equipment",
    "Media Equipment",
    "Furniture",
]

DEFAULT_STATUSES = [
    "All Statuses",
    "available",
    "in-use",
    "maintenance",
]