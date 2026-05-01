# =====================================================
# Campus Asset Tracker - Configuration
# =====================================================

# -------------------------
# Auth / Redirects
# -------------------------
PHP_LOGIN_URL = "http://localhost/index.php"
PHP_LOGOUT_URL = "http://localhost/logout.php"


# -------------------------
# Database
# -------------------------
DB_CONFIG = {
    "host": "127.0.0.1",
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
    "reserved": "Reserved",
}

STATUS_CLASSES = {
    "available": "badge-available",
    "in-use": "badge-inuse",
    "maintenance": "badge-maintenance",
    "reserved": "badge-reserved",
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

# Rental request filter options shown to admin
RENTAL_REQUEST_FILTERS = ["Pending", "Approved", "Denied", "All"]

# -------------------------
# Session
# -------------------------
SESSION_COOKIE_NAME = "cat_session_token"
PHP_SESSION_PATH    = "D:/ics499/tmp" # Update this to match your xampp's tmp file path
PHPSESSID_COOKIE    = "PHPSESSID"

# -------------------------
# Roles
# -------------------------
ROLES       = ["admin", "faculty", "student"]
ADMIN_ROLES = ["admin"]
USER_ROLES  = ["faculty", "student"]