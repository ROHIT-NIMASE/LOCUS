"""ui/confirmation.py - Screen 6: Booking Confirmation."""
import customtkinter as ctk
from theme import COLORS, font
from components.buttons import primary_button, secondary_button
from components.booking_card import BookingCard
from components.messages import empty_state
from components.page_header import page_header


class ConfirmationScreen(ctk.CTkFrame):
    def __init__(self, parent, app, booking=None):
        # booking = the booking dictionary returned by backend.create_booking
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        page_header(self, app, "Booking confirmed")

        if booking is None:
            empty_state(self, "Nothing to show", "No booking details were provided.").pack(pady=(80, 16))
            primary_button(self, "Back to Dashboard", lambda: app.show_screen("dashboard"),
                           width=200).pack()
            return

        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(fill="both", expand=True)
        centre = ctk.CTkFrame(area, fg_color="transparent")
        centre.place(relx=0.5, rely=0.46, anchor="center")

        # Green tick circle
        circle = ctk.CTkFrame(centre, width=72, height=72, corner_radius=36,
                              fg_color=COLORS["success_bg"])
        circle.pack()
        circle.pack_propagate(False)   # keep it a perfect circle
        ctk.CTkLabel(circle, text="✓", font=font(34, True),
                     text_color=COLORS["success"]).pack(expand=True)
        ctk.CTkLabel(centre, text="Booking successful!", font=font(26, True),
                     text_color=COLORS["text"]).pack(pady=(14, 2))
        ctk.CTkLabel(centre, text="Your seat has been reserved. Remember to check in when you arrive.",
                     font=font(13), text_color=COLORS["text_muted"]).pack(pady=(0, 18))

        BookingCard(centre, booking).pack(fill="x")

        primary_button(centre, "View My Bookings", lambda: app.show_screen("bookings"),
                       width=520).pack(pady=(20, 8))
        secondary_button(centre, "Back to Dashboard", lambda: app.show_screen("dashboard"),
                         width=520).pack()
