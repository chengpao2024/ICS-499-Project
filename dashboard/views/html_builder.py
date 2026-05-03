# views/html_builder.py
# Generates all HTML fragments injected into templates.
# Nothing here touches the DB or HTTP — pure presentation logic.

import html
from datetime import datetime
import config


class HtmlBuilder:

    # Status badges
    @staticmethod
    def status_badge_interactive(asset_id: int, status: str) -> str:
        """Clickable badge — admin only."""
        cls   = config.STATUS_CLASSES.get(status, "badge-default")
        label = config.STATUS_LABELS.get(status, status)
        return (
            f'<div class="status-cell" data-id="{asset_id}" data-status="{status}">'
            f'<span class="status-badge {cls} status-toggle">{html.escape(label)}</span>'
            f'</div>'
        )

    @staticmethod
    def status_badge_static(status: str) -> str:
        """Read-only badge — faculty / student."""
        cls   = config.STATUS_CLASSES.get(status, "badge-default")
        label = config.STATUS_LABELS.get(status, status)
        return f'<span class="status-badge {cls}">{html.escape(label)}</span>'

    @staticmethod
    def request_status_badge(status: str) -> str:
        cls_map = {"Pending": "badge-maintenance",
                   "Approved": "badge-available",
                   "Denied": "badge-default"}
        return f'<span class="status-badge {cls_map.get(status,"badge-default")}">{html.escape(status)}</span>'

    @staticmethod
    def rental_status_badge(status: str) -> str:
        cls_map = {"Active": "badge-inuse", "Returned": "badge-available",
                   "Late": "badge-maintenance"}
        return f'<span class="status-badge {cls_map.get(status,"badge-default")}">{html.escape(status)}</span>'

    # Asset table rows
    @classmethod
    def asset_rows(cls, assets: list, role: str = "admin") -> str:
        if not assets:
            return cls._empty_row(7)

        rows = ""
        for a in assets:
            aid       = a["asset_id"]
            name      = html.escape(str(a["name"]))
            category  = html.escape(str(a["category"]))
            location  = html.escape(str(a["location"] or ""))
            serial    = html.escape(str(a["serial_number"]))
            name_attr = html.escape(str(a["name"]), quote=True)

            if role == "admin":
                status_cell = cls.status_badge_interactive(aid, a["status"])
                name_cell   = f'<span class="editable" data-id="{aid}" data-field="name">{name}</span>'
                cat_cell    = f'<span class="editable" data-id="{aid}" data-field="category">{category}</span>'
                loc_cell    = f'<span class="editable" data-id="{aid}" data-field="location">{location}</span>'
                action_cell = cls._kebab_cell(aid, name_attr)
            else:
                status_cell = cls.status_badge_static(a["status"])
                name_cell   = name
                cat_cell    = category
                loc_cell    = location
                action_cell = cls._rent_button_cell(aid, name_attr)

            rows += f"""
        <tr id="row-{aid}">
          <td class="asset-id">{aid}</td>
          <td class="asset-name">
            <svg class="row-icon" xmlns="http://www.w3.org/2000/svg" fill="none"
                 viewBox="0 0 24 24" stroke-width="1.6" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3
                       3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25
                       2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0
                       0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0H3"/>
            </svg>
            {name_cell}
          </td>
          <td>{cat_cell}</td>
          <td class="serial">{serial}</td>
          <td>{status_cell}</td>
          <td>{loc_cell}</td>
          {action_cell}
        </tr>"""
        return rows

    # Rental request rows
    @classmethod
    def rental_request_rows(cls, requests: list, role: str = "admin") -> str:
        cols = 7 if role == "admin" else 6
        if not requests:
            return cls._empty_row(cols, "No rental requests found.")
        rows = ""
        for r in requests:
            req_id = r["request_id"]
            asset  = html.escape(str(r["asset_name"]))
            cat    = html.escape(str(r["asset_category"]))
            start  = str(r["requested_start"])[:10] if r["requested_start"] else "—"
            due    = str(r["requested_due"])[:10]   if r["requested_due"]   else "—"
            badge  = cls.request_status_badge(str(r["request_status"]))

            if role == "admin":
                requester = html.escape(str(r.get("requester_name", "—")))
                r_role    = html.escape(str(r.get("requester_role", "")))
                action    = (
                    f'<button class="btn-approve" onclick="approveRequest({req_id})">Approve</button>'
                    f'<button class="btn-deny"    onclick="denyRequest({req_id})">Deny</button>'
                ) if r["request_status"] == "Pending" else badge
                rows += f"""
            <tr>
              <td class="asset-id">{req_id}</td><td>{asset}</td><td>{cat}</td>
              <td>{requester} <small class="role-hint">({r_role})</small></td>
              <td>{start}</td><td>{due}</td>
              <td class="td-actions">{action}</td>
            </tr>"""
            else:
                rows += f"""
            <tr>
              <td class="asset-id">{req_id}</td><td>{asset}</td><td>{cat}</td>
              <td>{start}</td><td>{due}</td><td>{badge}</td>
            </tr>"""
        return rows

    # Active rental rows
    @classmethod
    def active_rental_rows(cls, rentals: list, role: str = "admin") -> str:
        # Columns: Rental# | Asset | [Rented By - admin only] | Start | Due | Status | Action
        cols = 7 if role == "admin" else 6
        if not rentals:
            return cls._empty_row(cols, "No active rentals found.")
        rows = ""
        for r in rentals:
            rental_id  = r["rental_id"]
            asset      = html.escape(str(r["asset_name"]))
            start      = str(r["rental_start"])[:10] if r["rental_start"] else "—"
            due        = str(r["rental_due"])[:10]   if r["rental_due"]   else "—"
            status     = str(r["rental_status"])
            badge      = cls.rental_status_badge(status)
            renter_col = (
                f'<td>{html.escape(str(r.get("renter_name", "—")))}</td>'
                if role == "admin" else ""
            )

            # Return button — only shown when rental is still active/late
            if status in ("Active", "Late"):
                action_cell = (
                    f'<td class="td-actions">'
                    f'<button class="btn-return" onclick="returnRental({rental_id})">'
                    f'Return Item</button></td>'
                )
            else:
                # Already returned — show the badge, no button
                action_cell = f'<td>{badge}</td>'

            rows += f"""
        <tr id="rental-row-{rental_id}">
          <td class="asset-id">{rental_id}</td>
          <td>{asset}</td>{renter_col}
          <td>{start}</td><td>{due}</td>
          <td>{badge}</td>
          {action_cell}
        </tr>"""
        return rows

    # Select option lists
    @staticmethod
    def options(items: list, selected: str, label_map: dict = None) -> str:
        out = ""
        for item in items:
            label = label_map.get(item, item) if label_map else item
            sel   = "selected" if item == selected else ""
            out  += f'<option value="{html.escape(item)}" {sel}>{html.escape(label)}</option>'
        return out

    # Private helpers
    @staticmethod
    def _empty_row(colspan: int, msg: str = "No assets found.") -> str:
        return f"""
        <tr>
          <td colspan="{colspan}" class="no-results">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 width="24" height="24" stroke-width="1.4" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5
                       7.5 0 0010.607 10.607z"/>
            </svg>
            {msg}
          </td>
        </tr>"""

    @staticmethod
    def _kebab_cell(aid: int, name_attr: str) -> str:
        return f"""
          <td class="td-kebab">
            <button class="btn-kebab" data-id="{aid}" data-name="{name_attr}"
                    data-edit-url="/public/asset_create.php?edit={aid}"
                    title="Actions">&#8942;</button>
          </td>"""

    @staticmethod
    def _rent_button_cell(aid: int, name_attr: str) -> str:
        return f"""
          <td class="td-action">
            <button class="btn-rent"
                    data-id="{aid}" data-name="{name_attr}"
                    onclick="openRentModal({aid}, '{name_attr}')">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none"
                   viewBox="0 0 24 24" width="13" height="13"
                   stroke-width="2" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round"
                      d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383
                         1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218
                         c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0
                         00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75
                         0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0
                         11-1.5 0 .75.75 0 011.5 0z"/>
              </svg>
              Request Rental
            </button>
          </td>"""
    
    @classmethod
    def summary_html(cls, data: dict) -> str:
        """
        Render the complete Summary tab body as a single HTML string.
 
        Expected keys in `data`:
            stats               dict  – from Asset.get_stats()
            in_use_assets       list  – assets with status 'in-use'
            active_rentals      list  – rental records (with renter_name / due dates)
            maintenance_assets  list  – assets with status 'maintenance'
            other_assets        list  – non-standard status assets
            all_requests        list  – every rental request (all statuses)
            req_counts          dict  – {"Pending": n, "Approved": n, "Denied": n}
            timeline            list  – may be [] if date columns are absent
            generated_at        str   – ISO timestamp string
        """
        from datetime import datetime
        now    = datetime.now()
        stats  = data.get("stats", {})
        out    = []
 
        # Generated-at banner
        gen_ts = data.get("generated_at", now.strftime("%Y-%m-%d %H:%M:%S"))
        out.append(f"""
        <div class="summ-header-bar">
          <div class="summ-header-left">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 width="18" height="18" stroke-width="1.8" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0
                       002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424
                       48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664
                       0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25
                       0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012
                       0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08
                       C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875
                       c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125
                       1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375
                       c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008
                       H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"/>
            </svg>
            <span>Asset Summary Report</span>
            <span class="summ-ts">Generated {html.escape(gen_ts)}</span>
          </div>
          <button class="btn-print" onclick="window.print()">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                 width="14" height="14" stroke-width="1.8" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round"
                    d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096
                       a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.38
                       -4.171l.24 4.171m0 0a2.25 2.25 0 002.25-2.25V6.75
                       a2.25 2.25 0 00-2.25-2.25H5.25A2.25 2.25 0 003
                       6.75v8.25a2.25 2.25 0 002.25 2.25h.75m11.25-10.5
                       H6.75M6.75 7.5h10.5"/>
            </svg>
            Print / Export
          </button>
        </div>""")
 
        # Key Performance Indicators
        kpis = [
            ("Total Assets", stats.get("total",       0), "#3b82f6"),
            ("Available",    stats.get("available",   0), "#22c55e"),
            ("In Use",       stats.get("in_use",      0), "#3b82f6"),
            ("Rented",       stats.get("rented",      0), "#8b5cf6"),
            ("Maintenance",  stats.get("maintenance", 0), "#f59e0b"),
        ]
        kpi_cards = "".join(f"""
        <div class="stat-card">
          <p class="stat-label">{label}</p>
          <div class="stat-value-row">
            <span class="status-dot" style="background:{color};flex-shrink:0;"></span>
            <span class="stat-number">{val}</span>
          </div>
        </div>""" for label, val, color in kpis)
        out.append(f'<div class="summ-kpi-grid">{kpi_cards}</div>')
 
        # All Assets
        all_assets = data.get("all_assets", [])
        all_assets_content = ""
        if all_assets:
            all_rows = ""
            for a in all_assets:
                aid   = a.get("asset_id", "")
                name  = html.escape(str(a.get("name",          "—")))
                cat   = html.escape(str(a.get("category",      "—")))
                sn    = html.escape(str(a.get("serial_number", "—")))
                loc   = html.escape(str(a.get("location",      "—")))
                badge = cls.status_badge_static(str(a.get("status", "")))
                all_rows += f"""<tr>
                  <td class="asset-id">{aid}</td>
                  <td style="font-weight:500;">{name}</td>
                  <td>{cat}</td>
                  <td class="serial">{sn}</td>
                  <td>{loc}</td>
                  <td>{badge}</td>
                </tr>"""
            all_assets_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <thead><tr>
                  <th>ID</th><th>Name</th><th>Category</th>
                  <th>Serial</th><th>Location</th><th>Status</th>
                </tr></thead>
                <tbody>{all_rows}</tbody>
              </table>
            </div>"""
        else:
            all_assets_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <tbody>{cls._empty_row(6)}</tbody>
              </table>
            </div>"""

        out.append(cls._summ_panel(
            title="All Assets",
            count=len(all_assets),
            color="#6366f1",
            content=all_assets_content
        ))

        # Active In-Use Items
        in_use = data.get("in_use_assets", [])
        out.append(cls._summ_panel(
            title="Active In-Use Items",
            count=len(in_use),
            color="#3b82f6",
            content=cls._summ_asset_table(in_use)
        ))
 
        # Currently Rented Items
        active_rentals = data.get("active_rentals", [])
        if active_rentals:
            rented_rows = ""
            for r in active_rentals:
                rental_id = r.get("rental_id", "")
                asset     = html.escape(str(r.get("asset_name",  "—")))
                renter    = html.escape(str(r.get("renter_name", "—")))
                start     = str(r.get("rental_start", ""))[:10] or "—"
                due_raw   = str(r.get("rental_due",   ""))[:10]
                due       = due_raw or "—"
                status    = str(r.get("rental_status", "Active"))
 
                # Flag overdue items
                overdue = False
                try:
                    from datetime import date as _date
                    overdue = (_date.fromisoformat(due_raw) < now.date()
                               and status == "Active")
                except (ValueError, TypeError):
                    pass
 
                due_cell = (
                    f'<span class="summ-overdue">{due} ⚠ Overdue</span>'
                    if overdue else due
                )
                badge = cls.rental_status_badge("Late" if overdue else status)
 
                rented_rows += f"""<tr>
                  <td class="asset-id">{rental_id}</td>
                  <td style="font-weight:500;">{asset}</td>
                  <td>{renter}</td>
                  <td>{start}</td>
                  <td>{due_cell}</td>
                  <td>{badge}</td>
                </tr>"""
 
            rented_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <thead><tr>
                  <th>Rental #</th><th>Asset</th><th>Rented By</th>
                  <th>Start</th><th>Due</th><th>Status</th>
                </tr></thead>
                <tbody>{rented_rows}</tbody>
              </table>
            </div>"""
        else:
            rented_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <tbody>{cls._empty_row(6, "No items currently rented.")}</tbody>
              </table>
            </div>"""
 
        out.append(cls._summ_panel(
            title="Currently Rented Items",
            count=len(active_rentals),
            color="#8b5cf6",
            content=rented_content
        ))
 
        # Rental Requests
        all_requests = data.get("all_requests", [])
        req_counts   = data.get("req_counts",   {"Pending": 0, "Approved": 0, "Denied": 0})
 
        breakdown = f"""
        <div class="summ-req-breakdown">
          <div class="summ-req-pill summ-pill-pending">
            <span class="summ-req-num">{req_counts.get("Pending",  0)}</span>
            <span class="summ-req-lbl">Pending</span>
          </div>
          <div class="summ-req-pill summ-pill-approved">
            <span class="summ-req-num">{req_counts.get("Approved", 0)}</span>
            <span class="summ-req-lbl">Approved</span>
          </div>
          <div class="summ-req-pill summ-pill-denied">
            <span class="summ-req-num">{req_counts.get("Denied",   0)}</span>
            <span class="summ-req-lbl">Denied</span>
          </div>
        </div>"""
 
        if all_requests:
            req_rows = ""
            for r in all_requests:
                req_id    = r.get("request_id", "")
                asset     = html.escape(str(r.get("asset_name",     "—")))
                cat       = html.escape(str(r.get("asset_category", "—")))
                requester = html.escape(str(r.get("requester_name", "—")))
                role      = html.escape(str(r.get("requester_role", "")))
                start     = str(r.get("requested_start", ""))[:10] or "—"
                due       = str(r.get("requested_due",   ""))[:10] or "—"
                badge     = cls.request_status_badge(str(r.get("request_status", "")))
                req_rows += f"""<tr>
                  <td class="asset-id">{req_id}</td>
                  <td>{asset}</td><td>{cat}</td>
                  <td>{requester}
                    <small class="role-hint">({role})</small>
                  </td>
                  <td>{start}</td><td>{due}</td><td>{badge}</td>
                </tr>"""
            req_table = f"""
            <div class="table-wrapper" style="margin-top:.75rem;">
              <table class="asset-table">
                <thead><tr>
                  <th>Req #</th><th>Asset</th><th>Category</th>
                  <th>Requested By</th><th>Start</th><th>Due</th><th>Status</th>
                </tr></thead>
                <tbody>{req_rows}</tbody>
              </table>
            </div>"""
        else:
            req_table = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <tbody>{cls._empty_row(7, "No rental requests found.")}</tbody>
              </table>
            </div>"""
 
        out.append(cls._summ_panel(
            title="Rental Requests",
            count=len(all_requests),
            color="#f59e0b",
            content=breakdown + req_table
        ))
 
        # Maintenance & Other Statuses
        maintenance = data.get("maintenance_assets", [])
        other       = data.get("other_assets",       [])
        combined    = maintenance + other
 
        if combined:
            other_rows = ""
            for a in combined:
                aid   = a.get("asset_id", "")
                name  = html.escape(str(a.get("name",          "—")))
                cat   = html.escape(str(a.get("category",      "—")))
                sn    = html.escape(str(a.get("serial_number", "—")))
                loc   = html.escape(str(a.get("location",      "—")))
                badge = cls.status_badge_static(str(a.get("status", "")))
                other_rows += f"""<tr>
                  <td class="asset-id">{aid}</td>
                  <td style="font-weight:500;">{name}</td>
                  <td>{cat}</td>
                  <td class="serial">{sn}</td>
                  <td>{loc}</td>
                  <td>{badge}</td>
                </tr>"""
            other_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <thead><tr>
                  <th>ID</th><th>Name</th><th>Category</th>
                  <th>Serial</th><th>Location</th><th>Status</th>
                </tr></thead>
                <tbody>{other_rows}</tbody>
              </table>
            </div>"""
        else:
            other_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <tbody>{cls._empty_row(6, "No items under maintenance or other statuses.")}</tbody>
              </table>
            </div>"""
 
        out.append(cls._summ_panel(
            title="Maintenance & Other Statuses",
            count=len(combined),
            color="#f59e0b",
            content=other_content
        ))
 
        # Asset Timeline
        timeline = data.get("timeline", [])
 
        if not timeline:
            timeline_content = f"""
            <div class="summ-notice">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                   width="16" height="16" stroke-width="1.8" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round"
                      d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708
                         2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0
                         11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
              </svg>
              <span>
                Timeline data requires <code>created_at</code> and
                <code>updated_at</code> columns in the <code>assets</code> table.
                Run the following SQL to enable this section:
              </span>
            </div>
            <pre class="summ-sql">ALTER TABLE assets
  ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
             ON UPDATE CURRENT_TIMESTAMP;</pre>"""
        else:
            has_created = "created_at" in timeline[0]
            has_updated = "updated_at" in timeline[0]
            tl_rows = ""
            for a in timeline:
                aid     = a.get("asset_id", "")
                name    = html.escape(str(a.get("name",     "—")))
                cat     = html.escape(str(a.get("category", "—")))
                badge   = cls.status_badge_static(str(a.get("status", "")))
                created = str(a.get("created_at", ""))[:16] or "—"
                updated = str(a.get("updated_at", ""))[:16] or "—"
 
                tl_rows += f"""<tr>
                  <td class="asset-id">{aid}</td>
                  <td style="font-weight:500;">{name}</td>
                  <td>{cat}</td>
                  <td>{badge}</td>
                  {"<td class='summ-date'>" + created + "</td>" if has_created else ""}
                  {"<td class='summ-date'>" + updated + "</td>" if has_updated else ""}
                </tr>"""
 
            th_created = "<th>Date Added</th>"    if has_created else ""
            th_updated = "<th>Last Updated</th>"  if has_updated else ""
            timeline_content = f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <thead><tr>
                  <th>ID</th><th>Name</th><th>Category</th><th>Status</th>
                  {th_created}{th_updated}
                </tr></thead>
                <tbody>{tl_rows}</tbody>
              </table>
            </div>"""
 
        out.append(cls._summ_panel(
            title="Asset Timeline",
            count=None,
            color="#6b7280",
            content=timeline_content
        ))
 
        return "\n".join(out)
 
    # Summary helpers
    @staticmethod
    def _summ_panel(title: str, count, color: str, content: str) -> str:
        """Wraps a summary section in a titled panel card."""
        count_badge = (
            f'<span class="summ-count-badge" style="'
            f'background:{color}1a;color:{color};">{count}</span>'
        ) if count is not None else ""
 
        return f"""
    <div class="panel summ-panel">
      <div class="summ-panel-hdr">
        <span class="summ-panel-dot" style="background:{color};"></span>
        <h2 class="panel-title" style="margin:0;">{title}</h2>
        {count_badge}
      </div>
      {content}
    </div>"""
 
    @classmethod
    def _summ_asset_table(cls, assets: list) -> str:
        """Read-only asset table for In-Use section of the summary."""
        if not assets:
            return f"""
            <div class="table-wrapper">
              <table class="asset-table">
                <tbody>{cls._empty_row(5)}</tbody>
              </table>
            </div>"""
        rows = ""
        for a in assets:
            aid  = a.get("asset_id", "")
            name = html.escape(str(a.get("name",          "—")))
            cat  = html.escape(str(a.get("category",      "—")))
            sn   = html.escape(str(a.get("serial_number", "—")))
            loc  = html.escape(str(a.get("location",      "—")))
            rows += f"""<tr>
              <td class="asset-id">{aid}</td>
              <td style="font-weight:500;">{name}</td>
              <td>{cat}</td>
              <td class="serial">{sn}</td>
              <td>{loc}</td>
            </tr>"""
        return f"""
        <div class="table-wrapper">
          <table class="asset-table">
            <thead><tr>
              <th>ID</th><th>Name</th><th>Category</th>
              <th>Serial</th><th>Location</th>
            </tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>"""