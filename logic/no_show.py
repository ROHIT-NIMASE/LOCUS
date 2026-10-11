"""Attendance and no-show logic for LOCUS.

All attendance-related database operations live here.
Do NOT create a separate attendance.py file.
"""

from datetime import datetime, timedelta

from database.database import get_connection

# Grace period before a booking is marked as no-show
NO_SHOW_GRACE_MINUTES = 15


# ── Internal helper ──────────────────────────────────────────────────────────

def _get_booking(cursor, booking_id):
    """Return a booking row dict or None."""
    cursor.execute(
        "SELECT booking_id, user_id, seat_id, booking_date, "
        "       start_time, end_time, status "
        "FROM   bookings "
        "WHERE  booking_id = %s",
        (booking_id,),
    )
    return cursor.fetchone()


# ── Public API ───────────────────────────────────────────────────────────────

def check_in(booking_id):
    """Record a student's check-in for a confirmed booking.

    Returns:
        dict  – ``{"success": True, "attendance_id": <id>}``
              – ``{"success": False, "error": "<reason>"}``
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        booking = _get_booking(cursor, booking_id)
        if not booking:
            return {"success": False, "error": "Booking not found."}

        if booking["status"] != "confirmed":
            return {
                "success": False,
                "error": f"Cannot check in: booking status is '{booking['status']}'.",
            }

        # Check whether an attendance record already exists
        cursor.execute(
            "SELECT attendance_id, status FROM attendance WHERE booking_id = %s",
            (booking_id,),
        )
        existing = cursor.fetchone()

        if existing:
            if existing["status"] == "present":
                return {"success": False, "error": "Already checked in."}
            # Attendance exists but was pre-created as no_show – allow override
            # only if the grace period hasn't truly elapsed (edge case).
            cursor.execute(
                "UPDATE attendance "
                "SET    check_in_time = %s, status = 'present' "
                "WHERE  booking_id = %s",
                (datetime.now(), booking_id),
            )
        else:
            cursor.execute(
                "INSERT INTO attendance (booking_id, check_in_time, status) "
                "VALUES (%s, %s, 'present')",
                (booking_id, datetime.now()),
            )

        attendance_id = existing["attendance_id"] if existing else cursor.lastrowid
        conn.commit()
        return {"success": True, "attendance_id": attendance_id}

    except Exception as exc:
        if conn:
            conn.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def check_out(booking_id):
    """Record a student's check-out time.

    Returns:
        dict – ``{"success": True}``
             – ``{"success": False, "error": "<reason>"}``
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT attendance_id, status, check_in_time "
            "FROM   attendance "
            "WHERE  booking_id = %s",
            (booking_id,),
        )
        record = cursor.fetchone()

        if not record:
            return {"success": False, "error": "No attendance record found – check in first."}

        if record["status"] != "present":
            return {"success": False, "error": "Cannot check out: student not marked as present."}

        cursor.execute(
            "UPDATE attendance "
            "SET    check_out_time = %s "
            "WHERE  booking_id = %s",
            (datetime.now(), booking_id),
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


def get_attendance(booking_id):
    """Return the attendance record for a booking, or None.

    Returns:
        dict | None
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT attendance_id, booking_id, check_in_time, "
            "       check_out_time, status "
            "FROM   attendance "
            "WHERE  booking_id = %s",
            (booking_id,),
        )
        return cursor.fetchone()
    except Exception:
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def mark_no_show(booking_id):
    """Mark a booking as no-show if the grace period has elapsed.

    Grace period: NO_SHOW_GRACE_MINUTES after booking start_time.

    The function checks the current wall-clock time against the booking's
    date + start_time. If the grace period has passed and the student has
    not checked in, both the attendance and booking records are updated.

    Returns:
        dict – ``{"success": True,  "marked": True}``   – successfully marked
             – ``{"success": True,  "marked": False}``  – grace period still active
             – ``{"success": False, "error": "<reason>"}``
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        booking = _get_booking(cursor, booking_id)
        if not booking:
            return {"success": False, "error": "Booking not found."}

        if booking["status"] != "confirmed":
            return {
                "success": False,
                "error": f"Booking status is '{booking['status']}'; cannot mark no-show.",
            }

        # Reconstruct the booking start datetime
        booking_date = booking["booking_date"]      # datetime.date
        start_time   = booking["start_time"]        # datetime.timedelta (MySQL TIME)

        # MySQL TIME columns come back as timedelta in mysql-connector-python
        if isinstance(start_time, timedelta):
            start_dt = datetime.combine(booking_date, datetime.min.time()) + start_time
        else:
            start_dt = datetime.combine(booking_date, start_time)

        deadline = start_dt + timedelta(minutes=NO_SHOW_GRACE_MINUTES)
        now = datetime.now()

        if now <= deadline:
            return {"success": True, "marked": False}   # grace period still active

        # Check whether already checked in
        cursor.execute(
            "SELECT attendance_id, status FROM attendance WHERE booking_id = %s",
            (booking_id,),
        )
        attendance = cursor.fetchone()

        if attendance and attendance["status"] == "present":
            return {"success": True, "marked": False}   # student is present

        # Mark no-show
        if attendance:
            cursor.execute(
                "UPDATE attendance SET status = 'no_show' WHERE booking_id = %s",
                (booking_id,),
            )
        else:
            cursor.execute(
                "INSERT INTO attendance (booking_id, status) VALUES (%s, 'no_show')",
                (booking_id,),
            )

        cursor.execute(
            "UPDATE bookings SET status = 'no_show' WHERE booking_id = %s",
            (booking_id,),
        )

        conn.commit()
        return {"success": True, "marked": True}

    except Exception as exc:
        if conn:
            conn.rollback()
        return {"success": False, "error": str(exc)}
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
