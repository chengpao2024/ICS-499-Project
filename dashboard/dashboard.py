#!D:/ics499/htdocs/.venv/Scripts/pythonw.exe
# =============================================================================
#  Campus Asset Tracker — Dashboard CGI Entry Point
#
#  This file is intentionally thin: routing, auth guard, template render.
#  All business logic lives in the modules below:
#
#    auth/session.py       → SessionResolver   (who is logged in?)
#    models/asset.py       → Asset             (DB queries for assets)
#    models/rental.py      → Rental            (DB queries for rentals)
#    views/html_builder.py → HtmlBuilder       (HTML fragment generation)
# =============================================================================

import cgi
import cgitb
import os
import sys
import html
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
cgitb.enable(display=0, logdir="D:/ics499/tmp")

import config
from auth.session       import SessionResolver
from models.asset       import Asset
from models.rental      import Rental
from views.html_builder import HtmlBuilder


#  HTTP UTILITIES
def redirect(url: str):
    print(f"Status: 302 Found\nLocation: {url}\n")
    sys.exit(0)


def json_response(data: dict):
    print("Content-Type: application/json; charset=utf-8\n")
    print(json.dumps(data))
    sys.exit(0)


def is_admin(user) -> bool:
    return user is not None and user.get("role") in config.ADMIN_ROLES


#  TEMPLATE RENDERING
def _load_template(name: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "templates", name)
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _apply(page: str, replacements: dict) -> str:
    for k, v in replacements.items():
        page = page.replace(k, v)
    return page


def render_admin(user, form, script_url: str) -> str:
    from datetime import datetime
 
    view       = form.getvalue("view",       "inventory")
    search     = form.getvalue("search",     "")
    category   = form.getvalue("category",   "All Categories")
    status     = form.getvalue("status",     "All Statuses")
    sort_by    = form.getvalue("sort_by",    "asset_id")
    sort_dir   = form.getvalue("sort_dir",   "asc")
    req_filter = form.getvalue("req_filter", "Pending")
 
    if sort_by  not in config.SORT_FIELDS:                     sort_by  = "asset_id"
    if sort_dir not in ("asc", "desc"):                        sort_dir = "asc"
    if view     not in ("inventory", "rentals", "summary"):    view     = "inventory"  # ← added "summary"
 
    # Always needed (stat cards, navbar)
    stats        = Asset.get_stats()
    rental_stats = Rental.get_admin_stats()
    status_map   = {"All Statuses": "All Statuses", **config.STATUS_LABELS}
 
    # Inventory view data
    assets      = Asset.get_list(search, category, status, sort_by, sort_dir) \
                  if view == "inventory" else []
 
    # Rentals view data
    rental_reqs  = Rental.get_requests(None, req_filter) if view == "rentals" else []
    active_rents = Rental.get_active(None)               if view == "rentals" else []
 
    # Summary view data
    summary_html = ""
    if view == "summary":
        all_requests       = Rental.get_requests(None, "All")
        summary_rentals    = Rental.get_active(None)
        in_use_assets      = Asset.get_by_status("in-use")
        maintenance_assets = Asset.get_by_status("maintenance")
        other_assets       = Asset.get_other_status_assets()
        timeline           = Asset.get_timeline()
 
        # Tally request statuses in Python (no extra DB round-trip)
        req_counts = {"Pending": 0, "Approved": 0, "Denied": 0}
        for r in all_requests:
            s = str(r.get("request_status", ""))
            if s in req_counts:
                req_counts[s] += 1
 
        summary_data = {
            "stats":              stats,
            "in_use_assets":      in_use_assets,
            "active_rentals":     summary_rentals,
            "maintenance_assets": maintenance_assets,
            "other_assets":       other_assets,
            "all_requests":       all_requests,
            "req_counts":         req_counts,
            "timeline":           timeline,
            "generated_at":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        summary_html = HtmlBuilder.summary_html(summary_data)
 
    return _apply(_load_template("dashboard_admin.html"), {
        "%SCRIPT_URL%":          script_url,
        "%USER_NAME%":           html.escape(user["display_name"]),
        "%STATS_TOTAL%":         str(stats["total"]),
        "%STATS_AVAILABLE%":     str(stats["available"]),
        "%STATS_IN_USE%":        str(stats["in_use"]),
        "%STATS_MAINTENANCE%":   str(stats["maintenance"]),
        "%STATS_RENTED%":        str(stats.get("rented", 0)),
        "%CAT_OPTIONS%":         HtmlBuilder.options(config.DEFAULT_CATEGORIES, category),
        "%ST_OPTIONS%":          HtmlBuilder.options(config.DEFAULT_STATUSES, status, status_map),
        "%SEARCH_VALUE%":        html.escape(search),
        "%ROWS_HTML%":           HtmlBuilder.asset_rows(assets, "admin"),
        "%ASSET_COUNT%":         str(len(assets)),
        "%SORT_BY%":             sort_by,
        "%SORT_ACTIVE_CLASS%":   "active" if sort_by != "asset_id" or sort_dir != "asc" else "",
        "%SORT_DIR%":            sort_dir,
        "%PENDING_REQUESTS%":    str(rental_stats["pending_requests"]),
        "%ACTIVE_RENTALS%":      str(rental_stats["active_rentals"]),
        "%OVERDUE_RENTALS%":     str(rental_stats["overdue"]),
        "%REQ_FILTER%":          req_filter,
        "%RENTAL_REQUEST_ROWS%": HtmlBuilder.rental_request_rows(rental_reqs, "admin"),
        "%ACTIVE_RENTAL_ROWS%":  HtmlBuilder.active_rental_rows(active_rents, "admin"),
        # ── View visibility ──
        "%INV_ACTIVE%":          "active" if view == "inventory" else "",
        "%RENT_ACTIVE%":         "active" if view == "rentals"   else "",
        "%SUMM_ACTIVE%":         "active" if view == "summary"   else "",   # ← new
        "%INV_HIDDEN%":          "" if view == "inventory" else 'style="display:none"',
        "%RENT_HIDDEN%":         "" if view == "rentals"   else 'style="display:none"',
        "%SUMM_HIDDEN%":         "" if view == "summary"   else 'style="display:none"', # ← new
        # ── Rental request filter tabs ──
        "%RF_PENDING_ACTIVE%":   "active" if req_filter == "Pending"  else "",
        "%RF_APPROVED_ACTIVE%":  "active" if req_filter == "Approved" else "",
        "%RF_DENIED_ACTIVE%":    "active" if req_filter == "Denied"   else "",
        "%RF_ALL_ACTIVE%":       "active" if req_filter == "All"      else "",
        "%VIEW%":                view,
        # ── Summary ──
        "%SUMMARY_HTML%":        summary_html,                               # ← new
    })


def render_user(user, form, script_url: str) -> str:
    view     = form.getvalue("view",     "available")
    search   = form.getvalue("search",   "")
    category = form.getvalue("category", "All Categories")

    if view not in ("available", "my_requests", "my_rentals"):
        view = "available"

    dept         = user.get("department", "")
    stats        = Rental.get_user_stats(user)
    available    = Asset.get_list(search=search, category=category,
                                  status="available", department=dept) \
                   if view == "available" else []
    rental_reqs  = Rental.get_requests(user, "All") if view == "my_requests" else []
    active_rents = Rental.get_active(user)          if view == "my_rentals"  else []

    role_label = "Faculty" if user["role"] == "faculty" else "Student"
    dept_note  = f" · {dept}" if dept else ""

    return _apply(_load_template("dashboard_user.html"), {
        "%SCRIPT_URL%":      script_url,
        "%USER_NAME%":       html.escape(user["display_name"]),
        "%USER_ROLE%":       role_label,
        "%DEPT_NOTE%":       html.escape(dept_note),
        "%STATS_AVAILABLE%": str(stats["available"]),
        "%STATS_ACTIVE%":    str(stats["active_rentals"]),
        "%STATS_PENDING%":   str(stats["pending_requests"]),
        "%AVAILABLE_ROWS%":  HtmlBuilder.asset_rows(available, user["role"]),
        "%AVAILABLE_COUNT%": str(len(available)),
        "%REQUEST_ROWS%":    HtmlBuilder.rental_request_rows(rental_reqs, user["role"]),
        "%RENTAL_ROWS%":     HtmlBuilder.active_rental_rows(active_rents, user["role"]),
        "%CAT_OPTIONS%":     HtmlBuilder.options(config.DEFAULT_CATEGORIES, category),
        "%SEARCH_VALUE%":    html.escape(search),
        "%VIEW%":            view,
        "%AVAIL_ACTIVE%":    "active" if view == "available"   else "",
        "%REQ_ACTIVE%":      "active" if view == "my_requests" else "",
        "%RENT_ACTIVE%":     "active" if view == "my_rentals"  else "",
        "%AVAIL_HIDDEN%":    "" if view == "available"   else 'style="display:none"',
        "%REQ_HIDDEN%":      "" if view == "my_requests" else 'style="display:none"',
        "%RENT_HIDDEN%":     "" if view == "my_rentals"  else 'style="display:none"',
    })


#  MAIN — CGI ROUTER
def main():
    form       = cgi.FieldStorage()
    method     = os.environ.get("REQUEST_METHOD", "GET").upper()
    action     = form.getvalue("action", "")
    script_url = os.environ.get("REQUEST_URI", "/dashboard/dashboard.py").split("?")[0]

    if action == "logout":
        response = (
            "Status: 302 Found\r\n"
            f"Location: {config.PHP_LOGOUT_URL}\r\n"
            f"Set-Cookie: {config.SESSION_COOKIE_NAME}=; "
            "expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; HttpOnly; SameSite=Lax\r\n"
            "\r\n"
        ).encode("ascii")
        sys.stdout.buffer.write(response)
        sys.stdout.buffer.flush()
        sys.exit(0)

    user = SessionResolver.get_current_user()
    if user is None:
        redirect(config.PHP_LOGIN_URL)

    role = user["role"]

    # Admin-only AJAX endpoints
    if action in ("delete", "update_status", "update_field",
                  "approve_request", "deny_request"):
        if not is_admin(user):
            json_response({"success": False, "error": "Forbidden"})

    if action == "delete" and method == "GET":
        asset_id = form.getvalue("id", "")
        if asset_id.isdigit():
            Asset.delete(int(asset_id))
        redirect(script_url)

    if action == "update_status" and method == "POST":
        asset_id, new_status = form.getvalue("id",""), form.getvalue("status","")
        if asset_id.isdigit() and new_status in config.STATUSES:
            ok = Asset.update_status(int(asset_id), new_status)
            json_response({"success": True,
                           "label": config.STATUS_LABELS[new_status],
                           "badge_class": config.STATUS_CLASSES[new_status]} if ok
                          else {"success": False, "error": "DB update failed"})
        json_response({"success": False, "error": "Invalid parameters"})

    if action == "update_field" and method == "POST":
        asset_id = form.getvalue("id","")
        field    = form.getvalue("field","")
        value    = form.getvalue("value","")
        if asset_id.isdigit() and field in config.EDITABLE_FIELDS:
            ok = Asset.update_field(int(asset_id), field, value)
            json_response({"success": True, "value": value.strip()} if ok
                          else {"success": False, "error": "Update failed"})
        json_response({"success": False, "error": "Invalid parameters"})

    if action == "approve_request" and method == "POST":
        req_id = form.getvalue("id","")
        if req_id.isdigit():
            ok = Rental.approve(int(req_id))
            json_response({"success": ok})
        json_response({"success": False, "error": "Invalid ID"})

    if action == "deny_request" and method == "POST":
        req_id = form.getvalue("id","")
        if req_id.isdigit():
            ok = Rental.deny(int(req_id))
            json_response({"success": ok})
        json_response({"success": False, "error": "Invalid ID"})

    # Faculty / Student AJAX
    if action == "request_rental" and method == "POST":
        if role not in config.USER_ROLES:
            json_response({"success": False, "error": "Forbidden"})
        asset_id   = form.getvalue("asset_id",  "")
        start_date = form.getvalue("start_date","").strip()
        due_date   = form.getvalue("due_date",  "").strip()
        if not asset_id.isdigit() or not start_date or not due_date:
            json_response({"success": False, "error": "Missing required fields"})
        ok, result = Rental.create_request(user, int(asset_id), start_date, due_date)
        json_response({"success": True, "request_id": result} if ok
                      else {"success": False, "error": result})


    # return_rental — available to all authenticated users
    # faculty/student can only return their own; admin can return any
    if action == "return_rental" and method == "POST":
        rental_id = form.getvalue("id", "")
        if not rental_id.isdigit():
            json_response({"success": False, "error": "Invalid rental ID"})
        acting_user = None if is_admin(user) else user
        ok, error = Rental.return_rental(int(rental_id), acting_user)
        json_response({"success": True} if ok
                      else {"success": False, "error": error})

    # Page renders
    page = render_admin(user, form, script_url) if is_admin(user) \
           else render_user(user, form, script_url)

    print("Content-Type: text/html; charset=utf-8\n")
    print(page)


if __name__ == "__main__":
    print("Content-Type: text/html; charset=utf-8\n")
    main()