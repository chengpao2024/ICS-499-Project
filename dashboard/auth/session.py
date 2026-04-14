# auth/session.py
# Resolves the current user from cookies.
# Reads the PHP session file written by index.php and looks up
# the matching user record in the database.

import os
import re
import subprocess
import mysql.connector
from mysql.connector import Error
import config


class SessionResolver:

    # ── Public API ────────────────────────────────────
    @classmethod
    def get_current_user(cls) -> dict | None:
        """Return user dict or None (caller redirects to login)."""
        cookies = cls._parse_cookies()

        # Strategy 1: DB-backed sessions table (requires PHP team integration)
        token = cookies.get(config.SESSION_COOKIE_NAME, "")
        if token:
            user = cls._from_db_token(token)
            if user:
                return user

        # Strategy 2: Read PHP session file directly (works out of the box)
        phpsessid = cookies.get(config.PHPSESSID_COOKIE, "")
        if phpsessid:
            return cls._from_php_session(phpsessid)

        return None

    # ── Cookie parsing ────────────────────────────────
    @staticmethod
    def _parse_cookies() -> dict:
        cookies = {}
        for part in os.environ.get("HTTP_COOKIE", "").split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    # ── Strategy 1: DB sessions table ────────────────
    @classmethod
    def _from_db_token(cls, token: str) -> dict | None:
        try:
            conn   = mysql.connector.connect(**config.DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT user_id, role, username,
                          COALESCE(department, '') AS department
                   FROM sessions
                   WHERE token = %s
                     AND created_at > NOW() - INTERVAL 8 HOUR""",
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            details = cls._fetch_user_by_id(cursor, row["role"], row["user_id"])
            return {**row, **details,
                    "department": row["department"] or details.get("department", "")}
        except Error:
            return None
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # ── Strategy 2: PHP session file ─────────────────
    @classmethod
    def _from_php_session(cls, session_id: str) -> dict | None:
        if not re.match(r"^[a-zA-Z0-9,\-]+$", session_id):
            return None

        session_path = cls._resolve_session_path()
        path = os.path.join(session_path, f"sess_{session_id}")
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                raw = fh.read()
        except OSError:
            return None

        session    = cls._parse_php_session_data(raw)
        identifier = session.get("user", "")      # email or username
        role       = session.get("role", "")
        user_id    = session.get("user_id", 0)    # stored by updated index.php

        if not identifier or role not in config.ROLES:
            return None

        try:
            conn   = mysql.connector.connect(**config.DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # Prefer lookup by user_id (set by updated index.php)
            if user_id:
                details = cls._fetch_user_by_id(cursor, role, int(user_id))
            else:
                # Fallback: lookup by identifier for older sessions
                details = cls._fetch_user_by_identifier(cursor, role, identifier)

            return {
                "user_id":      details.get("user_id", 0),
                "username":     identifier,
                "display_name": details.get("display_name", identifier),
                "email":        details.get("email", ""),
                "role":         role,
                "department":   details.get("department", ""),
            }
        except Error:
            # DB unavailable — cant verify user
            return None
        
            # This was for the bypass to render the page
            return {
                "user_id": 0, "username": identifier,
                "display_name": identifier, "email": "",
                "role": role, "department": "",
            }
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # ── DB lookups ────────────────────────────────────
    @staticmethod
    def _fetch_user_by_id(cursor, role: str, user_id: int) -> dict:
        """Look up user record by primary key — exact, no ambiguity."""
        defaults = {"user_id": user_id, "display_name": "",
                    "email": "", "department": ""}
        try:
            if role == "admin":
                cursor.execute(
                    "SELECT admin_id AS user_id, admin_username AS display_name"
                    " FROM admins WHERE admin_id = %s LIMIT 1",
                    (user_id,),
                )
                row = cursor.fetchone()
                if row:
                    return {"user_id": row["user_id"],
                            "display_name": row["display_name"],
                            "email": "", "department": ""}

            elif role == "faculty":
                cursor.execute(
                    """SELECT faculty_id AS user_id,
                              CONCAT(faculty_fname,' ',faculty_lname) AS display_name,
                              faculty_email AS email,
                              COALESCE(department,'') AS department
                       FROM faculty WHERE faculty_id = %s LIMIT 1""",
                    (user_id,),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)

            elif role == "student":
                cursor.execute(
                    """SELECT student_id AS user_id,
                              CONCAT(student_fname,' ',student_lname) AS display_name,
                              student_email AS email,
                              '' AS department
                       FROM students WHERE student_id = %s LIMIT 1""",
                    (user_id,),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)

        except Error:
            return None
        return defaults

    @staticmethod
    def _fetch_user_by_identifier(cursor, role: str, identifier: str) -> dict:
        """
        Fallback lookup by username or email for sessions created before
        index.php was updated to store user_id.
        """
        defaults = {"user_id": 0, "display_name": identifier,
                    "email": "", "department": ""}
        try:
            if role == "admin":
                cursor.execute(
                    "SELECT admin_id AS user_id, admin_username AS display_name"
                    " FROM admins WHERE admin_username = %s LIMIT 1",
                    (identifier,),
                )
                row = cursor.fetchone()
                if row:
                    return {"user_id": row["user_id"],
                            "display_name": row["display_name"],
                            "email": "", "department": ""}

            elif role == "faculty":
                cursor.execute(
                    """SELECT faculty_id AS user_id,
                              CONCAT(faculty_fname,' ',faculty_lname) AS display_name,
                              faculty_email AS email,
                              COALESCE(department,'') AS department
                       FROM faculty WHERE faculty_email = %s LIMIT 1""",
                    (identifier,),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)

            elif role == "student":
                cursor.execute(
                    """SELECT student_id AS user_id,
                              CONCAT(student_fname,' ',student_lname) AS display_name,
                              student_email AS email,
                              '' AS department
                       FROM students WHERE student_email = %s LIMIT 1""",
                    (identifier,),
                )
                row = cursor.fetchone()
                if row:
                    return dict(row)

        except Error:
            return None
        return defaults

    # ── Session path resolver ─────────────────────────
    @staticmethod
    def _resolve_session_path() -> str:
        """Find PHP session path dynamically instead of hardcoding it."""
        # First try asking PHP directly
        try:
            result = subprocess.run(
                ["php", "-r", "echo session_save_path();"],
                capture_output=True, text=True, timeout=3
            )
            path = result.stdout.strip()
            if path and os.path.exists(path):
                return path
        except Exception:
            pass

        # Fall back to config value, then common XAMPP locations
        candidates = [
            config.PHP_SESSION_PATH,
            "C:/xampp/tmp",
            "D:/xampp/tmp",
            "D:/ics499/tmp",
            os.path.join(os.environ.get("TEMP", ""), ""),
        ]
        for p in candidates:
            if p and os.path.exists(p):
                return p

        return config.PHP_SESSION_PATH

    # ── PHP session deserialiser ──────────────────────
    @staticmethod
    def _parse_php_session_data(data: str) -> dict:
        """Parse PHP native session serialisation format (scalar values only)."""
        result = {}
        i, n = 0, len(data)
        while i < n:
            pipe = data.find("|", i)
            if pipe == -1:
                break
            key = data[i:pipe]
            i   = pipe + 1
            if i >= n:
                break
            if data[i:i+2] == "s:":
                colon = data.find(":", i + 2)
                if colon == -1:
                    break
                try:
                    length = int(data[i+2:colon])
                    start  = colon + 2
                    result[key] = data[start:start + length]
                    i = start + length + 2
                except (ValueError, IndexError):
                    break
            elif data[i:i+2] == "i:":
                semi = data.find(";", i)
                if semi == -1:
                    break
                try:
                    result[key] = int(data[i+2:semi])
                except ValueError:
                    pass
                i = semi + 1
            else:
                semi = data.find(";", i)
                i = (semi + 1) if semi != -1 else n
        return result