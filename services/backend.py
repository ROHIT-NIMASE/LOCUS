"""
services/backend.py - THE SINGLE DOOR BETWEEN THE UI AND THE BACKEND.

UI files (ui/*.py) import ONLY this module:   from services import backend
and call e.g. backend.login_user(...).

This file contains no logic. It just re-exports the functions from the three
service files. Backend teammates edit those files, NOT this one:

    user_service.py     -> register_user, login_user
    seat_service.py     -> get_seat_statuses, get_available_seat_count
    booking_service.py  -> create_booking, get_user_bookings, get_current_booking,
                           cancel_booking, check_in, check_out
"""
from services.user_service import register_user, login_user
from services.seat_service import get_seat_statuses, get_available_seat_count
from services.booking_service import (create_booking, get_user_bookings, get_current_booking,
                                      cancel_booking, check_in, check_out)

__all__ = [
    "register_user", "login_user",
    "get_seat_statuses", "get_available_seat_count",
    "create_booking", "get_user_bookings", "get_current_booking",
    "cancel_booking", "check_in", "check_out",
]
