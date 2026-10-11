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
from services.responses import ok, fail


# ── Internal helper ──────────────────────────────────────────────────────────

def _row_to_user(row, include_password=False):
    """Convert a DB dict-row to a User model instance."""
    return User(
        user_id    = row["user_id"],
        name       = row["name"],
        email      = row["email"],
        student_id = row["student_id"],
        password   = row.get("password") if include_password else None,
        created_at = row.get("created_at"),
    )


def _row_to_safe_user_dict(row):
    """Convert a DB dict-row to the user dictionary expected by the frontend."""
    return {
        "user_id":    row["user_id"],
        "name":       row["name"],
        "full_name":  row["name"],
        "student_id": row["student_id"],
        "username":   row["student_id"].lower(),
        "email":      row["email"],
        "created_at": str(row["created_at"]) if row.get("created_at") else None,
    }


# ── Public API ───────────────────────────────────────────────────────────────

def register_user(name, arg2, arg3, password):
    """Create a new user account.

    Supports both parameter orderings:
      - (full_name, student_id, email, password) from UI
      - (name, email, student_id, password) from backend test suite

    Returns:
        dict – unified response with success, message, data, and user_id.
    """
    # Detect parameter order by checking for '@'
    if "@" in str(arg2):
        email = str(arg2).strip().lower()
        student_id = str(arg3).strip()
    elif "@" in str(arg3):
        student_id = str(arg2).strip()
        email = str(arg3).strip().lower()
    else:
        student_id = str(arg2).strip()
        email = str(arg3).strip().lower()

    full_name = str(name).strip()

    try:
        validate_name(full_name)
        validate_email(email)
        validate_student_id(student_id)
        validate_password(password)
    except ValueError as exc:
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, student_id, password) "
            "VALUES (%s, %s, %s, %s)",
            (full_name, email, student_id, hashed),
        )
        conn.commit()
        user_id = cursor.lastrowid

        res = ok("Account created successfully.", {"user_id": user_id})
        res["user_id"] = user_id
        return res

    except Exception as exc:
        if conn:
            conn.rollback()
        err = str(exc)
        if "uq_users_email" in err or ("Duplicate entry" in err and "email" in err):
            err_msg = "An account with this email already exists."
        elif "uq_users_student_id" in err or ("Duplicate entry" in err and "student_id" in err):
            err_msg = "An account with this Student ID already exists."
        else:
            err_msg = err

        res = fail(err_msg)
        res["error"] = err_msg
        return res
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def login_user(identifier, password):
    """Verify credentials and return user details on success.

    Identifier can be an email OR a student ID / username.

    Returns:
        dict – unified response with success, message, data (safe dict), and user (User model).
    """
    ident = str(identifier).strip()
    if not ident:
        res = fail("Please enter both your email/username and password.")
        res["error"] = "Invalid email or password."
        return res

    try:
        validate_password(password)
    except ValueError as exc:
        res = fail(str(exc))
        res["error"] = str(exc)
        return res

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT user_id, name, email, student_id, password, created_at "
            "FROM   users "
            "WHERE  LOWER(email) = %s OR LOWER(student_id) = %s",
            (ident.lower(), ident.lower()),
        )
        row = cursor.fetchone()

        if not row:
            res = fail("Invalid email/username or password.")
            res["error"] = "Invalid email or password."
            return res

        if not bcrypt.checkpw(password.encode("utf-8"), row["password"].encode("utf-8")):
            res = fail("Invalid email/username or password.")
            res["error"] = "Invalid email or password."
            return res

        user = _row_to_user(row, include_password=False)
        safe_user = _row_to_safe_user_dict(row)

        res = ok("Login successful.", safe_user)
        res["user"] = user
        return res

    except Exception as exc:
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res
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
            "FROM   users WHERE LOWER(email) = %s",
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
    """Update profile fields for a user."""
    try:
        validate_user_id(user_id)
        validate_name(name)
        validate_email(email)
        validate_student_id(student_id)
    except ValueError as exc:
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res

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
            res = fail("User not found.")
            res["error"] = "User not found."
            return res
        conn.commit()
        res = ok("User updated successfully.")
        return res

    except Exception as exc:
        if conn:
            conn.rollback()
        err = str(exc)
        if "uq_users_email" in err or ("Duplicate entry" in err and "email" in err):
            err_msg = "Email address is already in use."
        elif "uq_users_student_id" in err or ("Duplicate entry" in err and "student_id" in err):
            err_msg = "Student ID is already in use."
        else:
            err_msg = err
        res = fail(err_msg)
        res["error"] = err_msg
        return res
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_user(user_id):
    """Delete a user account."""
    try:
        validate_user_id(user_id)
    except ValueError as exc:
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        if cursor.rowcount == 0:
            res = fail("User not found.")
            res["error"] = "User not found."
            return res
        conn.commit()
        return ok("User deleted successfully.")

    except Exception as exc:
        if conn:
            conn.rollback()
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
