"""
services/responses.py - the two helpers that build the dictionary every service
function returns. Backend functions should use these so the UI always gets the same shape.

    ok("Booking confirmed.", booking)  ->  {"success": True,  "message": "...", "data": booking}
    fail("Seat already taken.")        ->  {"success": False, "message": "...", "data": None}
"""


def ok(message="", data=None):
    return {"success": True, "message": message, "data": data}


def fail(message):
    return {"success": False, "message": message, "data": None}
