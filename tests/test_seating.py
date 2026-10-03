
"""Unit tests for LOCUS validation and booking logic."""

import unittest
from datetime import datetime, timedelta

from logic.validation import (
    validate_positive_id,
    validate_booking_times,
)
from logic.booking_logic import (
    bookings_overlap,
    is_seat_available,
)


class TestValidation(unittest.TestCase):

    def test_positive_id(self):
        self.assertTrue(validate_positive_id(5, "Seat ID"))

    def test_reject_zero_id(self):
        with self.assertRaises(ValueError):
            validate_positive_id(0)

    def test_reject_negative_id(self):
        with self.assertRaises(ValueError):
            validate_positive_id(-1)

    def test_reject_boolean_id(self):
        with self.assertRaises(ValueError):
            validate_positive_id(True)

    def test_reject_string_id(self):
        with self.assertRaises(ValueError):
            validate_positive_id("5")

    def test_valid_future_booking(self):
        now = datetime(2026, 10, 3, 10, 0)
        start = now + timedelta(hours=1)
        end = start + timedelta(hours=2)

        self.assertTrue(validate_booking_times(start, end, now=now))

    def test_reject_booking_in_the_past(self):
        now = datetime(2026, 10, 3, 10, 0)
        start = now - timedelta(minutes=1)
        end = now + timedelta(hours=1)

        with self.assertRaises(ValueError):
            validate_booking_times(start, end, now=now)

    def test_reject_end_before_start(self):
        now = datetime(2026, 10, 3, 10, 0)
        start = now + timedelta(hours=2)
        end = start - timedelta(hours=1)

        with self.assertRaises(ValueError):
            validate_booking_times(start, end, now=now)



class TestBookingOverlap(unittest.TestCase):

    def setUp(self):
        self.day = datetime(2026, 10, 5)

    def test_overlapping_periods(self):
        self.assertTrue(
            bookings_overlap(
                self.day.replace(hour=10),
                self.day.replace(hour=12),
                self.day.replace(hour=11),
                self.day.replace(hour=13),
            )
        )

    def test_non_overlapping_periods(self):
        self.assertFalse(
            bookings_overlap(
                self.day.replace(hour=10),
                self.day.replace(hour=11),
                self.day.replace(hour=11),
                self.day.replace(hour=12),
            )
        )

    def test_one_period_inside_another(self):
        self.assertTrue(
            bookings_overlap(
                self.day.replace(hour=9),
                self.day.replace(hour=15),
                self.day.replace(hour=10),
                self.day.replace(hour=11),
            )
        )

    def test_identical_periods(self):
        self.assertTrue(
            bookings_overlap(
                self.day.replace(hour=10),
                self.day.replace(hour=11),
                self.day.replace(hour=10),
                self.day.replace(hour=11),
            )
        )

    def test_invalid_period(self):
        with self.assertRaises(ValueError):
            bookings_overlap(
                self.day.replace(hour=12),
                self.day.replace(hour=10),
                self.day.replace(hour=11),
                self.day.replace(hour=13),
            )



class TestSeatAvailability(unittest.TestCase):

    def setUp(self):
        self.bookings = [
            {
                "seat_id": 5,
                "start_time": datetime(2026, 10, 5, 10, 0),
                "end_time": datetime(2026, 10, 5, 11, 0),
                "status": "BOOKED",
            }
        ]

    def test_conflicting_booking_is_unavailable(self):
        result = is_seat_available(
            5,
            datetime(2026, 10, 5, 10, 30),
            datetime(2026, 10, 5, 11, 30),
            self.bookings,
        )
        self.assertFalse(result)

    def test_adjacent_booking_is_available(self):
        result = is_seat_available(
            5,
            datetime(2026, 10, 5, 11, 0),
            datetime(2026, 10, 5, 12, 0),
            self.bookings,
        )
        self.assertTrue(result)

    def test_different_seat_is_available(self):
        result = is_seat_available(
            6,
            datetime(2026, 10, 5, 10, 30),
            datetime(2026, 10, 5, 11, 30),
            self.bookings,
        )
        self.assertTrue(result)

    def test_cancelled_booking_does_not_block(self):
        cancelled = [dict(self.bookings[0], status="CANCELLED")]

        result = is_seat_available(
            5,
            datetime(2026, 10, 5, 10, 30),
            datetime(2026, 10, 5, 11, 30),
            cancelled,
        )
        self.assertTrue(result)

    def test_no_show_booking_does_not_block(self):
        no_show = [dict(self.bookings[0], status="NO_SHOW")]

        result = is_seat_available(
            5,
            datetime(2026, 10, 5, 10, 30),
            datetime(2026, 10, 5, 11, 30),
            no_show,
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
