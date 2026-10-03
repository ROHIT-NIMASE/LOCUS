
"""Pure Python booking rules for LOCUS."""

from datetime import datetime

from logic.validation import (
    validate_positive_id,
    validate_booking_times,
)


# These statuses currently occupy a seat.
# Keep these values consistent with the final project schema.
ACTIVE_BOOKING_STATUSES = frozenset({
    "BOOKED",
    "CHECKED_IN",
})


def bookings_overlap(start1, end1, start2, end2):
    """
    Return True when two valid time ranges overlap.

    Adjacent reservations are allowed:
    10:00-11:00 and 11:00-12:00 do not overlap.
    """
    for start, end in ((start1, end1), (start2, end2)):
        if not isinstance(start, datetime):
            raise ValueError("Booking start must be a datetime object.")
        if not isinstance(end, datetime):
            raise ValueError("Booking end must be a datetime object.")
        if start.tzinfo != end.tzinfo:
            raise ValueError("Booking times must use compatible time zones.")
        if end <= start:
            raise ValueError("Booking end must be after booking start.")

    return start1 < end2 and end1 > start2


def is_seat_available(
    seat_id,
    start_time,
    end_time,
    existing_bookings,
):
    """
    Check availability against a collection of booking records.

    Each record must contain:
        seat_id: positive integer
        start_time: datetime
        end_time: datetime
        status: string

    Cancelled, completed, and no-show bookings do not block
    availability. Only ACTIVE_BOOKING_STATUSES block a seat.
    """
    validate_positive_id(seat_id, "Seat ID")

    if not isinstance(existing_bookings, (list, tuple)):
        raise ValueError("Existing bookings must be a list or tuple.")

    # Validate the requested range without assuming the real clock.
    # Actual future-time validation belongs to the booking service.
    if not isinstance(start_time, datetime):
        raise ValueError("Start time must be a datetime object.")
    if not isinstance(end_time, datetime):
        raise ValueError("End time must be a datetime object.")
    if start_time.tzinfo != end_time.tzinfo:
        raise ValueError("Booking times must use compatible time zones.")
    if end_time <= start_time:
        raise ValueError("End time must be after start time.")

    for booking in existing_bookings:
        if not isinstance(booking, dict):
            raise ValueError("Each booking must be a dictionary.")

        required = {"seat_id", "start_time", "end_time", "status"}
        if not required.issubset(booking):
            raise ValueError(
                "Each booking needs seat_id, start_time, "
                "end_time, and status."
            )

        validate_positive_id(booking["seat_id"], "Existing seat ID")

        status = booking["status"]
        if not isinstance(status, str):
            raise ValueError("Booking status must be a string.")

        if status.upper() not in ACTIVE_BOOKING_STATUSES:
            continue

        if booking["seat_id"] != seat_id:
            continue

        if bookings_overlap(
            start_time,
            end_time,
            booking["start_time"],
            booking["end_time"],
        ):
            return False

    return True
