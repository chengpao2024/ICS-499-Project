# views/html_builder.py
# Generates all HTML fragments injected into templates.
# Nothing here touches the DB or HTTP — pure presentation logic.

import html
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
        cols = 6 if role == "admin" else 5
        if not rentals:
            return cls._empty_row(cols, "No active rentals found.")
        rows = ""
        for r in rentals:
            asset = html.escape(str(r["asset_name"]))
            start = str(r["rental_start"])[:10] if r["rental_start"] else "—"
            due   = str(r["rental_due"])[:10]   if r["rental_due"]   else "—"
            badge = cls.rental_status_badge(str(r["rental_status"]))
            renter_col = f'<td>{html.escape(str(r.get("renter_name","—")))}</td>' if role == "admin" else ""
            rows += f"""
        <tr>
          <td class="asset-id">{r["rental_id"]}</td>
          <td>{asset}</td>{renter_col}
          <td>{start}</td><td>{due}</td><td>{badge}</td>
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
                 stroke-width="1.4" stroke="currentColor">
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
            <a href="/public/rental_create.php" class="btn-rent">
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
            </a>
        </td>"""