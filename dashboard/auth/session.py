# auth/session.py
# Resolves the current user from cookies.
# Two-tier strategy:
#   1. DB sessions table (preferred: PHP team adds this)
#   2. Raw PHP session file read from XAMPP tmp file (zero-config fallback)

import os
import re
import mysql.connector
from mysql.connector import Error
import config


class SessionResolver:

    # Public API
    @classmethod
    def get_current_user(cls) -> dict | None:
        """Return user dict or None (caller should redirect to login)."""
        cookies = cls._parse_cookies()

        token = cookies.get(config.SESSION_COOKIE_NAME, "")
        if token:
            user = cls._from_db_token(token)
            if user:
                return user

        phpsessid = cookies.get(config.PHPSESSID_COOKIE, "")
        if phpsessid:
            return cls._from_php_session(phpsessid)

        return None

    # Cookie parsing
    @staticmethod
    def _parse_cookies() -> dict:
        cookies = {}
        for part in os.environ.get("HTTP_COOKIE", "").split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    # Strategy 1: DB sessions table
    @classmethod
    def _from_db_token(cls, token: str) -> dict | None:
        try:
            conn = mysql.connector.connect(**config.DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT user_id, role, username,
                          COALESCE(department,'') AS department
                   FROM sessions
                   WHERE token = %s
                     AND created_at > NOW() - INTERVAL 8 HOUR""",
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            details = cls._fetch_display_info(cursor, row["role"], row["username"])
            return {**row, **details,
                    "department": row["department"] or details.get("department", "")}
        except Error:
            return None
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # Strategy 2: PHP session file
    @classmethod
    def _from_php_session(cls, session_id: str) -> dict | None:
        if not re.match(r"^[a-zA-Z0-9,\-]+$", session_id):
            return None
        path = os.path.join(config.PHP_SESSION_PATH, f"sess_{session_id}")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                raw = fh.read()
        except OSError:
            return None

        session  = cls._parse_php_session_data(raw)
        username = session.get("user", "")
        role     = session.get("role", "")
        if not username or role not in config.ROLES:
            return None

        try:
            conn    = mysql.connector.connect(**config.DB_CONFIG)
            cursor  = conn.cursor(dictionary=True)
            details = cls._fetch_display_info(cursor, role, username)
            return {"username": username, "role": role, **details}
        except Error:
            # DB unavailable — return minimal dict
            return {"user_id": 0, "username": username,
                    "display_name": username, "email": "",
                    "role": role, "department": ""}
        finally:
            try: cursor.close(); conn.close()
            except Exception: pass

    # PHP session deserialiser
    @staticmethod
    def _parse_php_session_data(data: str) -> dict:
        """Parse PHP native session format (scalar values only)."""
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
                try: result[key] = int(data[i+2:semi])
                except ValueError: pass
                i = semi + 1
            else:
                semi = data.find(";", i)
                i = (semi + 1) if semi != -1 else n
        return result

    # DB lookup for display info
    @staticmethod
    def _fetch_display_info(cursor, role: str, username: str) -> dict:
        """Look up name, email, department for a given role + username."""
        defaults = {"user_id": 0, "display_name": username,
                    "email": "", "department": ""}
        try:
            if role == "admin":
                cursor.execute(
                    "SELECT admin_id, admin_username FROM admins WHERE admin_username=%s LIMIT 1",
                    (username,),
                )
                row = cursor.fetchone()
                if row:
                    return {"user_id": row["admin_id"],
                            "display_name": row["admin_username"],
                            "email": "", "department": ""}

            elif role == "faculty":
                cursor.execute(
                    """SELECT faculty_id, faculty_fname, faculty_lname,
                              faculty_email, COALESCE(department,'') AS department
                       FROM faculty WHERE faculty_email LIKE %s LIMIT 1""",
                    (f"%{username}%",),
                )
                row = cursor.fetchone()
                if row:
                    return {"user_id": row["faculty_id"],
                            "display_name": f"{row['faculty_fname']} {row['faculty_lname']}",
                            "email": row["faculty_email"],
                            "department": row["department"]}

            elif role == "student":
                cursor.execute(
                    """SELECT student_id, student_fname, student_lname, student_email
                       FROM students WHERE student_email LIKE %s LIMIT 1""",
                    (f"%{username}%",),
                )
                row = cursor.fetchone()
                if row:
                    return {"user_id": row["student_id"],
                            "display_name": f"{row['student_fname']} {row['student_lname']}",
                            "email": row["student_email"],
                            "department": ""}
        except Error:
            pass
        return defaults