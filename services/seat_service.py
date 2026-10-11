"""Seat-related database operations for LOCUS."""

from database.database import get_connection
from models.seat import Seat
from logic.validation import (
    validate_seat_id,
    validate_booking_date,
    validate_time_value,
    validate_time_range,
)


# ── Internal helper ──────────────────────────────────────────────────────────

def _row_to_seat(row):
    return Seat(
        seat_id     = row["seat_id"],
        seat_number = row["seat_number"],
        floor       = row["floor"],
        status      = row["status"],
    )


# ── Public API ───────────────────────────────────────────────────────────────

def get_all_seats():
    """Return a list of all Seat objects.

    Returns:
        list[Seat]  – on success
        list[]      – on error
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT seat_id, seat_number, floor, status "
            "FROM   seats "
            "ORDER BY floor, seat_number"
        )
        return [_row_to_seat(row) for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_available_seats(booking_date, start_time, end_time):
    """Return seats that can be booked for the given date/time window.

    A seat is available when:
      1. Its status is 'available' (not 'maintenance').
      2. It has no confirmed booking that overlaps [start_time, end_time]
         on booking_date.

    Overlap condition (adjacent bookings are allowed):
        existing_start < new_end  AND  existing_end > new_start

    Args:
        booking_date (date | str): The date to check ('YYYY-MM-DD').
        start_time   (time | str): Window start ('HH:MM' or 'HH:MM:SS').
        end_time     (time | str): Window end   ('HH:MM' or 'HH:MM:SS').

    Returns:
        dict – ``{"success": True,  "seats": [Seat, ...]}``
             – ``{"success": False, "error": "<reason>"}``
    """
    try:
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

        # Seats that are available and NOT blocked by a confirmed booking
        cursor.execute(
            """
            SELECT s.seat_id, s.seat_number, s.floor, s.status
            FROM   seats s
            WHERE  s.status = 'available'
              AND  s.seat_id NOT IN (
                       SELECT b.seat_id
                       FROM   bookings b
                       WHERE  b.booking_date = %s
                         AND  b.status       = 'confirmed'
                         AND  b.start_time   < %s
                         AND  b.end_time     > %s
                   )
            ORDER BY s.floor, s.seat_number
            """,
            (booking_date, end_time, start_time),
        )
        seats = [_row_to_seat(row) for row in cursor.fetchall()]
        return {"success": True, "seats": seats}

    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_seat_by_id(seat_id):
    """Return a Seat object for the given seat_id, or None.

    Returns:
        Seat | None
    """
    try:
        validate_seat_id(seat_id)
    except ValueError:
        return None

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT seat_id, seat_number, floor, status "
            "FROM   seats WHERE seat_id = %s",
            (seat_id,),
        )
        row = cursor.fetchone()
        return _row_to_seat(row) if row else None
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
