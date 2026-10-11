"""Integration tests for LOCUS backend (requires a live MySQL connection).

Run from the LOCUS/ directory:
    python -m pytest tests/test_backend.py -v

Or directly:
    python tests/test_backend.py

These tests hit the real 'library_hotdesking' database.
A temporary test user and bookings are created and cleaned up after each run.
"""

import sys
import os
import unittest
from datetime import date, timedelta

# Allow imports from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.user_service    import register_user, login_user, get_user_by_id
from services.seat_service    import get_all_seats, get_available_seats, get_seat_by_id
from services.booking_service import (
    create_booking,
    get_user_bookings,
    get_booking_by_id,
    cancel_booking,
)
from logic.no_show import check_in, check_out, get_attendance, mark_no_show
from database.database import get_connection


# ── Helpers ──────────────────────────────────────────────────────────────────

TOMORROW = (date.today() + timedelta(days=1)).isoformat()   # 'YYYY-MM-DD'

TEST_EMAIL_A  = "test_user_a@locus.test"
TEST_EMAIL_B  = "test_user_b@locus.test"
TEST_SID_A    = "TEST_SID_001"
TEST_SID_B    = "TEST_SID_002"


def _cleanup():
    """Remove test data left over from a previous run."""
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM users WHERE email IN (%s, %s)", (TEST_EMAIL_A, TEST_EMAIL_B))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


# ── Test cases ───────────────────────────────────────────────────────────────

class TestUserRegistration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _cleanup()

    # 1. Register new user → success
    def test_01_register_new_user(self):
        result = register_user("Alice Test", TEST_EMAIL_A, TEST_SID_A, "password123")
        self.assertTrue(result["success"], result)
        self.assertIn("user_id", result)
        TestUserRegistration.user_a_id = result["user_id"]

    # 2. Register duplicate email → rejected
    def test_02_duplicate_email(self):
        result = register_user("Alice Again", TEST_EMAIL_A, "DIFF_SID_999", "pass")
        self.assertFalse(result["success"])
        self.assertIn("email", result["error"].lower())

    # 3. Register duplicate student ID → rejected
    def test_03_duplicate_student_id(self):
        result = register_user("Bob Test", "bob@locus.test", TEST_SID_A, "pass")
        self.assertFalse(result["success"])

    # 4. Correct login → success
    def test_04_correct_login(self):
        result = login_user(TEST_EMAIL_A, "password123")
        self.assertTrue(result["success"], result)
        self.assertIsNotNone(result["user"])

    # 5. Wrong password → rejected
    def test_05_wrong_password(self):
        result = login_user(TEST_EMAIL_A, "wrongpassword")
        self.assertFalse(result["success"])


class TestSeats(unittest.TestCase):

    # 6. Fetch all seats
    def test_06_get_all_seats(self):
        seats = get_all_seats()
        self.assertIsInstance(seats, list)
        self.assertGreater(len(seats), 0)

    # 7. Fetch available seats
    def test_07_get_available_seats(self):
        result = get_available_seats(TOMORROW, "09:00", "10:00")
        self.assertTrue(result["success"], result)
        self.assertIsInstance(result["seats"], list)

    # 8. Seat 1 should exist and have a status
    def test_08_get_seat_by_id(self):
        seat = get_seat_by_id(1)
        self.assertIsNotNone(seat)
        self.assertIn(seat.status, ("available", "maintenance"))


class TestBooking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure test users exist
        r = register_user("Alice Test", TEST_EMAIL_A, TEST_SID_A, "password123")
        cls.user_a_id = r.get("user_id") or get_user_by_id_by_email(TEST_EMAIL_A)

        r2 = register_user("Bob Test", TEST_EMAIL_B, TEST_SID_B, "password456")
        cls.user_b_id = r2.get("user_id") or get_user_by_id_by_email(TEST_EMAIL_B)

        # Pick the first available seat
        result = get_available_seats(TOMORROW, "10:00", "12:00")
        cls.seat_id = result["seats"][0].seat_id if result["success"] and result["seats"] else 1

    # 9. Book available seat → success
    def test_09_book_seat(self):
        result = create_booking(
            self.user_a_id, self.seat_id, TOMORROW, "10:00", "12:00"
        )
        self.assertTrue(result["success"], result)
        TestBooking.booking_a_id = result["booking_id"]

    # 10. Book same seat for overlapping time → rejected
    def test_10_overlap_rejected(self):
        result = create_booking(
            self.user_a_id, self.seat_id, TOMORROW, "11:00", "13:00"
        )
        self.assertFalse(result["success"])
        self.assertIn("booked", result["error"].lower())

    # 11. Book same seat for non-overlapping time → allowed
    def test_11_non_overlap_allowed(self):
        result = create_booking(
            self.user_a_id, self.seat_id, TOMORROW, "12:00", "14:00"
        )
        self.assertTrue(result["success"], result)
        TestBooking.booking_adjacent_id = result["booking_id"]

    # 12. View user's bookings
    def test_12_view_user_bookings(self):
        result = get_user_bookings(self.user_a_id)
        self.assertTrue(result["success"], result)
        self.assertGreater(len(result["bookings"]), 0)

    # 13. Cancel own booking → success
    def test_13_cancel_own_booking(self):
        result = cancel_booking(self.booking_a_id, self.user_a_id)
        self.assertTrue(result["success"], result)

    # 14. Cancel another user's booking → rejected
    def test_14_cancel_other_users_booking(self):
        result = cancel_booking(self.booking_adjacent_id, self.user_b_id)
        self.assertFalse(result["success"])
        self.assertIn("own", result["error"].lower())

    # 15. Cancel already cancelled booking → rejected
    def test_15_cancel_already_cancelled(self):
        result = cancel_booking(self.booking_a_id, self.user_a_id)
        self.assertFalse(result["success"])
        self.assertIn("cancelled", result["error"].lower())


class TestAttendance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a fresh booking for attendance tests
        r = register_user("Alice Test", TEST_EMAIL_A, TEST_SID_A, "password123")
        cls.user_id = r.get("user_id") or _get_uid(TEST_EMAIL_A)

        result = get_available_seats(TOMORROW, "14:00", "15:00")
        seat_id = result["seats"][0].seat_id if result["success"] and result["seats"] else 1

        b = create_booking(cls.user_id, seat_id, TOMORROW, "14:00", "15:00")
        cls.booking_id = b.get("booking_id")

    # 16. Check in → present
    def test_16_check_in(self):
        result = check_in(self.booking_id)
        self.assertTrue(result["success"], result)
        record = get_attendance(self.booking_id)
        self.assertEqual(record["status"], "present")

    # 17. Check out → timestamp recorded
    def test_17_check_out(self):
        result = check_out(self.booking_id)
        self.assertTrue(result["success"], result)
        record = get_attendance(self.booking_id)
        self.assertIsNotNone(record["check_out_time"])

    # 18. No-show after grace period (simulated via a past booking)
    def test_18_no_show(self):
        # mark_no_show returns {"marked": False} for future bookings (grace not elapsed)
        # so we test directly by calling with a booking_id that can't have elapsed yet.
        result = mark_no_show(self.booking_id)
        # The booking is for TOMORROW so grace period hasn't passed – expect marked=False
        self.assertTrue(result["success"])
        self.assertFalse(result["marked"])


# ── Utilities used in test setUp ─────────────────────────────────────────────

def _get_uid(email):
    from services.user_service import get_user_by_email
    u = get_user_by_email(email)
    return u.user_id if u else None


def get_user_by_id_by_email(email):
    return _get_uid(email)


# ── Cleanup after all tests run ──────────────────────────────────────────────

def tearDownModule():
    _cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
