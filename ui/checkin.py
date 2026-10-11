"""ui/checkin.py - Screen 8: Check-in."""
import customtkinter as ctk
from services import backend
from theme import COLORS, font
from components.buttons import primary_button, secondary_button
from components.booking_card import BookingCard
from components.messages import MessageBanner, empty_state
from components.page_header import page_header


class CheckInScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        self.booking = None
        page_header(self, app, "Check-in")

        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(fill="both", expand=True)
        card = ctk.CTkFrame(area, fg_color=COLORS["card"], corner_radius=16,
                            border_width=1, border_color=COLORS["border"])
        card.place(relx=0.5, rely=0.46, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=32)

        ctk.CTkLabel(inner, text="Check in to your seat", font=font(22, True),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(inner, text="Check in once you have arrived at your seat.", font=font(13),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 14))

        self.message = MessageBanner(inner, width=520, height=44)
        self.message.pack(pady=(0, 8))
        self.body = ctk.CTkFrame(inner, fg_color="transparent")   # redrawn when state changes
        self.body.pack(fill="x")

        self.show_current_booking()

    def clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def show_current_booking(self):
        self.clear_body()

        # BACKEND INTEGRATION POINT: backend.get_current_booking
        result = backend.get_current_booking(self.app.current_user["user_id"])
        if not result["success"]:
            self.message.show_error(result["message"])
            return
        self.booking = result["data"]

        if self.booking is None:
            empty_state(self.body, "No booking to check in",
                        "You do not have an upcoming booking.").pack(fill="x")
            primary_button(self.body, "Book a Seat", self.open_seat_layout, width=520).pack(pady=(14, 8))
            secondary_button(self.body, "Back to Dashboard",
                             lambda: self.app.show_screen("dashboard"), width=520).pack()
            return

        BookingCard(self.body, self.booking).pack(fill="x")
        check_in_button = primary_button(self.body, "Check In", self.handle_check_in, width=520)
        check_in_button.pack(pady=(14, 8))
        if self.booking["status"] == "Active":
            # Already checked in: nothing more to do here
            self.message.show_info("You are already checked in to this booking.")
            check_in_button.configure(state="disabled", fg_color="#9CA3AF")
        secondary_button(self.body, "Back to Dashboard",
                         lambda: self.app.show_screen("dashboard"), width=520).pack()

    def handle_check_in(self):
        # BACKEND INTEGRATION POINT: backend.check_in
        result = backend.check_in(self.booking["booking_id"])
        if not result["success"]:
            self.message.show_error(result["message"])
            return

        # Success: show the updated booking (status is now Active)
        self.clear_body()
        BookingCard(self.body, result["data"]).pack(fill="x")
        primary_button(self.body, "Back to Dashboard",
                       lambda: self.app.show_screen("dashboard"), width=520).pack(pady=(14, 8))
        secondary_button(self.body, "View My Bookings",
                         lambda: self.app.show_screen("bookings"), width=520).pack()
        self.message.show_success(result["message"])

    def open_seat_layout(self):
        self.app.selected_seat = None
        self.app.selected_slot = None
        self.app.show_screen("seats")
