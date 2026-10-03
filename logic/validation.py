
"""Input validation for the LOCUS desk reservation system."""

from datetime import datetime


def validate_positive_id(value, field_name="ID"):
    """Validate a positive integer identifier."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")

    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    return True


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
