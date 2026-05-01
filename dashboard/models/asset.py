# models/asset.py
# Handles all DB interaction for the assets table.

import mysql.connector
from mysql.connector import Error
import config


class Asset:

    # connection helper
    @staticmethod
    def _connect():
        try:
            return mysql.connector.connect(**config.DB_CONFIG)
        except Error:
            return None

    @staticmethod
    def _col_exists(cursor, column: str) -> bool:
        """Graceful check for columns not yet in the schema (e.g. department)."""
        try:
            cursor.execute(
                """SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = %s
                     AND TABLE_NAME   = 'assets'
                     AND COLUMN_NAME  = %s""",
                (config.DB_CONFIG["database"], column),
            )
            row = cursor.fetchone()
            return bool(row and row[0])
        except Exception:
            return False

    # queries
    @classmethod
    def get_stats(cls) -> dict:
        conn = cls._connect()
        if conn is None:
            return {"total": 0, "available": 0, "in_use": 0,
                    "maintenance": 0, "rented": 0}
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT COUNT(*)                          AS total,
                       SUM(asset_status='available')     AS available,
                       SUM(asset_status='in-use')        AS in_use,
                       SUM(asset_status='maintenance')   AS maintenance,
                       SUM(asset_status='rented')        AS rented
                FROM assets
            """)
            row = cursor.fetchone()
            return {k: int(v or 0) for k, v in row.items()}
        except Error:
            return {"total": 0, "available": 0, "in_use": 0,
                    "maintenance": 0, "rented": 0}
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def get_list(cls, search="", category="", status="",
                 sort_by="asset_id", sort_dir="asc",
                 department="") -> list:
        conn = cls._connect()
        if conn is None:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            db_col = config.SORT_FIELDS.get(sort_by, "asset_id")
            db_dir = "DESC" if sort_dir == "desc" else "ASC"

            query  = """
                SELECT asset_id,
                       asset_name     AS name,
                       asset_category AS category,
                       asset_serial   AS serial_number,
                       asset_location AS location,
                       asset_status   AS status
                FROM assets WHERE 1=1
            """
            params = []
            if search:
                like    = f"%{search}%"
                query  += " AND (asset_name LIKE %s OR asset_serial LIKE %s OR asset_location LIKE %s)"
                params += [like, like, like]
            if category and category != "All Categories":
                query += " AND asset_category = %s"; params.append(category)
            if status and status != "All Statuses":
                query += " AND asset_status = %s";   params.append(status)
            if department and cls._col_exists(cursor, "department"):
                query += " AND department = %s";     params.append(department)

            query += f" ORDER BY {db_col} {db_dir}"
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error:
            return []
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def delete(cls, asset_id: int) -> bool:
        conn = cls._connect()
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

    @classmethod
    def update_status(cls, asset_id: int, new_status: str) -> bool:
        if new_status not in config.STATUSES:
            return False
        conn = cls._connect()
        if conn is None:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE assets SET asset_status = %s WHERE asset_id = %s",
                (new_status, asset_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Error:
            return False
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def update_field(cls, asset_id: int, field: str, value: str) -> bool:
        """Inline edit — only whitelisted fields."""
        if field not in config.EDITABLE_FIELDS:
            return False
        value = value.strip()
        if not value:
            return False
        db_col = config.EDITABLE_FIELDS[field]
        conn   = cls._connect()
        if conn is None:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE assets SET {db_col} = %s WHERE asset_id = %s",
                (value, asset_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Error:
            return False
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def get_by_status(cls, status: str) -> list:
        """Return all assets matching a single status value."""
        return cls.get_list(status=status)
 
    @classmethod
    def get_other_status_assets(cls) -> list:
        """
        Return assets whose status falls outside the four standard values.
        Useful for surfacing 'reserved' or any future custom statuses.
        """
        conn = cls._connect()
        if conn is None:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT asset_id,
                       asset_name     AS name,
                       asset_category AS category,
                       asset_serial   AS serial_number,
                       asset_location AS location,
                       asset_status   AS status
                FROM   assets
                WHERE  asset_status NOT IN ('available','in-use','maintenance','rented')
                ORDER  BY asset_id ASC
            """)
            return cursor.fetchall()
        except Error:
            return []
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass
 
    @classmethod
    def get_timeline(cls) -> list:
        """
        Return all assets ordered by creation date, including
        created_at and updated_at if those columns exist in the schema.
 
        If neither column is present the method returns an empty list —
        the caller (HtmlBuilder.summary_html) renders an informational
        notice telling the admin to add the columns.
 
        To enable this section, run:
            ALTER TABLE assets
              ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         ON UPDATE CURRENT_TIMESTAMP;
        """
        conn = cls._connect()
        if conn is None:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
 
            has_created = cls._col_exists(cursor, "created_at")
            has_updated = cls._col_exists(cursor, "updated_at")
 
            if not has_created and not has_updated:
                return []          # Caller will display the "add columns" notice
 
            date_parts = []
            if has_created:
                date_parts.append("created_at")
            if has_updated:
                date_parts.append("updated_at")
 
            col_str  = ", ".join(date_parts)
            order_by = "created_at DESC" if has_created else "asset_id DESC"
 
            cursor.execute(f"""
                SELECT asset_id,
                       asset_name     AS name,
                       asset_category AS category,
                       asset_status   AS status,
                       {col_str}
                FROM   assets
                ORDER  BY {order_by}
            """)
            return cursor.fetchall()
        except Error:
            return []
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass