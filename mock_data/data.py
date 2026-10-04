"""
mock_data/data.py - TEMPORARY dummy data so the UI can be demonstrated.
Only services/backend.py imports this file. When the real MySQL backend is
connected, this whole folder can be deleted.
"""
from datetime import date

# ---- Seat layout settings (change these to grow the library) ----
SEAT_ROWS = "ABCD"      # rows A, B, C, D
SEATS_PER_ROW = 4       # columns 1..4  ->  A01 ... D04
ALL_SEAT_IDS = [f"{row}{col:02d}" for row in SEAT_ROWS for col in range(1, SEATS_PER_ROW + 1)]

# Seats closed by the library (e.g. broken chair, reserved) - always unavailable
UNAVAILABLE_SEATS = ["A04", "C04"]

# ---- Demo account (password is plain text ONLY because this is mock data) ----
USERS = [
    {"user_id": 1, "full_name": "Demo Student", "student_id": "S1001",
     "email": "student@locus.edu", "username": "student", "password": "locus123"},
]

# ---- Demo bookings. Dates use today so the demo always looks current ----
_today = date.today().isoformat()
BOOKINGS = [
    # Bookings by OTHER students (make some seats show as occupied)
    {"booking_id": "BK0001", "user_id": 99, "seat_id": "A02", "date": _today,
     "start_time": "09:00", "end_time": "21:00", "status": "Active"},
    {"booking_id": "BK0002", "user_id": 98, "seat_id": "B03", "date": _today,
     "start_time": "09:00", "end_time": "21:00", "status": "Upcoming"},
    {"booking_id": "BK0003", "user_id": 97, "seat_id": "C01", "date": _today,
     "start_time": "09:00", "end_time": "21:00", "status": "Upcoming"},
    {"booking_id": "BK0004", "user_id": 96, "seat_id": "D04", "date": _today,
     "start_time": "09:00", "end_time": "21:00", "status": "Active"},
]
