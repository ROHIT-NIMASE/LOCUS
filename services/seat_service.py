"""Seat-related database operations for LOCUS."""

from database.database import get_connection
from models.seat import Seat
from logic.validation import (
    validate_seat_id,
    validate_booking_date,
    validate_time_value,
    validate_time_range,
)
from services.responses import ok, fail


# ── Internal helper ──────────────────────────────────────────────────────────

def _row_to_seat(row):
    return Seat(
        seat_id     = row["seat_id"],
        seat_number = row["seat_number"],
        floor       = row["floor"],
        status      = row["status"],
    )


def _overlaps(start_a, end_a, start_b, end_b):
    """True if two time ranges overlap. HH:MM text / time objects compare correctly."""
    return str(start_a) < str(end_b) and str(end_a) > str(start_b)


# ── Public API ───────────────────────────────────────────────────────────────

def get_all_seats():
    """Return a list of all Seat model objects."""
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
    """
    try:
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
        res = ok("Available seats loaded.", seats)
        res["seats"] = seats
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


def get_seat_by_id(seat_id):
    """Return a Seat object for the given seat_id or seat_number, or None."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if isinstance(seat_id, int) or (isinstance(seat_id, str) and seat_id.isdigit()):
            cursor.execute(
                "SELECT seat_id, seat_number, floor, status FROM seats WHERE seat_id = %s",
                (int(seat_id),),
            )
        else:
            cursor.execute(
                "SELECT seat_id, seat_number, floor, status FROM seats WHERE seat_number = %s",
                (str(seat_id).strip(),),
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


def seat_status(seat_id, booking_date, start_time, end_time):
    """Status of ONE seat for a given date/time: 'available', 'occupied', or 'unavailable'."""
    seat = get_seat_by_id(seat_id)
    if not seat or seat.status == "maintenance":
        return "unavailable"

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT booking_id
            FROM   bookings
            WHERE  seat_id      = %s
              AND  booking_date = %s
              AND  status       = 'confirmed'
              AND  start_time   < %s
              AND  end_time     > %s
            LIMIT 1
            """,
            (seat.seat_id, booking_date, end_time, start_time),
        )
        return "occupied" if cursor.fetchone() else "available"
    except Exception:
        return "unavailable"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_seat_statuses(booking_date, start_time, end_time):
    """Return status of all seats for the UI seat layout grid.

    Returns:
        dict – ok(data=[{"seat_id": "A01", "status": "available"|"occupied"|"unavailable"}])
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Fetch all seats
        cursor.execute(
            "SELECT seat_id, seat_number, floor, status "
            "FROM   seats "
            "ORDER BY floor, seat_number"
        )
        all_seats = cursor.fetchall()

        # 2. Fetch occupied seat IDs for the date/time range
        cursor.execute(
            """
            SELECT DISTINCT seat_id
            FROM   bookings
            WHERE  booking_date = %s
              AND  status       = 'confirmed'
              AND  start_time   < %s
              AND  end_time     > %s
            """,
            (booking_date, end_time, start_time),
        )
        occupied_seat_ids = {row["seat_id"] for row in cursor.fetchall()}

        statuses = []
        for s in all_seats:
            if s["status"] == "maintenance":
                st = "unavailable"
            elif s["seat_id"] in occupied_seat_ids:
                st = "occupied"
            else:
                st = "available"

            statuses.append({
                "seat_id":     s["seat_number"],   # UI grid requires alphanumeric ID like 'A01'
                "seat_number": s["seat_number"],
                "db_seat_id":  s["seat_id"],
                "status":      st,
            })

        return ok("Seat statuses loaded.", statuses)

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


def get_available_seat_count(booking_date, start_time, end_time):
    """Return the number of seats available for the given date and time range."""
    result = get_seat_statuses(booking_date, start_time, end_time)
    if not result["success"]:
        return result

    count = sum(1 for seat in result["data"] if seat["status"] == "available")
    return ok("Available seat count loaded.", count)
