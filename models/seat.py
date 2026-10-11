"""Simple Seat data structure for LOCUS."""


class Seat:
    """Represents a row in the ``seats`` table.

    ``status`` reflects the physical state of the seat:
        'available'  – the seat is usable.
        'maintenance'– the seat cannot be booked.

    Whether the seat is *occupied* at a particular moment is determined
    by querying active bookings, NOT by this status field.
    """

    def __init__(self, seat_id, seat_number, floor, status="available"):
        self.seat_id     = seat_id
        self.seat_number = seat_number
        self.floor       = floor
        self.status      = status       # 'available' | 'maintenance'

    def to_dict(self):
        return {
            "seat_id":     self.seat_id,
            "seat_number": self.seat_number,
            "floor":       self.floor,
            "status":      self.status,
        }

    def __repr__(self):
        return (
            f"Seat(seat_id={self.seat_id!r}, seat_number={self.seat_number!r}, "
            f"floor={self.floor!r}, status={self.status!r})"
        )
