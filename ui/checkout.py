"""ui/checkout.py - Screen 9: Check-out."""
import customtkinter as ctk
from services import backend
from theme import COLORS, font
from components.buttons import primary_button, secondary_button
from components.booking_card import BookingCard
from components.messages import MessageBanner, empty_state
from components.page_header import page_header


class CheckOutScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        self.booking = None
        page_header(self, app, "Check-out")

        area = ctk.CTkFrame(self, fg_color="transparent")
        area.pack(fill="both", expand=True)
        card = ctk.CTkFrame(area, fg_color=COLORS["card"], corner_radius=16,
                            border_width=1, border_color=COLORS["border"])
        card.place(relx=0.5, rely=0.46, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=32)

        ctk.CTkLabel(inner, text="Check out of your seat", font=font(22, True),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(inner, text="Check out when you are leaving so others can use the seat.",
                     font=font(13), text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 14))

        self.message = MessageBanner(inner, width=520, height=44)
        self.message.pack(pady=(0, 8))
        self.body = ctk.CTkFrame(inner, fg_color="transparent")   # redrawn when state changes
        self.body.pack(fill="x")

        self.show_active_booking()

    def clear_body(self):
        for child in self.body.winfo_children():
            child.destroy()

    def show_active_booking(self):
        self.clear_body()

        # BACKEND INTEGRATION POINT: backend.get_current_booking
        result = backend.get_current_booking(self.app.current_user["user_id"])
        if not result["success"]:
            self.message.show_error(result["message"])
            return
        self.booking = result["data"]

        # Only an Active (checked-in) booking can be checked out
        if self.booking is None or self.booking["status"] != "Active":
            if self.booking is None:
                title, text = "No active booking", "You have no booking to check out of."
            else:
                title, text = "You are not checked in", "Check in to your seat first."
            empty_state(self.body, title, text).pack(fill="x")
            if self.booking is None:
                primary_button(self.body, "Book a Seat", self.open_seat_layout, width=520).pack(pady=(14, 8))
            else:
                primary_button(self.body, "Go to Check-in",
                               lambda: self.app.show_screen("checkin"), width=520).pack(pady=(14, 8))
            secondary_button(self.body, "Back to Dashboard",
                             lambda: self.app.show_screen("dashboard"), width=520).pack()
            return

        BookingCard(self.body, self.booking).pack(fill="x")
        primary_button(self.body, "Check Out", self.handle_check_out, width=520).pack(pady=(14, 8))
        secondary_button(self.body, "Back to Dashboard",
                         lambda: self.app.show_screen("dashboard"), width=520).pack()

    def handle_check_out(self):
        # BACKEND INTEGRATION POINT: backend.check_out
        result = backend.check_out(self.booking["booking_id"])
        if not result["success"]:
            self.message.show_error(result["message"])
            return

        # Success: show the finished booking (status is now Completed)
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
