# models/rental.py
# Handles all DB interaction for rental_requests and rentals tables.

import mysql.connector
from mysql.connector import Error
import config


class Rental:

    @staticmethod
    def _connect():
        try:
            return mysql.connector.connect(**config.DB_CONFIG)
        except Error:
            return None

    # Admin stat cards
    @classmethod
    def get_admin_stats(cls) -> dict:
        conn = cls._connect()
        if conn is None:
            return {"pending_requests": 0, "active_rentals": 0, "overdue": 0}
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS cnt FROM rental_requests WHERE request_status='Pending'")
            pending = int(cursor.fetchone()["cnt"] or 0)
            cursor.execute("SELECT COUNT(*) AS cnt FROM rentals WHERE rental_status='Active'")
            active  = int(cursor.fetchone()["cnt"] or 0)
            cursor.execute("SELECT COUNT(*) AS cnt FROM rentals WHERE rental_status='Late'")
            overdue = int(cursor.fetchone()["cnt"] or 0)
            return {"pending_requests": pending, "active_rentals": active, "overdue": overdue}
        except Error:
            return {"pending_requests": 0, "active_rentals": 0, "overdue": 0}
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # User stat cards
    @classmethod
    def get_user_stats(cls, user: dict) -> dict:
        conn = cls._connect()
        if conn is None:
            return {"available": 0, "active_rentals": 0, "pending_requests": 0}
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM assets WHERE asset_status='available'"
            )
            available = int(cursor.fetchone()["cnt"] or 0)

            uid  = user["user_id"]
            role = user["role"]
            id_col = "student_id" if role == "student" else "faculty_id"

            cursor.execute(
                f"""SELECT COUNT(*) AS cnt FROM rentals r
                    JOIN rental_requests rr ON rr.request_id = r.request_id
                    WHERE rr.{id_col} = %s AND r.rental_status = 'Active'""",
                (uid,),
            )
            active = int(cursor.fetchone()["cnt"] or 0)

            cursor.execute(
                f"SELECT COUNT(*) AS cnt FROM rental_requests WHERE {id_col} = %s AND request_status='Pending'",
                (uid,),
            )
            pending = int(cursor.fetchone()["cnt"] or 0)

            return {"available": available, "active_rentals": active, "pending_requests": pending}
        except Error:
            return {"available": 0, "active_rentals": 0, "pending_requests": 0}
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # Fetch rental requests
    @classmethod
    def get_requests(cls, user=None, status_filter="Pending") -> list:
        """
        user=None  → all requests (admin view)
        user=dict  → filtered to that faculty/student
        """
        conn = cls._connect()
        if conn is None:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT rr.request_id, rr.asset_id,
                       a.asset_name, a.asset_category, a.asset_location,
                       rr.request_date, rr.requested_start, rr.requested_due,
                       rr.request_status, rr.review_date,
                       COALESCE(
                           CONCAT(s.student_fname,' ',s.student_lname),
                           CONCAT(f.faculty_fname,' ',f.faculty_lname),
                           'Unknown'
                       ) AS requester_name,
                       CASE WHEN rr.student_id IS NOT NULL THEN 'student'
                            ELSE 'faculty' END AS requester_role
                FROM rental_requests rr
                JOIN  assets    a ON a.asset_id  = rr.asset_id
                LEFT JOIN students s ON s.student_id = rr.student_id
                LEFT JOIN faculty  f ON f.faculty_id = rr.faculty_id
                WHERE 1=1
            """
            params = []
            if status_filter and status_filter != "All":
                query += " AND rr.request_status = %s"; params.append(status_filter)
            if user:
                id_col = "student_id" if user["role"] == "student" else "faculty_id"
                query += f" AND rr.{id_col} = %s";     params.append(user["user_id"])
            query += " ORDER BY rr.request_date DESC"
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error:
            return []
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # Fetch active rentals
    @classmethod
    def get_active(cls, user=None) -> list:
        conn = cls._connect()
        if conn is None:
            return []
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT r.rental_id, r.asset_id,
                       a.asset_name, a.asset_category, a.asset_location,
                       r.rental_start, r.rental_due, r.rental_returned,
                       r.rental_status, rr.student_id, rr.faculty_id,
                       COALESCE(
                           CONCAT(s.student_fname,' ',s.student_lname),
                           CONCAT(f.faculty_fname,' ',f.faculty_lname),
                           'Unknown'
                       ) AS renter_name
                FROM rentals r
                JOIN  rental_requests rr ON rr.request_id = r.request_id
                JOIN  assets           a ON a.asset_id    = r.asset_id
                LEFT JOIN students s ON s.student_id = rr.student_id
                LEFT JOIN faculty  f ON f.faculty_id = rr.faculty_id
                WHERE r.rental_status IN ('Active','Late')
            """
            params = []
            if user:
                id_col = "student_id" if user["role"] == "student" else "faculty_id"
                query += f" AND rr.{id_col} = %s"; params.append(user["user_id"])
            query += " ORDER BY r.rental_due ASC"
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error:
            return []
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # Create / Approve / Deny
    @classmethod
    def create_request(cls, user: dict, asset_id: int,
                       start_date: str, due_date: str):
        """Returns (True, request_id) or (False, error_string)."""
        conn = cls._connect()
        if conn is None:
            return False, "Database connection failed"
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT asset_status FROM assets WHERE asset_id=%s", (asset_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Asset not found"
            if row[0] != "available":
                return False, "Asset is not currently available"

            id_col = "student_id" if user["role"] == "student" else "faculty_id"
            cursor.execute(
                f"""SELECT request_id FROM rental_requests
                    WHERE asset_id=%s AND {id_col}=%s
                      AND request_status IN ('Pending','Approved') LIMIT 1""",
                (asset_id, user["user_id"]),
            )
            if cursor.fetchone():
                return False, "You already have an active request for this asset"

            cursor.execute(
                f"""INSERT INTO rental_requests
                        (asset_id, {id_col}, requested_start, requested_due, request_status)
                    VALUES (%s, %s, %s, %s, 'Pending')""",
                (asset_id, user["user_id"], start_date, due_date),
            )
            conn.commit()
            return True, cursor.lastrowid
        except Error as exc:
            return False, str(exc)
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def approve(cls, request_id: int) -> bool:
        conn = cls._connect()
        if conn is None:
            return False
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM rental_requests WHERE request_id=%s AND request_status='Pending'",
                (request_id,),
            )
            req = cursor.fetchone()
            if not req:
                return False
            cursor.execute(
                "UPDATE rental_requests SET request_status='Approved', review_date=NOW() WHERE request_id=%s",
                (request_id,),
            )
            cursor.execute(
                """INSERT INTO rentals (request_id, asset_id, rental_start, rental_due, rental_status)
                   VALUES (%s, %s, %s, %s, 'Active')""",
                (request_id, req["asset_id"], req["requested_start"], req["requested_due"]),
            )
            cursor.execute(
                "UPDATE assets SET asset_status='rented' WHERE asset_id=%s",
                (req["asset_id"],),
            )
            conn.commit()
            return True
        except Error:
            try: conn.rollback()
            except Exception: pass
            return False
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def deny(cls, request_id: int) -> bool:
        conn = cls._connect()
        if conn is None:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE rental_requests SET request_status='Denied', review_date=NOW() WHERE request_id=%s AND request_status='Pending'",
                (request_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Error:
            return False
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    @classmethod
    def return_rental(cls, rental_id: int, user: dict) -> tuple:
        """
        Mark a rental as returned.
        - Sets rentals.rental_status = 'Returned' and rental_returned = NOW()
        - Sets assets.asset_status   = 'available'

        Security: faculty/student can only return their own rentals.
                  Admin can return any rental (user=None).

        Returns (True, None) on success or (False, error_string) on failure.
        """
        conn = cls._connect()
        if conn is None:
            return False, "Database connection failed"
        try:
            cursor = conn.cursor(dictionary=True)

            # Fetch the rental and verify it is still active
            cursor.execute(
                """SELECT r.rental_id, r.asset_id, r.rental_status,
                          rr.student_id, rr.faculty_id
                   FROM rentals r
                   JOIN rental_requests rr ON rr.request_id = r.request_id
                   WHERE r.rental_id = %s""",
                (rental_id,),
            )
            rental = cursor.fetchone()

            if not rental:
                return False, "Rental not found"

            if rental["rental_status"] == "Returned":
                return False, "This rental has already been returned"

            if rental["rental_status"] not in ("Active", "Late"):
                return False, "Rental cannot be returned in its current state"

            # Ownership check, skip for admin
            if user and user.get("role") != "admin":
                uid    = user["user_id"]
                role   = user["role"]
                owner  = (
                    rental["student_id"] if role == "student"
                    else rental["faculty_id"]
                )
                if owner != uid:
                    return False, "You can only return your own rentals"

            # Mark rental as returned
            cursor.execute(
                """UPDATE rentals
                   SET rental_status   = 'Returned',
                       rental_returned = NOW()
                   WHERE rental_id = %s""",
                (rental_id,),
            )

            # Free up the asset
            cursor.execute(
                "UPDATE assets SET asset_status = 'available' WHERE asset_id = %s",
                (rental["asset_id"],),
            )

            conn.commit()
            return True, None

        except Error as exc:
            try: conn.rollback()
            except Exception: pass
            return False, str(exc)
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass