C:\Users\Nora\AppData\Local\Microsoft\WindowsApps\python.exe
# =============================================================================
#  Campus Asset Tracker – Admin Dashboard (CGI Version)
#  Runs directly under Apache/XAMPP via mod_cgi.
#
#  URL:  http://localhost/dashboard/dashboard.py
#        http://localhost/dashboard/          (with .htaccess clean URL)
#
#  Auth: Reads the cat_session_token cookie, validates it against the
#        shared MySQL php_sessions table that PHP writes on login.
#
#  NOTE: If Apache cannot find Python via the shebang above, replace the
#        first line with the explicit path to your Python install, e.g.:
#        #!C:/Python312/python.exe
#        Run `where python` in a terminal to find yours.
# =============================================================================

import cgi
import cgitb
import os

import sys
# Fix Windows CGI encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import html
import mysql.connector
from mysql.connector import Error

# Show detailed tracebacks in the browser during development.
# DISABLE THIS IN PRODUCTION by removing or commenting it out.
cgitb.enable()

# Will need to configure this for our db later
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",               # default XAMPP blank password
    "database": "campus_asset_tracker",
    "port":     3306
}

PHP_LOGIN_URL = "http://localhost/index.php"   # login page
SESSION_COOKIE_NAME = "cat_session_token"



#  HELPERS
def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        return None


def get_token(form) -> str | None:
    """Read token from URL query string (?token=...) or hidden form field."""
    return form.getvalue("token", None)


def redirect(url: str):
    """Emit an HTTP redirect and exit immediately."""
    print(f"Status: 302 Found")
    print(f"Location: {url}")
    print()   # blank line = end of headers
    sys.exit(0)


def validate_session(token: str) -> dict | None:
    """
    Validates token against the php_sessions table written by index.php.
    Returns user dict if valid and not expired, None otherwise.
    """
    if not token:
        return None

    conn = get_db_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT user_id, user_email, user_name, role
            FROM   php_sessions
            WHERE  token = %s
              AND  expires_at > NOW()
            LIMIT  1
            """,
            (token,)
        )
        return cursor.fetchone()
    except Error:
        return None
    finally:
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass


#  PLACEHOLDER DATA  (replace with DB queries later)
def get_asset_stats() -> dict:
    """
    TODO: Replace with real DB query when schema is ready.

    Uncomment the block below and remove the placeholder return:

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('''
        SELECT
            COUNT(*)                                AS total,
            SUM(status = "Available")               AS available,
            SUM(status = "In Use")                  AS in_use,
            SUM(status = "Under Maintenance")       AS maintenance
        FROM assets
    ''')
    row = cursor.fetchone()
    cursor.close(); conn.close()
    return row
    """
    return {"total": 12, "available": 6, "in_use": 3, "maintenance": 1}


def get_assets(search="", category="", status="") -> list:
    """
    TODO: Replace with real DB query when schema is ready.

    Uncomment the block below and remove the placeholder list:

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query  = "SELECT * FROM assets WHERE 1=1"
    params = []
    if search:
        like = f"%{search}%"
        query  += " AND (name LIKE %s OR asset_id LIKE %s OR serial_number LIKE %s OR location LIKE %s)"
        params += [like, like, like, like]
    if category and category != "All Categories":
        query += " AND category = %s"; params.append(category)
    if status and status != "All Statuses":
        query += " AND status = %s";   params.append(status)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows
    """
    placeholder = [
        {"asset_id": "A001", "name": "Dell Latitude 5520 Laptop",   "category": "IT Equipment",    "serial_number": "DL5520-2024-001",  "status": "Available",         "location": "IT Lab – Building A, Room 201",         "assigned_to": None},
        {"asset_id": "A002", "name": "HP ProDesk 600 Desktop",      "category": "IT Equipment",    "serial_number": "HP600-2023-045",   "status": "In Use",            "location": "Computer Lab – Building B, Room 105",   "assigned_to": "Dr. Sarah Johnson"},
        {"asset_id": "A003", "name": "Epson PowerLite Projector",   "category": "AV Equipment",    "serial_number": "EP-PL-2022-012",   "status": "Available",         "location": "Media Room – Building C",               "assigned_to": None},
        {"asset_id": "A004", "name": "iPad Pro 12.9\" (6th Gen)",   "category": "IT Equipment",    "serial_number": "IPAD-2024-008",    "status": "In Use",            "location": "Library – Main Floor",                  "assigned_to": "Marcus Lee"},
        {"asset_id": "A005", "name": "Logitech Conference Camera",  "category": "AV Equipment",    "serial_number": "LGT-CAM-2023-003", "status": "Under Maintenance", "location": "Conference Room 2A",                    "assigned_to": None},
        {"asset_id": "A006", "name": "Canon EOS R50 Camera",        "category": "Media Equipment", "serial_number": "CNON-R50-2024-002","status": "Available",         "location": "Media Checkout – Building D",           "assigned_to": None},
    ]
    filtered = placeholder
    if search:
        s = search.lower()
        filtered = [a for a in filtered if
                    s in a["asset_id"].lower() or s in a["name"].lower() or
                    s in a["serial_number"].lower() or s in (a["location"] or "").lower()]
    if category and category != "All Categories":
        filtered = [a for a in filtered if a["category"] == category]
    if status and status != "All Statuses":
        filtered = [a for a in filtered if a["status"] == status]
    return filtered


# LOGOUT ACTION
def handle_logout(token: str):
    # Token handling is there, not using at the moment
    """
    Delete token from MySQL (invalidates Python session),
    expire the cookie, then redirect to PHP login page.
    PHP session itself is destroyed by logout.php if user
    came from there — or expires naturally otherwise.
    """
    if token:
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM php_sessions WHERE token = %s", (token,))
                conn.commit()
            except Error:
                pass
            finally:
                try: cursor.close(); conn.close()
                except Exception: pass

    print("Status: 302 Found")
    print(f"Location: {PHP_LOGIN_URL}")
    # Expire the cookie immediately
    print("Set-Cookie: cat_session_token=; Max-Age=0; Path=/; HttpOnly; SameSite=Lax")
    print()
    sys.exit(0)


#  HTML RENDERING
def status_badge(status: str) -> str:
    classes = {
        "Available":         "badge-available",
        "In Use":            "badge-inuse",
        "Under Maintenance": "badge-maintenance",
    }
    cls = classes.get(status, "badge-default")
    return f'<span class="status-badge {cls}">{html.escape(status)}</span>'


def render_dashboard(user: dict, stats: dict, assets: list,
                     search: str, category: str, status: str,
                     categories: list, statuses: list) -> str:
    """Build and return the full dashboard HTML string."""

    #  Asset table rows 
    if assets:
        rows_html = ""
        for a in assets:
            assigned = html.escape(a["assigned_to"]) if a["assigned_to"] else "–"
            rows_html += f"""
        <tr>
          <td class="asset-id">{html.escape(a['asset_id'])}</td>
          <td class="asset-name">
            <svg class="row-icon" xmlns="http://www.w3.org/2000/svg" fill="none"
                 viewBox="0 0 24 24" stroke-width="1.6" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0
                       0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25
                       2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25
                       0 003 5.25m18 0H3"/>
            </svg>
            {html.escape(a['name'])}
          </td>
          <td>{html.escape(a['category'])}</td>
          <td class="serial">{html.escape(a['serial_number'])}</td>
          <td>{status_badge(a['status'])}</td>
          <td>{html.escape(a['location'])}</td>
          <td>{assigned}</td>
          <td>
            <button class="btn-view" disabled title="Detail view coming soon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                   stroke-width="1.8" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5
                         12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0
                         .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007
                         -9.963-7.178z"/>
                <path stroke-linecap="round" stroke-linejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              View
            </button>
          </td>
        </tr>"""
    else:
        rows_html = """
        <tr>
          <td colspan="8" class="no-results">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 stroke-width="1.4" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0
                       0010.607 10.607z"/>
            </svg>
            No assets found matching your search.
          </td>
        </tr>"""

    # Category options 
    cat_options = "".join(
        f'<option value="{html.escape(c)}" {"selected" if category == c else ""}>'
        f'{html.escape(c)}</option>'
        for c in categories
    )

    # Status options
    st_options = "".join(
        f'<option value="{html.escape(s)}" {"selected" if status == s else ""}>'
        f'{html.escape(s)}</option>'
        for s in statuses
    )

    # Current script URL (works regardless of clean-URL rewriting)
    script_url = os.environ.get("REQUEST_URI", "/dashboard/dashboard.py").split("?")[0]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Campus Asset Tracker – Inventory</title>
  <link rel="stylesheet" href="/dashboard/static/dashboard.css"/>
</head>
<body>

  <!-- ═══════ NAVBAR ═══════ -->
  <nav class="navbar">
    <div class="nav-brand">
      <div class="brand-icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
             stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9
                   5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9"/>
        </svg>
      </div>
      <div class="brand-text">
        <span class="brand-title">Campus Asset Tracker</span>
        <span class="brand-sub">IT Management Portal</span>
      </div>
    </div>

    <div class="nav-links">
      <a href="{script_url}" class="nav-link active">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
             stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247
                   2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10
                   11.25h4M3.375 7.5h17.25c.621 0 1.125-.504
                   1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375
                   c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z"/>
        </svg>
        Inventory
      </a>
      <a href="#" class="nav-link" title="Coming soon – separate page">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
             stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0
                   012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18
                   0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021
                   18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25
                   2.25 0 0121 11.25v7.5"/>
        </svg>
        Rental Management
      </a>
    </div>

    <div class="nav-right">
      <span class="nav-user">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
             stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M17.982 18.725A7.488 7.488 0 0012 15.75a7.488 7.488
                   0 00-5.982 2.975m11.963 0a9 9 0 10-11.963 0m11.963
                   0A8.966 8.966 0 0112 21a8.966 8.966 0
                   01-5.982-2.275M15 9.75a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        {html.escape(user['user_name'])}
      </span>
      <a href="{script_url}?action=logout" class="btn-logout">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
             stroke-width="1.8" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round"
                d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0
                   00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25
                   0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9"/>
        </svg>
        Logout
      </a>
    </div>
  </nav>

  <!-- ═══════ MAIN CONTENT ═══════ -->
  <main class="main-content">

    <div class="page-header">
      <div>
        <h1 class="page-title">Asset Inventory</h1>
        <p class="page-subtitle">Track and manage all campus assets</p>
      </div>
      <button class="btn-primary" disabled title="Feature coming soon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
             stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        Add New Asset
      </button>
    </div>

    <!-- Stat Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <p class="stat-label">Total Assets</p>
        <div class="stat-value-row">
          <svg class="stat-icon icon-blue" xmlns="http://www.w3.org/2000/svg"
               fill="none" viewBox="0 0 24 24" stroke-width="1.6" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round"
                  d="M21 7.5l-9-5.25L3 7.5m18 0l-9 5.25m9-5.25v9l-9
                     5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9"/>
          </svg>
          <span class="stat-number">{stats['total']}</span>
        </div>
      </div>
      <div class="stat-card">
        <p class="stat-label">Available</p>
        <div class="stat-value-row">
          <span class="status-dot dot-green"></span>
          <span class="stat-number">{stats['available']}</span>
        </div>
      </div>
      <div class="stat-card">
        <p class="stat-label">In Use</p>
        <div class="stat-value-row">
          <span class="status-dot dot-blue"></span>
          <span class="stat-number">{stats['in_use']}</span>
        </div>
      </div>
      <div class="stat-card">
        <p class="stat-label">Under Maintenance</p>
        <div class="stat-value-row">
          <span class="status-dot dot-amber"></span>
          <span class="stat-number">{stats['maintenance']}</span>
        </div>
      </div>
    </div>

    <!-- Asset Table Panel -->
    <div class="panel">
      <h2 class="panel-title">All Assets</h2>

      <form method="GET" action="{script_url}" class="filters-bar" id="filter-form">
        <div class="search-wrapper">
          <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" fill="none"
               viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round"
                  d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0
                     0010.607 10.607z"/>
          </svg>
          <input type="text" name="search" id="search" class="search-input"
                 placeholder="Search by name, ID, serial number, or location..."
                 value="{html.escape(search)}" autocomplete="off"/>
        </div>
        <select name="category" class="filter-select" onchange="this.form.submit()">
          {cat_options}
        </select>
        <select name="status" class="filter-select" onchange="this.form.submit()">
          {st_options}
        </select>
      </form>

      <div class="table-wrapper">
        <table class="asset-table">
          <thead>
            <tr>
              <th>Asset ID <span class="sort-icon">↕</span></th>
              <th>Name <span class="sort-icon">↕</span></th>
              <th>Category <span class="sort-icon">↕</span></th>
              <th>Serial Number</th>
              <th>Status <span class="sort-icon">↕</span></th>
              <th>Location</th>
              <th>Assigned To</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </div>

      <p class="row-count">
        Showing <strong>{len(assets)}</strong> of <strong>{stats['total']}</strong> assets
      </p>
    </div>

  </main>

  <script>
    const searchInput = document.getElementById('search');
    let debounceTimer;
    searchInput.addEventListener('input', () => {{
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {{
        document.getElementById('filter-form').submit();
      }}, 400);
    }});
  </script>

</body>
</html>"""


#  MAIN CGI ENTRY POINT. This is what gets called from Apache
def main():
    form     = cgi.FieldStorage()
    action   = form.getvalue("action",   "")
    search   = form.getvalue("search",   "")
    category = form.getvalue("category", "All Categories")
    status   = form.getvalue("status",   "All Statuses")

    if action == "logout":
        redirect(PHP_LOGIN_URL)

    user = {"user_name": "Admin", "user_email": "admin@metrostate.edu", "role": "admin"}

    stats      = get_asset_stats()
    assets     = get_assets(search, category, status)
    categories = ["All Categories", "IT Equipment", "AV Equipment", "Media Equipment", "Furniture"]
    statuses   = ["All Statuses",   "Available",    "In Use",       "Under Maintenance"]

    page = render_dashboard(user, stats, assets, search, category, status, categories, statuses)

    print("Content-Type: text/html; charset=utf-8")
    print()
    print(page)


if __name__ == "__main__":
    main()