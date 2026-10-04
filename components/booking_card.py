"""
components/booking_card.py - shows ONE booking's details as a card.
Reused on the Dashboard, Confirmation, Check-in and Check-out screens, so a
booking always looks the same everywhere.
"""
from datetime import datetime
import customtkinter as ctk
from theme import COLORS, STATUS_COLORS, font


def format_date(iso_date):
    """'2026-10-04' -> '04 Oct 2026'. Falls back to the original text if it can't convert."""
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return iso_date


def status_badge(parent, status):
    """Small coloured label such as 'Upcoming' or 'Active'. Pack it yourself."""
    colours = STATUS_COLORS.get(status, STATUS_COLORS["Completed"])
    return ctk.CTkLabel(parent, text=status, width=90, height=26, corner_radius=13,
                        font=font(12, True), fg_color=colours["bg"],
                        text_color=colours["text"])


class BookingCard(ctk.CTkFrame):
    def __init__(self, parent, booking):
        # booking = a booking dictionary from the backend (see services/backend.py)
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=12,
                         border_width=1, border_color=COLORS["border"])

        # Top row: booking ID on the left, status badge on the right
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(18, 10))
        ctk.CTkLabel(header, text=f"Booking {booking['booking_id']}", font=font(15, True),
                     text_color=COLORS["text"]).pack(side="left")
        status_badge(header, booking["status"]).pack(side="right")

        # Details row: Seat | Date | Time
        details = ctk.CTkFrame(self, fg_color="transparent")
        details.pack(fill="x", padx=22, pady=(0, 18))
        items = [
            ("Seat", booking["seat_id"]),
            ("Date", format_date(booking["date"])),
            ("Time", f"{booking['start_time']} – {booking['end_time']}"),
        ]
        for column, (label, value) in enumerate(items):
            box = ctk.CTkFrame(details, fg_color="transparent")
            box.grid(row=0, column=column, sticky="w", padx=(0, 36))
            ctk.CTkLabel(box, text=label, font=font(12), text_color=COLORS["text_muted"]).pack(anchor="w")
            ctk.CTkLabel(box, text=value, font=font(18, True), text_color=COLORS["text"]).pack(anchor="w")
