"""User-related database operations for LOCUS."""

import bcrypt

from database.database import get_connection
from models.user import User
from logic.validation import (
    validate_name,
    validate_email,
    validate_student_id,
    validate_password,
    validate_user_id,
)


# ── Internal helper ──────────────────────────────────────────────────────────

def _row_to_user(row, include_password=False):
    """Convert a DB dict-row to a User model instance."""
    user = User(
        user_id    = row["user_id"],
        name       = row["name"],
        email      = row["email"],
        student_id = row["student_id"],
        password   = row.get("password") if include_password else None,
        created_at = row.get("created_at"),
    )
    return user


# ── Public API ───────────────────────────────────────────────────────────────

def register_user(name, email, student_id, password):
    """Create a new user account.

    Args:
        name        (str): Full name.
        email       (str): Unique email address.
        student_id  (str): Unique student/registration number.
        password    (str): Plain-text password (will be hashed).

    Returns:
        dict – ``{"success": True,  "user_id": <id>}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
        validate_name(name)
        validate_email(email)
        validate_student_id(student_id)
        validate_password(password)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    # Hash the password
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, student_id, password) "
            "VALUES (%s, %s, %s, %s)",
            (name.strip(), email.strip().lower(), student_id.strip(), hashed),
        )
        conn.commit()
        return {"success": True, "user_id": cursor.lastrowid}

    except Exception as exc:
        if conn:
            conn.rollback()
        err = str(exc)
        if "uq_users_email" in err or "Duplicate entry" in err and "email" in err:
            return {"success": False, "error": "Email address is already registered."}
        if "uq_users_student_id" in err or "Duplicate entry" in err and "student_id" in err:
            return {"success": False, "error": "Student ID is already registered."}
        return {"success": False, "error": err}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def login_user(email, password):
    """Verify credentials and return the User on success.

    Returns:
        dict – ``{"success": True,  "user": User}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
        validate_email(email)
        validate_password(password)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, name, email, student_id, password, created_at "
            "FROM   users "
            "WHERE  email = %s",
            (email.strip().lower(),),
        )
        row = cursor.fetchone()

        if not row:
            return {"success": False, "error": "Invalid email or password."}

        if not bcrypt.checkpw(password.encode("utf-8"), row["password"].encode("utf-8")):
            return {"success": False, "error": "Invalid email or password."}

        user = _row_to_user(row, include_password=False)
        return {"success": True, "user": user}

    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user_by_email(email):
    """Return a User (without password) matching the email, or None."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, name, email, student_id, created_at "
            "FROM   users WHERE email = %s",
            (email.strip().lower(),),
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user_by_id(user_id):
    """Return a User (without password) matching the user_id, or None."""
    try:
        validate_user_id(user_id)
    except ValueError:
        return None

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, name, email, student_id, created_at "
            "FROM   users WHERE user_id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        return _row_to_user(row) if row else None
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_user(user_id, name, email, student_id):
    """Update profile fields for a user.

    Returns:
        dict – ``{"success": True}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
        validate_user_id(user_id)
        validate_name(name)
        validate_email(email)
        validate_student_id(student_id)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET name = %s, email = %s, student_id = %s "
            "WHERE user_id = %s",
            (name.strip(), email.strip().lower(), student_id.strip(), user_id),
        )
        if cursor.rowcount == 0:
            return {"success": False, "error": "User not found."}
        conn.commit()
        return {"success": True}

    except Exception as exc:
        if conn:
            conn.rollback()
        err = str(exc)
        if "uq_users_email" in err or "Duplicate entry" in err and "email" in err:
            return {"success": False, "error": "Email address is already in use."}
        if "uq_users_student_id" in err or "Duplicate entry" in err and "student_id" in err:
            return {"success": False, "error": "Student ID is already in use."}
        return {"success": False, "error": err}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_user(user_id):
    """Delete a user account.

    Returns:
        dict – ``{"success": True}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
        validate_user_id(user_id)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        if cursor.rowcount == 0:
            return {"success": False, "error": "User not found."}
        conn.commit()
        return {"success": True}

    except Exception as exc:
        if conn:
            conn.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
