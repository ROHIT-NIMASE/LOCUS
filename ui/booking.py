"""ui/booking.py - Screen 5: Booking (review the summary, then confirm)."""
import customtkinter as ctk
from services import backend
from theme import COLORS, font
from components.buttons import primary_button, secondary_button, link_button
from components.booking_card import format_date
from components.messages import MessageBanner, empty_state
from components.page_header import page_header


def duration_text(start, end):
    """'10:00', '12:30' -> '2 hours 30 min'"""
    minutes = (int(end[:2]) * 60 + int(end[3:])) - (int(start[:2]) * 60 + int(start[3:]))
    hours, extra = divmod(minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours} hour" + ("s" if hours != 1 else ""))
    if extra:
        parts.append(f"{extra} min")
    return " ".join(parts)


class BookingScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        page_header(self, app, "Confirm booking")

        # Safety: this screen needs a seat and a time slot from the seat layout screen
        if not app.selected_seat or not app.selected_slot:
            empty_state(self, "No seat selected", "Please choose a seat first.").pack(pady=(80, 16))
            primary_button(self, "Choose a Seat", lambda: app.show_screen("seats"),
                           width=200).pack()
            return

        self.seat_id = app.selected_seat
        self.day, self.start, self.end = app.selected_slot

        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(fill="both", expand=True)
        card = ctk.CTkFrame(area, fg_color=COLORS["card"], corner_radius=16,
                            border_width=1, border_color=COLORS["border"])
        card.place(relx=0.5, rely=0.46, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=32)

        ctk.CTkLabel(inner, text="Booking summary", font=font(22, True),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(inner, text="Please check the details before confirming.", font=font(13),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 14))

        # Summary box: one row per detail
        summary = ctk.CTkFrame(inner, fg_color=COLORS["bg"], corner_radius=10, width=420)
        summary.pack(fill="x")
        rows = [
            ("Student", app.current_user["full_name"]),
            ("Seat", self.seat_id),
            ("Date", format_date(self.day)),
            ("Start time", self.start),
            ("End time", self.end),
            ("Duration", duration_text(self.start, self.end)),
        ]
        for label, value in rows:
            row = ctk.CTkFrame(summary, fg_color="transparent")
            row.pack(fill="x", padx=18, pady=5)
            ctk.CTkLabel(row, text=label, font=font(13), width=110, anchor="w",
                         text_color=COLORS["text_muted"]).pack(side="left")
            ctk.CTkLabel(row, text=value, font=font(14, True),
                         text_color=COLORS["text"]).pack(side="left")
        ctk.CTkLabel(summary, text="", height=4).pack()   # bottom spacing

        self.message = MessageBanner(inner, width=420)
        self.message.pack(pady=(12, 10))

        primary_button(inner, "Confirm Booking", self.confirm_booking, width=420).pack()
        secondary_button(inner, "Back to Seat Selection",
                         lambda: app.show_screen("seats"), width=420).pack(pady=(8, 4))
        link_button(inner, "Cancel", self.cancel).pack()

    def confirm_booking(self):
        # BACKEND INTEGRATION POINT: backend.create_booking
        result = backend.create_booking(self.app.current_user["user_id"], self.seat_id,
                                        self.day, self.start, self.end)
        if result["success"]:
            self.app.selected_seat = None
            self.app.selected_slot = None
            self.app.show_screen("confirmation", booking=result["data"])
        else:
            # "Booking failed" state - the seat may have been taken a moment ago
            self.message.show_error("Booking failed. " + result["message"])

    def cancel(self):
        self.app.selected_seat = None
        self.app.selected_slot = None
        self.app.show_screen("dashboard")
