"""Simple Booking data structure for LOCUS."""

# Valid booking statuses – mirrors the ENUM in database.sql
VALID_STATUSES = frozenset({
    "confirmed",
    "cancelled",
    "completed",
    "expired",
    "no_show",
})


class Booking:
    """Represents a row in the ``bookings`` table.

    No database queries live here – this is a plain data container.
    """

    def __init__(
        self,
        booking_id,
        user_id,
        seat_id,
        booking_date,
        start_time,
        end_time,
        status="confirmed",
        created_at=None,
    ):
        self.booking_id   = booking_id
        self.user_id      = user_id
        self.seat_id      = seat_id
        self.booking_date = booking_date
        self.start_time   = start_time
        self.end_time     = end_time
        self.status       = status
        self.created_at   = created_at

    def to_dict(self):
        return {
            "booking_id":   self.booking_id,
            "user_id":      self.user_id,
            "seat_id":      self.seat_id,
            "booking_date": str(self.booking_date) if self.booking_date else None,
            "start_time":   str(self.start_time)   if self.start_time   else None,
            "end_time":     str(self.end_time)      if self.end_time     else None,
            "status":       self.status,
            "created_at":   str(self.created_at)   if self.created_at   else None,
        }

    def __repr__(self):
        return (
            f"Booking(booking_id={self.booking_id!r}, user_id={self.user_id!r}, "
            f"seat_id={self.seat_id!r}, date={self.booking_date!r}, "
            f"start={self.start_time!r}, end={self.end_time!r}, "
            f"status={self.status!r})"
        )
