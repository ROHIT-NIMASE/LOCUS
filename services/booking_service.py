"""Booking-related database operations for LOCUS."""

from datetime import datetime, timedelta

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


# ── Internal helper ──────────────────────────────────────────────────────────

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


# ── Public API ───────────────────────────────────────────────────────────────

def create_booking(user_id, seat_id, booking_date, start_time, end_time):
    """Create a new booking inside a single MySQL transaction.

    Transaction steps:
        1. Validate all inputs.
        2. Verify seat exists.
        3. Verify seat is not under maintenance.
        4. Lock and re-check for overlapping confirmed bookings.
        5. INSERT booking.
        6. COMMIT  (or ROLLBACK on any failure).

    Args:
        user_id      (int):        The booking user.
        seat_id      (int):        The seat to book.
        booking_date (date | str): 'YYYY-MM-DD'.
        start_time   (time | str): 'HH:MM' or 'HH:MM:SS'.
        end_time     (time | str): 'HH:MM' or 'HH:MM:SS'.

    Returns:
        dict – ``{"success": True,  "booking_id": <id>}``
             – ``{"success": False, "error": "<reason>"}``
    """
    # ── Validate inputs ──────────────────────────────────────────────────────
    try:
        validate_user_id(user_id)
        validate_seat_id(seat_id)
        validate_booking_date(booking_date)
        validate_time_value(start_time, "start_time")
        validate_time_value(end_time,   "end_time")
        validate_time_range(start_time, end_time)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # ── Verify seat exists ───────────────────────────────────────────────
        cursor.execute(
            "SELECT seat_id, status FROM seats WHERE seat_id = %s FOR UPDATE",
            (seat_id,),
        )
        seat = cursor.fetchone()
        if not seat:
            return {"success": False, "error": "Seat not found."}

        # ── Verify seat is not under maintenance ─────────────────────────────
        if seat["status"] == "maintenance":
            return {"success": False, "error": "Seat is currently under maintenance."}

        # ── Check for overlapping confirmed bookings (with row lock) ─────────
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
            (seat_id, booking_date, end_time, start_time),
        )
        conflict = cursor.fetchone()
        if conflict:
            return {
                "success": False,
                "error": "Seat is already booked for the requested time period.",
            }

        # ── Verify user exists ───────────────────────────────────────────────
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            return {"success": False, "error": "User not found."}

        # ── Insert booking ───────────────────────────────────────────────────
        cursor.execute(
            """
            INSERT INTO bookings
                (user_id, seat_id, booking_date, start_time, end_time, status)
            VALUES (%s, %s, %s, %s, %s, 'confirmed')
            """,
            (user_id, seat_id, booking_date, start_time, end_time),
        )
        booking_id = cursor.lastrowid
        conn.commit()
        return {"success": True, "booking_id": booking_id}

    except Exception as exc:
        if conn:
            conn.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_user_bookings(user_id):
    """Return all bookings belonging to a user.

    Returns:
        dict – ``{"success": True,  "bookings": [Booking, ...]}``
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
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT b.booking_id, b.user_id, b.seat_id,
                   b.booking_date, b.start_time, b.end_time,
                   b.status, b.created_at,
                   s.seat_number, s.floor
            FROM   bookings b
            JOIN   seats    s ON s.seat_id = b.seat_id
            WHERE  b.user_id = %s
            ORDER BY b.booking_date DESC, b.start_time DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        bookings = []
        for row in rows:
            b = _row_to_booking(row)
            # Attach seat info as extra attributes for UI convenience
            b.seat_number = row["seat_number"]
            b.floor       = row["floor"]
            bookings.append(b)
        return {"success": True, "bookings": bookings}

    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_booking_by_id(booking_id):
    """Return a single Booking by its ID, or None.

    Returns:
        Booking | None
    """
    try:
        validate_booking_id(booking_id)
    except ValueError:
        return None

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT booking_id, user_id, seat_id,
                   booking_date, start_time, end_time, status, created_at
            FROM   bookings
            WHERE  booking_id = %s
            """,
            (booking_id,),
        )
        row = cursor.fetchone()
        return _row_to_booking(row) if row else None
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def cancel_booking(booking_id, user_id):
    """Cancel a booking by setting its status to 'cancelled'.

    Rules:
        * The booking must belong to user_id.
        * The booking must currently be 'confirmed'.
        * The record is NEVER deleted.

    Returns:
        dict – ``{"success": True}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
        validate_booking_id(booking_id)
        validate_user_id(user_id)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT booking_id, user_id, status FROM bookings WHERE booking_id = %s",
            (booking_id,),
        )
        booking = cursor.fetchone()

        if not booking:
            return {"success": False, "error": "Booking not found."}

        if booking["user_id"] != user_id:
            return {"success": False, "error": "You can only cancel your own bookings."}

        if booking["status"] == "cancelled":
            return {"success": False, "error": "Booking is already cancelled."}

        if booking["status"] != "confirmed":
            return {
                "success": False,
                "error": f"Cannot cancel a booking with status '{booking['status']}'.",
            }

        cursor.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE booking_id = %s",
            (booking_id,),
        )
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


def update_booking_status(booking_id, status):
    """Update the status of a booking.

    Intended for internal/admin use (e.g., marking bookings as completed
    or expired by a scheduled process).

    Returns:
        dict – ``{"success": True}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
        validate_booking_id(booking_id)
        validate_booking_status(status)
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE bookings SET status = %s WHERE booking_id = %s",
            (status, booking_id),
        )
        if cursor.rowcount == 0:
            return {"success": False, "error": "Booking not found."}

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
