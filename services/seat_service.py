"""
services/seat_service.py - seat layout and availability.

BACKEND INTEGRATION POINT: replace the BODY of each function with real code.
Seat status must be exactly: "available", "occupied" or "unavailable".
Seat IDs look like "A01" (letter = row, number = column) - the UI draws the grid from them.
"""
from mock_data import data as mock
from services.responses import ok


def _overlaps(start_a, end_a, start_b, end_b):
    """True if two time ranges overlap. 'HH:MM' text compares correctly."""
    return start_a < end_b and end_a > start_b


def seat_status(seat_id, booking_date, start_time, end_time):
    """Status of ONE seat for a date/time. (Also used by booking_service.create_booking.)"""
    if seat_id in mock.UNAVAILABLE_SEATS:
        return "unavailable"
    for booking in mock.BOOKINGS:
        if (booking["seat_id"] == seat_id
                and booking["date"] == booking_date
                and booking["status"] in ("Upcoming", "Active")
                and _overlaps(start_time, end_time, booking["start_time"], booking["end_time"])):
            return "occupied"
    return "available"


def get_seat_statuses(booking_date, start_time, end_time):
    # BACKEND INTEGRATION POINT
    # Real version: query all seats and mark each one using the bookings table
    # for the chosen date/time.
    # data = [{"seat_id": "A01", "status": "available"}, ...]
    statuses = [
        {"seat_id": seat_id,
         "status": seat_status(seat_id, booking_date, start_time, end_time)}
        for seat_id in mock.ALL_SEAT_IDS
    ]
    return ok(data=statuses)


def get_available_seat_count(booking_date, start_time, end_time):
    # BACKEND INTEGRATION POINT
    # The dashboard calls this with "now until one hour later", e.g. 06:11 - 07:11.
    # data = a number
    statuses = get_seat_statuses(booking_date, start_time, end_time)["data"]
    count = sum(1 for seat in statuses if seat["status"] == "available")
    return ok(data=count)
