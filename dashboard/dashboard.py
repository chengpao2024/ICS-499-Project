#!D:/ics499/htdocs/.venv/Scripts/pythonw.exe
# =============================================================================
#  Campus Asset Tracker - Admin Dashboard (CGI Version)
#
#  File structure:
#    dashboard.py              <-Python logic only
#    templates/dashboard.html  <-HTML template
#    static/dashboard.css      <-styles
#    static/dashboard.js       <-client-side behaviour
# =============================================================================

# check filepath
import cgi
import cgitb
import os
import sys
import html
import io
import json
import mysql.connector
from mysql.connector import Error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
cgitb.enable()

import config

# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────
def get_db_connection():
    try:
        return mysql.connector.connect(**config.DB_CONFIG)
    except Error:
        return None


def redirect(url: str):
    print("Status: 302 Found")
    print(f"Location: {url}")
    print()
    sys.exit(0)


def json_response(data: dict):
    print("Content-Type: application/json; charset=utf-8")
    print()
    print(json.dumps(data))
    sys.exit(0)


# ─────────────────────────────────────────────
#  DATABASE QUERIES
# ─────────────────────────────────────────────
def get_asset_stats() -> dict:
    conn = get_db_connection()
    if conn is None:
        return {"total": 0, "available": 0, "in_use": 0, "maintenance": 0}
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                COUNT(*)                           AS total,
                SUM(asset_status = 'available')    AS available,
                SUM(asset_status = 'in-use')       AS in_use,
                SUM(asset_status = 'maintenance')  AS maintenance
            FROM assets
        """)
        row = cursor.fetchone()
        return {
            "total":       int(row["total"]       or 0),
            "available":   int(row["available"]   or 0),
            "in_use":      int(row["in_use"]       or 0),
            "maintenance": int(row["maintenance"] or 0),
        }
    except Error:
        return {"total": 0, "available": 0, "in_use": 0, "maintenance": 0}
    finally:
        try: cursor.close(); conn.close()
        except Exception: pass


def get_assets(search="", category="", status="",
               sort_by="asset_id", sort_dir="asc") -> list:
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor(dictionary=True)

        # Validate against whitelist before interpolating into SQL
        db_col = config.SORT_FIELDS.get(sort_by, "asset_id")
        db_dir = "DESC" if sort_dir == "desc" else "ASC"

        query = f"""
            SELECT
                asset_id,
                asset_name      AS name,
                asset_category  AS category,
                asset_serial    AS serial_number,
                asset_location  AS location,
                asset_status    AS status
            FROM assets
            WHERE 1=1
        """
        params = []
        if search:
            like = f"%{search}%"
            query  += " AND (asset_name LIKE %s OR asset_serial LIKE %s OR asset_location LIKE %s)"
            params += [like, like, like]
        if category and category != "All Categories":
            query += " AND asset_category = %s"
            params.append(category)
        if status and status != "All Statuses":
            query += " AND asset_status = %s"
            params.append(status)

        query += f" ORDER BY {db_col} {db_dir}"

        cursor.execute(query, params)
        return cursor.fetchall()
    except Error:
        return []
    finally:
        try: cursor.close(); conn.close()
        except Exception: pass


def delete_asset(asset_id: int) -> bool:
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assets WHERE asset_id = %s", (asset_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Error:
        return False
    finally:
        try: cursor.close(); conn.close()
        except Exception: pass


def update_asset_status(asset_id: int, new_status: str) -> bool:
    if new_status not in config.STATUSES:
        return False
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE assets SET asset_status = %s WHERE asset_id = %s",
            (new_status, asset_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Error:
        return False
    finally:
        try: cursor.close(); conn.close()
        except Exception: pass


def update_asset_field(asset_id: int, field: str, value: str) -> bool:
    """Inline edit — only whitelisted fields, rejects blank values."""
    if field not in config.EDITABLE_FIELDS:
        return False
    value = value.strip()
    if not value:
        return False
    db_col = config.EDITABLE_FIELDS[field]   # safe: from our own dict, not user input
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE assets SET {db_col} = %s WHERE asset_id = %s",
            (value, asset_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Error:
        return False
    finally:
        try: cursor.close(); conn.close()
        except Exception: pass


# ─────────────────────────────────────────────
#  HTML HELPERS
# ─────────────────────────────────────────────
def status_badge(asset_id: int, status: str) -> str:
    cls   = config.STATUS_CLASSES.get(status, "badge-default")
    label = config.STATUS_LABELS.get(status, status)
    return (
        f'<div class="status-cell" data-id="{asset_id}" data-status="{status}">'
        f'<span class="status-badge {cls} status-toggle">'
        f'{html.escape(label)}</span></div>'
    )


def build_rows(assets: list) -> str:
    if not assets:
        return """
        <tr>
          <td colspan="7" class="no-results">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 stroke-width="1.4" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0
                       0010.607 10.607z"/>
            </svg>
            No assets found.
          </td>
        </tr>"""

    rows = ""
    for a in assets:
        aid      = a['asset_id']
        name     = html.escape(str(a['name']))
        category = html.escape(str(a['category']))
        location = html.escape(str(a['location'] or ''))
        serial   = html.escape(str(a['serial_number']))
        # Safe for data-name attribute — escape quotes
        name_attr = html.escape(str(a['name']), quote=True)

        rows += f"""
        <tr id="row-{aid}">
          <td class="asset-id">{aid}</td>
          <td class="asset-name">
            <svg class="row-icon" xmlns="http://www.w3.org/2000/svg" fill="none"
                 viewBox="0 0 24 24" stroke-width="1.6" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0
                       0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25
                       2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25
                       0 003 5.25m18 0H3"/>
            </svg>
            <span class="editable" data-id="{aid}" data-field="name">{name}</span>
          </td>
          <td><span class="editable" data-id="{aid}" data-field="category">{category}</span></td>
          <td class="serial">{serial}</td>
          <td>{status_badge(aid, a['status'])}</td>
          <td><span class="editable" data-id="{aid}" data-field="location">{location}</span></td>
          <td class="td-kebab">
            <button class="btn-kebab" data-id="{aid}" data-name="{name_attr}"
                    data-edit-url="/public/asset_create.php?edit={aid}"
                    title="Actions">&#8942;</button>
          </td>
        </tr>"""
    return rows


def build_options(items: list, selected: str, label_map: dict = None) -> str:
    out = ""
    for item in items:
        label = label_map.get(item, item) if label_map else item
        sel   = 'selected' if item == selected else ''
        out  += f'<option value="{html.escape(item)}" {sel}>{html.escape(label)}</option>'
    return out


# ─────────────────────────────────────────────
#  TEMPLATE RENDERER
# ─────────────────────────────────────────────
def render_dashboard(user: dict, stats: dict, assets: list,
                     search: str, category: str, status: str,
                     categories: list, statuses: list,
                     sort_by: str, sort_dir: str,
                     script_url: str) -> str:
    template_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    with open(template_path, encoding="utf-8") as f:
        page = f.read()

    status_label_map = {"All Statuses": "All Statuses", **config.STATUS_LABELS}

    replacements = {
        "%SCRIPT_URL%":        script_url,
        "%USER_NAME%":         html.escape(user["user_name"]),
        "%STATS_TOTAL%":       str(stats["total"]),
        "%STATS_AVAILABLE%":   str(stats["available"]),
        "%STATS_IN_USE%":      str(stats["in_use"]),
        "%STATS_MAINTENANCE%": str(stats["maintenance"]),
        "%CAT_OPTIONS%":       build_options(categories, category),
        "%ST_OPTIONS%":        build_options(statuses, status, status_label_map),
        "%SEARCH_VALUE%":      html.escape(search),
        "%ROWS_HTML%":         build_rows(assets),
        "%ASSET_COUNT%":       str(len(assets)),
        "%SORT_BY%":           sort_by,
        "%SORT_ACTIVE_CLASS%":  "active" if sort_by != "asset_id" or sort_dir != "asc" else "",
        "%SORT_DIR%":          sort_dir,
    }

    for placeholder, value in replacements.items():
        page = page.replace(placeholder, value)

    return page


# ─────────────────────────────────────────────
#  MAIN CGI ENTRY POINT
# ─────────────────────────────────────────────
def main():
    form   = cgi.FieldStorage()
    method = os.environ.get("REQUEST_METHOD", "GET").upper()
    action = form.getvalue("action", "")

    script_url = os.environ.get("REQUEST_URI", "/dashboard/dashboard.py").split("?")[0]

    if action == "logout":
        redirect(config.PHP_LOGIN_URL)

    if action == "delete" and method == "GET":
        asset_id = form.getvalue("id", "")
        if asset_id.isdigit():
            delete_asset(int(asset_id))
        redirect(script_url)

    if action == "update_status" and method == "POST":
        asset_id   = form.getvalue("id",     "")
        new_status = form.getvalue("status", "")
        if asset_id.isdigit() and new_status in config.STATUSES:
            ok = update_asset_status(int(asset_id), new_status)
            if ok:
                json_response({
                    "success":     True,
                    "label":       config.STATUS_LABELS[new_status],
                    "badge_class": config.STATUS_CLASSES[new_status],
                })
            else:
                json_response({"success": False, "error": "DB update failed"})
        else:
            json_response({"success": False, "error": "Invalid parameters"})

    if action == "update_field" and method == "POST":
        asset_id = form.getvalue("id",    "")
        field    = form.getvalue("field", "")
        value    = form.getvalue("value", "")
        if asset_id.isdigit() and field in config.EDITABLE_FIELDS:
            ok = update_asset_field(int(asset_id), field, value)
            if ok:
                json_response({"success": True,  "value": value.strip()})
            else:
                json_response({"success": False, "error": "Update failed"})
        else:
            json_response({"success": False, "error": "Invalid parameters"})

    # Normal page render
    search   = form.getvalue("search",   "")
    category = form.getvalue("category", "All Categories")
    status   = form.getvalue("status",   "All Statuses")
    sort_by  = form.getvalue("sort_by",  "asset_id")
    sort_dir = form.getvalue("sort_dir", "asc")

    if sort_by  not in config.SORT_FIELDS: sort_by  = "asset_id"
    if sort_dir not in ["asc", "desc"]: sort_dir = "asc"

    user = {"user_name": "Admin", "user_email": "admin@metrostate.edu", "role": "admin"}

    stats      = get_asset_stats()
    assets     = get_assets(search, category, status, sort_by, sort_dir)
    categories = config.DEFAULT_CATEGORIES
    statuses = config.DEFAULT_STATUSES

    page = render_dashboard(user, stats, assets, search, category, status,
                            categories, statuses, sort_by, sort_dir, script_url)

    print("Content-Type: text/html; charset=utf-8")
    print()
    print(page)


if __name__ == "__main__":
    main()