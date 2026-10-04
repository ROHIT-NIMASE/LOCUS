"""ui/dashboard.py - Screen 3: Student Dashboard (the home screen after login)."""
from datetime import datetime, timedelta
import customtkinter as ctk
from services import backend
from theme import COLORS, APP_NAME, font
from components.buttons import primary_button, secondary_button, link_button
from components.booking_card import BookingCard
from components.messages import empty_state


def next_hour_slot():
    """Returns (date, start, end) for 'right now until one hour later'.
    Used to show how many seats are free at this moment."""
    now = datetime.now()
    later = now + timedelta(hours=1)
    end_text = "23:59" if later.date() != now.date() else later.strftime("%H:%M")
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), end_text


class DashboardScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        self.user = app.current_user   # set by the login screen

        self.build_header()
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=26)
        self.build_welcome(content)
        self.build_overview(content)
        self.build_quick_actions(content)

    # ---------- top bar: logo, user name, logout ----------
    def build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text=APP_NAME, font=font(24, True),
                     text_color=COLORS["primary"]).pack(side="left", padx=40)
        link_button(header, "Logout", self.app.logout).pack(side="right", padx=(8, 40))
        ctk.CTkLabel(header, text=f"{self.user['full_name']}  ·  {self.user['student_id']}",
                     font=font(13), text_color=COLORS["text_muted"]).pack(side="right")
        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1, corner_radius=0).pack(fill="x")

    # ---------- welcome message ----------
    def build_welcome(self, parent):
        first_name = self.user["full_name"].split()[0]
        ctk.CTkLabel(parent, text=f"Welcome back, {first_name}", font=font(28, True),
                     text_color=COLORS["text"]).pack(anchor="w")
        ctk.CTkLabel(parent, text="Here is your library seating overview.", font=font(14),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(2, 0))

    # ---------- current booking (left) + available seats (right) ----------
    def build_overview(self, parent):
        overview = ctk.CTkFrame(parent, fg_color="transparent")
        overview.pack(fill="x", pady=(24, 0))
        overview.grid_columnconfigure(0, weight=3, uniform="overview")
        overview.grid_columnconfigure(1, weight=1, uniform="overview")

        # Left: current booking
        left = ctk.CTkFrame(overview, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        ctk.CTkLabel(left, text="Your current booking", font=font(15, True),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 8))

        # BACKEND INTEGRATION POINT: backend.get_current_booking
        result = backend.get_current_booking(self.user["user_id"])
        if not result["success"]:
            empty_state(left, "Could not load your booking", result["message"]).pack(fill="x")
        elif result["data"] is None:
            empty_state(left, "No current booking",
                        "You have no upcoming or active booking. Book a seat to get started.").pack(fill="x")
        else:
            BookingCard(left, result["data"]).pack(fill="x")

        # Right: available seats right now
        right = ctk.CTkFrame(overview, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right, text="Seat availability", font=font(15, True),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(0, 8))
        self.build_seat_count_card(right)

    def build_seat_count_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.pack(fill="x")

        day, start, end = next_hour_slot()
        # BACKEND INTEGRATION POINT: backend.get_available_seat_count
        result = backend.get_available_seat_count(day, start, end)

        if not result["success"]:
            ctk.CTkLabel(card, text="Could not load availability.", font=font(13),
                         text_color=COLORS["error"]).pack(padx=22, pady=30)
            return

        count = result["data"]
        number_colour = COLORS["primary"] if count > 0 else COLORS["error"]
        ctk.CTkLabel(card, text=str(count), font=font(44, True),
                     text_color=number_colour).pack(pady=(16, 0))
        ctk.CTkLabel(card, text="seats available now", font=font(14, True),
                     text_color=COLORS["text"]).pack()
        ctk.CTkLabel(card, text=f"Next hour: {start} – {end}", font=font(12),
                     text_color=COLORS["text_muted"]).pack(pady=(2, 16 if count > 0 else 0))
        if count == 0:
            # "No available seats" state
            ctk.CTkLabel(card, text="No seats are free right now.\nPlease check again later.",
                         font=font(12), text_color=COLORS["error"]).pack(pady=(6, 16))

    # ---------- quick action buttons ----------
    def build_quick_actions(self, parent):
        ctk.CTkLabel(parent, text="Quick actions", font=font(15, True),
                     text_color=COLORS["text"]).pack(anchor="w", pady=(28, 8))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x")

        actions = [
            ("Book a Seat", self.open_seat_layout),
            ("My Bookings", lambda: self.app.show_screen("bookings")),
            ("Check-in", lambda: self.app.show_screen("checkin")),
            ("Check-out", lambda: self.app.show_screen("checkout")),
        ]
        for column, (text, command) in enumerate(actions):
            row.grid_columnconfigure(column, weight=1, uniform="actions")
            make_button = primary_button if column == 0 else secondary_button
            is_last = column == len(actions) - 1
            make_button(row, text, command, width=100, height=56).grid(
                row=0, column=column, sticky="ew",
                padx=(0 if column == 0 else 6, 0 if is_last else 6))

    def open_seat_layout(self):
        self.app.selected_seat = None   # start a fresh booking
        self.app.selected_slot = None
        self.app.show_screen("seats")
