"""
services/booking_service.py - create, list, cancel bookings; check-in and check-out.

BACKEND INTEGRATION POINT: replace the BODY of each function with real code.
Booking status must be exactly: "Upcoming", "Active", "Completed", "Cancelled" or "No-show".
A booking dictionary is:
    {"booking_id", "user_id", "seat_id", "date", "start_time", "end_time", "status"}
Rules such as booking limits, check-in time window and no-show handling belong HERE
(or in logic/), not in the UI.
"""
from mock_data import data as mock
from services import seat_service
from services.responses import ok, fail


def create_booking(user_id, seat_id, booking_date, start_time, end_time):
    # BACKEND INTEGRATION POINT
    # Real version: re-check the seat is free (someone may have booked it a second
    # ago), apply booking rules, INSERT the booking.
    # data = the new booking dictionary (with its booking_id)
    if end_time <= start_time:
        return fail("End time must be after start time.")

    if seat_service.seat_status(seat_id, booking_date, start_time, end_time) != "available":
        return fail(f"Seat {seat_id} is no longer available for that time.")

    new_booking = {
        "booking_id": f"BK{len(mock.BOOKINGS) + 1:04d}",
        "user_id": user_id,
        "seat_id": seat_id,
        "date": booking_date,
        "start_time": start_time,
        "end_time": end_time,
        "status": "Upcoming",
    }
    mock.BOOKINGS.append(new_booking)
    return ok("Booking confirmed.", new_booking)


def get_user_bookings(user_id):
    # BACKEND INTEGRATION POINT
    # data = list of booking dictionaries for this user (newest first)
    mine = [b for b in mock.BOOKINGS if b["user_id"] == user_id]
    mine.sort(key=lambda b: (b["date"], b["start_time"]), reverse=True)
    return ok(data=mine)


def get_current_booking(user_id):
    # BACKEND INTEGRATION POINT
    # The booking shown on the dashboard / check-in / check-out screens:
    # the Active one if there is one, otherwise the soonest Upcoming one.
    # data = booking dictionary, or None if the user has nothing current.
    mine = [b for b in mock.BOOKINGS if b["user_id"] == user_id]
    for booking in mine:
        if booking["status"] == "Active":
            return ok(data=booking)
    upcoming = sorted((b for b in mine if b["status"] == "Upcoming"),
                      key=lambda b: (b["date"], b["start_time"]))
    return ok(data=upcoming[0] if upcoming else None)


def _find_booking(booking_id):
    for booking in mock.BOOKINGS:
        if booking["booking_id"] == booking_id:
            return booking
    return None


def cancel_booking(booking_id):
    # BACKEND INTEGRATION POINT
    booking = _find_booking(booking_id)
    if booking is None:
        return fail("Booking not found.")
    if booking["status"] != "Upcoming":
        return fail("Only upcoming bookings can be cancelled.")
    booking["status"] = "Cancelled"
    return ok("Booking cancelled.", booking)


def check_in(booking_id):
    # BACKEND INTEGRATION POINT
    # Real version: the check-in time window / no-show rules are the backend's job.
    booking = _find_booking(booking_id)
    if booking is None:
        return fail("Booking not found.")
    if booking["status"] != "Upcoming":
        return fail("This booking cannot be checked in.")
    booking["status"] = "Active"
    return ok("Checked in successfully.", booking)


def check_out(booking_id):
    # BACKEND INTEGRATION POINT
    booking = _find_booking(booking_id)
    if booking is None:
        return fail("Booking not found.")
    if booking["status"] != "Active":
        return fail("You are not checked in to this booking.")
    booking["status"] = "Completed"
    return ok("Checked out successfully.", booking)
