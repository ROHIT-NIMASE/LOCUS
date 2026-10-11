"""Booking-related database operations for LOCUS."""

from datetime import datetime, timedelta, time, date

from database.database import get_connection
from models.booking import Booking, VALID_STATUSES
from logic.validation import (
    validate_user_id,
    validate_seat_id,
    validate_booking_id,
    validate_booking_date,
    validate_time_value,
    validate_time_range,
    validate_booking_status,
)
from services.responses import ok, fail
from logic import no_show


# ── Internal helpers ─────────────────────────────────────────────────────────

def _format_time(t):
    """Format time object / timedelta / string to 'HH:MM'."""
    if isinstance(t, timedelta):
        total_seconds = int(t.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    if isinstance(t, (time, datetime)):
        return t.strftime("%H:%M")
    if isinstance(t, str):
        return t[:5]
    return str(t)


def _parse_booking_id(booking_id):
    """Extract numeric booking_id from int or string like 'BK0001' or '1'."""
    s = str(booking_id).strip()
    if s.upper().startswith("BK"):
        return int(s[2:])
    return int(s)


def _row_to_booking(row):
    return Booking(
        booking_id   = row["booking_id"],
        user_id      = row["user_id"],
        seat_id      = row["seat_id"],
        booking_date = row["booking_date"],
        start_time   = row["start_time"],
        end_time     = row["end_time"],
        status       = row["status"],
        created_at   = row.get("created_at"),
    )


def _derive_ui_status(db_status, attendance_status=None, check_out_time=None):
    """Map DB status and attendance record to the UI's expected status:
    'Upcoming', 'Active', 'Completed', 'Cancelled', 'No-show'
    """
    if db_status == "confirmed":
        if attendance_status == "present":
            if check_out_time is not None:
                return "Completed"
            return "Active"
        return "Upcoming"
    if db_status == "completed":
        return "Completed"
    if db_status == "cancelled":
        return "Cancelled"
    if db_status == "no_show":
        return "No-show"
    if db_status == "expired":
        return "Completed"
    return db_status.capitalize()


def _row_to_booking_dict(row):
    """Convert DB row to the dictionary expected by frontend components."""
    ui_status = _derive_ui_status(
        row.get("status"),
        row.get("attendance_status"),
        row.get("check_out_time"),
    )
    b_id = row["booking_id"]
    seat_num = row.get("seat_number", str(row["seat_id"]))

    return {
        "booking_id":   f"BK{b_id:04d}",
        "id":           b_id,
        "user_id":      row["user_id"],
        "seat_id":      seat_num,         # UI displays seat label like 'A01'
        "seat_number":  seat_num,
        "floor":        row.get("floor"),
        "date":         str(row["booking_date"]),
        "booking_date": str(row["booking_date"]),
        "start_time":   _format_time(row["start_time"]),
        "end_time":     _format_time(row["end_time"]),
        "status":       ui_status,
        "db_status":    row["status"],
        "created_at":   str(row["created_at"]) if row.get("created_at") else None,
    }


# ── Public API ───────────────────────────────────────────────────────────────

def create_booking(user_id, seat_id, booking_date, start_time, end_time):
    """Create a new booking inside a single MySQL transaction.

    Supports seat_id as int or seat label string (e.g. 'A01').
    Uses row-level locking (FOR UPDATE) to prevent double bookings.
    """
    try:
        validate_user_id(user_id)
        validate_booking_date(booking_date)
        validate_time_value(start_time, "start_time")
        validate_time_value(end_time,   "end_time")
        validate_time_range(start_time, end_time)
    except ValueError as exc:
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Resolve and verify seat exists (supports int ID or 'A01' string)
        if isinstance(seat_id, int) or (isinstance(seat_id, str) and seat_id.isdigit()):
            cursor.execute(
                "SELECT seat_id, seat_number, status FROM seats WHERE seat_id = %s FOR UPDATE",
                (int(seat_id),),
            )
        else:
            cursor.execute(
                "SELECT seat_id, seat_number, status FROM seats WHERE seat_number = %s FOR UPDATE",
                (str(seat_id).strip(),),
            )
        seat = cursor.fetchone()
        if not seat:
            res = fail("Seat not found.")
            res["error"] = "Seat not found."
            return res

        real_seat_id = seat["seat_id"]
        seat_number = seat["seat_number"]

        # 2. Check maintenance
        if seat["status"] == "maintenance":
            res = fail("Seat is currently under maintenance.")
            res["error"] = "Seat is currently under maintenance."
            return res

        # 3. Check for overlapping confirmed bookings (row-locked)
        cursor.execute(
            """
            SELECT booking_id
            FROM   bookings
            WHERE  seat_id      = %s
              AND  booking_date = %s
              AND  status       = 'confirmed'
              AND  start_time   < %s
              AND  end_time     > %s
            FOR UPDATE
            """,
            (real_seat_id, booking_date, end_time, start_time),
        )
        if cursor.fetchone():
            err_msg = "Seat is already booked for the requested time period."
            res = fail(err_msg)
            res["error"] = err_msg
            return res

        # 4. Verify user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            res = fail("User not found.")
            res["error"] = "User not found."
            return res

        # 5. Insert booking
        cursor.execute(
            """
            INSERT INTO bookings
                (user_id, seat_id, booking_date, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, %s, 'confirmed')
            """,
            (user_id, real_seat_id, booking_date, start_time, end_time),
        )
        booking_id = cursor.lastrowid
        conn.commit()

        booking_dict = {
            "booking_id":   f"BK{booking_id:04d}",
            "id":           booking_id,
            "user_id":      user_id,
            "seat_id":      seat_number,
            "seat_number":  seat_number,
            "date":         str(booking_date),
            "booking_date": str(booking_date),
            "start_time":   _format_time(start_time),
            "end_time":     _format_time(end_time),
            "status":       "Upcoming",
        }

        res = ok("Booking confirmed.", booking_dict)
        res["booking_id"] = booking_id
        return res

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


def get_user_bookings(user_id):
    """Return all bookings for a user.

    Returns:
        dict – unified response with:
            data: list of booking dicts (for frontend)
            bookings: list of Booking model instances (for backend tests)
    """
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
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT b.booking_id, b.user_id, b.seat_id,
                   b.booking_date, b.start_time, b.end_time,
                   b.status, b.created_at,
                   s.seat_number, s.floor,
                   a.status AS attendance_status, a.check_in_time, a.check_out_time
            FROM   bookings b
            JOIN   seats    s ON s.seat_id = b.seat_id
            LEFT JOIN attendance a ON a.booking_id = b.booking_id
            WHERE  b.user_id = %s
            ORDER BY b.booking_date DESC, b.start_time DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        booking_models = []
        booking_dicts = []

        for row in rows:
            b_model = _row_to_booking(row)
            b_model.seat_number = row["seat_number"]
            b_model.floor       = row["floor"]
            booking_models.append(b_model)

            booking_dicts.append(_row_to_booking_dict(row))

        res = ok("Bookings loaded.", booking_dicts)
        res["bookings"] = booking_models
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


def get_current_booking(user_id):
    """Return the Active booking if present, otherwise the soonest Upcoming booking."""
    result = get_user_bookings(user_id)
    if not result["success"]:
        return result

    bookings = result["data"]
    # 1. Look for Active (checked-in) booking
    for b in bookings:
        if b["status"] == "Active":
            return ok("Current active booking loaded.", b)

    # 2. Look for soonest Upcoming booking
    upcoming = [b for b in bookings if b["status"] == "Upcoming"]
    if upcoming:
        upcoming.sort(key=lambda x: (x["date"], x["start_time"]))
        return ok("Next upcoming booking loaded.", upcoming[0])

    return ok("No current booking.", None)


def get_booking_by_id(booking_id):
    """Return a single Booking model instance by its ID, or None."""
    try:
        numeric_id = _parse_booking_id(booking_id)
        validate_booking_id(numeric_id)
    except Exception:
        return None

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT b.booking_id, b.user_id, b.seat_id,
                   b.booking_date, b.start_time, b.end_time, b.status, b.created_at,
                   s.seat_number, s.floor
            FROM   bookings b
            JOIN   seats s ON s.seat_id = b.seat_id
            WHERE  b.booking_id = %s
            """,
            (numeric_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        b_model = _row_to_booking(row)
        b_model.seat_number = row["seat_number"]
        b_model.floor       = row["floor"]
        return b_model
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def cancel_booking(booking_id, user_id=None):
    """Cancel a booking by setting status to 'cancelled'.

    If user_id is provided, checks that the booking belongs to user_id.
    """
    try:
        numeric_id = _parse_booking_id(booking_id)
        validate_booking_id(numeric_id)
        if user_id is not None:
            validate_user_id(user_id)
    except Exception as exc:
        err_msg = str(exc)
        res = fail(err_msg)
        res["error"] = err_msg
        return res

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT b.booking_id, b.user_id, b.seat_id, b.booking_date,
                   b.start_time, b.end_time, b.status, s.seat_number
            FROM   bookings b
            JOIN   seats s ON s.seat_id = b.seat_id
            WHERE  b.booking_id = %s
            """,
            (numeric_id,),
        )
        booking = cursor.fetchone()

        if not booking:
            res = fail("Booking not found.")
            res["error"] = "Booking not found."
            return res

        if user_id is not None and booking["user_id"] != user_id:
            err_msg = "You can only cancel your own bookings."
            res = fail(err_msg)
            res["error"] = err_msg
            return res

        if booking["status"] == "cancelled":
            err_msg = "Booking is already cancelled."
            res = fail(err_msg)
            res["error"] = err_msg
            return res

        if booking["status"] != "confirmed":
            err_msg = "Only upcoming bookings can be cancelled."
            res = fail(err_msg)
            res["error"] = err_msg
            return res

        cursor.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
            (numeric_id,),
        )
        conn.commit()

        booking["status"] = "cancelled"
        updated_dict = _row_to_booking_dict(booking)
        return ok("Booking cancelled.", updated_dict)

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


def check_in(booking_id):
    """Check in to a confirmed booking."""
    try:
        numeric_id = _parse_booking_id(booking_id)
    except Exception:
        return fail("Invalid booking ID.")

    # 1. Use existing no_show check_in logic
    checkin_res = no_show.check_in(numeric_id)
    if not checkin_res["success"]:
        return fail(checkin_res.get("error", "Check-in failed."))

    # 2. Fetch updated booking
    b_model = get_booking_by_id(numeric_id)
    if not b_model:
        return fail("Booking not found.")

    b_dict = {
        "booking_id":   f"BK{numeric_id:04d}",
        "id":           numeric_id,
        "user_id":      b_model.user_id,
        "seat_id":      getattr(b_model, "seat_number", str(b_model.seat_id)),
        "seat_number":  getattr(b_model, "seat_number", str(b_model.seat_id)),
        "date":         str(b_model.booking_date),
        "booking_date": str(b_model.booking_date),
        "start_time":   _format_time(b_model.start_time),
        "end_time":     _format_time(b_model.end_time),
        "status":       "Active",
    }
    return ok("Checked in successfully.", b_dict)


def check_out(booking_id):
    """Check out from an active booking."""
    try:
        numeric_id = _parse_booking_id(booking_id)
    except Exception:
        return fail("Invalid booking ID.")

    checkout_res = no_show.check_out(numeric_id)
    if not checkout_res["success"]:
        return fail(checkout_res.get("error", "Check-out failed."))

    # Update booking status to completed
    update_booking_status(numeric_id, "completed")

    b_model = get_booking_by_id(numeric_id)
    b_dict = {
        "booking_id":   f"BK{numeric_id:04d}",
        "id":           numeric_id,
        "user_id":      b_model.user_id,
        "seat_id":      getattr(b_model, "seat_number", str(b_model.seat_id)),
        "seat_number":  getattr(b_model, "seat_number", str(b_model.seat_id)),
        "date":         str(b_model.booking_date),
        "booking_date": str(b_model.booking_date),
        "start_time":   _format_time(b_model.start_time),
        "end_time":     _format_time(b_model.end_time),
        "status":       "Completed",
    }
    return ok("Checked out successfully.", b_dict)


def update_booking_status(booking_id, status):
    """Update status column of a booking in MySQL."""
    try:
        numeric_id = _parse_booking_id(booking_id)
        validate_booking_id(numeric_id)
        validate_booking_status(status)
    except Exception as exc:
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
            "UPDATE bookings SET status = %s WHERE booking_id = %s",
            (status, numeric_id),
        )
        if cursor.rowcount == 0:
            res = fail("Booking not found.")
            res["error"] = "Booking not found."
            return res
        conn.commit()
        return ok("Status updated successfully.")

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
