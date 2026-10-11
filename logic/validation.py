"""Input validation for the LOCUS desk reservation system."""

import re
from datetime import datetime, date, time

from models.booking import VALID_STATUSES


# ── Identifiers ─────────────────────────────────────────────────────────────

def validate_positive_id(value, field_name="ID"):
    """Validate a positive integer identifier."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return True


def validate_user_id(user_id):
    """Raise ValueError if user_id is not a valid positive integer."""
    return validate_positive_id(user_id, "User ID")


def validate_seat_id(seat_id):
    """Raise ValueError if seat_id is not a valid positive integer."""
    return validate_positive_id(seat_id, "Seat ID")


def validate_booking_id(booking_id):
    """Raise ValueError if booking_id is not a valid positive integer."""
    return validate_positive_id(booking_id, "Booking ID")


# ── User fields ──────────────────────────────────────────────────────────────

def validate_name(name):
    """Raise ValueError if name is empty or not a string."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Name must be a non-empty string.")
    return True


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email):
    """Raise ValueError if email does not look like a valid address."""
    if not isinstance(email, str) or not _EMAIL_RE.match(email.strip()):
        raise ValueError("A valid email address is required.")
    return True


def validate_student_id(student_id):
    """Raise ValueError if student_id is empty or not a string."""
    if not isinstance(student_id, str) or not student_id.strip():
        raise ValueError("Student ID must be a non-empty string.")
    return True


def validate_password(password):
    """Raise ValueError if password is empty or not a string."""
    if not isinstance(password, str) or not password.strip():
        raise ValueError("Password must be a non-empty string.")
    return True


# ── Booking fields ───────────────────────────────────────────────────────────

def validate_booking_date(booking_date):
    """Accept a ``datetime.date`` object or an ISO 'YYYY-MM-DD' string."""
    if isinstance(booking_date, date):
        return True
    if isinstance(booking_date, str):
        try:
            datetime.strptime(booking_date, "%Y-%m-%d")
            return True
        except ValueError:
            pass
    raise ValueError("Booking date must be a date object or 'YYYY-MM-DD' string.")


def validate_time_value(t, field_name="Time"):
    """Accept a ``datetime.time`` object or an 'HH:MM' / 'HH:MM:SS' string."""
    if isinstance(t, time):
        return True
    if isinstance(t, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                datetime.strptime(t, fmt)
                return True
            except ValueError:
                continue
    raise ValueError(
        f"{field_name} must be a time object or 'HH:MM' / 'HH:MM:SS' string."
    )


def validate_time_range(start_time, end_time):
    """Raise ValueError if start_time >= end_time.

    Accepts both ``datetime.time`` objects and HH:MM strings.
    """
    def _to_time(t):
        if isinstance(t, time):
            return t
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(t, fmt).time()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse time value: {t!r}")

    s = _to_time(start_time)
    e = _to_time(end_time)
    if s >= e:
        raise ValueError("start_time must be earlier than end_time.")
    return True


def validate_booking_status(status):
    """Raise ValueError if status is not one of the recognised booking statuses."""
    if not isinstance(status, str) or status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid booking status {status!r}. "
            f"Must be one of: {sorted(VALID_STATUSES)}."
        )
    return True


# ── Legacy helper kept for existing tests ────────────────────────────────────

def validate_booking_times(start_time, end_time, now=None):
    """
    Validate a booking time range.

    Both times must be datetime objects, must use compatible
    timezone information, and the start must be in the future.

    The optional 'now' parameter makes testing deterministic.
    """
    if not isinstance(start_time, datetime):
        raise ValueError("Start time must be a datetime object.")

    if not isinstance(end_time, datetime):
        raise ValueError("End time must be a datetime object.")

    if start_time.tzinfo != end_time.tzinfo:
        raise ValueError(
            "Start and end times must use compatible time zones."
        )

    if end_time <= start_time:
        raise ValueError("End time must be after start time.")

    if now is None:
        now = datetime.now(start_time.tzinfo)

    if not isinstance(now, datetime):
        raise ValueError("'now' must be a datetime object.")

    if now.tzinfo != start_time.tzinfo:
        raise ValueError(
            "Current time and booking time must use compatible time zones."
        )

    if start_time <= now:
        raise ValueError("Booking start time must be in the future.")

    return True
