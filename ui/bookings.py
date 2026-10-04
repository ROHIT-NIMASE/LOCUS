"""ui/bookings.py - Screen 7: My Bookings (table of the student's bookings)."""
from tkinter import messagebox
import customtkinter as ctk
from services import backend
from theme import COLORS, font
from components.buttons import primary_button, secondary_button, danger_button
from components.booking_card import format_date, status_badge
from components.messages import MessageBanner, empty_state
from components.page_header import page_header

# (column title, minimum width in pixels). Header and rows share these so they line up.
COLUMNS = [("Booking ID", 110), ("Seat", 70), ("Date", 130), ("Time", 150), ("Status", 110), ("", 150)]


class MyBookingsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        page_header(self, app, "My bookings")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=(18, 16))

        # Title + number of bookings
        top = ctk.CTkFrame(content, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text="My bookings", font=font(24, True),
                     text_color=COLORS["text"]).pack(side="left")
        self.count_label = ctk.CTkLabel(top, text="", font=font(13), text_color=COLORS["text_muted"])
        self.count_label.pack(side="left", padx=14, pady=(6, 0))

        self.message = MessageBanner(content, width=820, height=44)
        self.message.pack(anchor="w", pady=(8, 6))

        self.table_header = self.build_table_header(content)
        self.scroll = ctk.CTkScrollableFrame(content, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        secondary_button(content, "Back to Dashboard", lambda: app.show_screen("dashboard"),
                         width=200).pack(anchor="w", pady=(10, 0))

        self.refresh()

    # ---------------- table ----------------
    def build_table_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color="transparent", height=24)
        header.pack(fill="x")
        header.pack_propagate(False)   # fixed height, so hiding the labels keeps the layout steady
        self.header_labels = ctk.CTkFrame(header, fg_color="transparent")
        for column, (title, width) in enumerate(COLUMNS):
            self.header_labels.grid_columnconfigure(column, minsize=width)
            ctk.CTkLabel(self.header_labels, text=title, font=font(12, True),
                         text_color=COLORS["text_muted"]).grid(row=0, column=column, sticky="w")
        return header

    def refresh(self):
        """Loads the bookings from the backend and redraws the list."""
        for child in self.scroll.winfo_children():
            child.destroy()
        self.header_labels.pack_forget()   # hide column titles until we know there are bookings

        # BACKEND INTEGRATION POINT: backend.get_user_bookings
        result = backend.get_user_bookings(self.app.current_user["user_id"])

        if not result["success"]:
            self.count_label.configure(text="")
            empty_state(self.scroll, "Could not load your bookings", result["message"]).pack(pady=40)
            return

        bookings = result["data"]
        if not bookings:
            # "No bookings" state
            self.count_label.configure(text="")
            empty_state(self.scroll, "No bookings yet",
                        "When you book a seat, it will appear here.").pack(pady=(40, 14))
            primary_button(self.scroll, "Book a Seat", self.open_seat_layout, width=200).pack()
            return

        self.count_label.configure(text=f"{len(bookings)} booking" + ("s" if len(bookings) != 1 else ""))
        self.header_labels.pack(fill="x", padx=(26, 20))
        for booking in bookings:
            self.add_row(booking)

    def add_row(self, booking):
        row = ctk.CTkFrame(self.scroll, fg_color=COLORS["card"], corner_radius=10,
                           border_width=1, border_color=COLORS["border"])
        row.pack(fill="x", pady=4)
        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=12)
        for column, (_, width) in enumerate(COLUMNS):
            inner.grid_columnconfigure(column, minsize=width)
        inner.grid_columnconfigure(5, weight=1)

        values = [booking["booking_id"], booking["seat_id"], format_date(booking["date"]),
                  f"{booking['start_time']} – {booking['end_time']}"]
        for column, text in enumerate(values):
            ctk.CTkLabel(inner, text=text, font=font(14, column == 0),
                         text_color=COLORS["text"]).grid(row=0, column=column, sticky="w")
        status_badge(inner, booking["status"]).grid(row=0, column=4, sticky="w")

        # Cancel button only where it makes sense: upcoming bookings
        if booking["status"] == "Upcoming":
            danger_button(inner, "Cancel Booking",
                          lambda b=booking: self.cancel(b), width=140, height=32).grid(
                row=0, column=5, sticky="e")

    # ---------------- actions ----------------
    def cancel(self, booking):
        sure = messagebox.askyesno(
            "Cancel booking",
            f"Cancel booking {booking['booking_id']}?\n\nSeat {booking['seat_id']} on "
            f"{format_date(booking['date'])}, {booking['start_time']} – {booking['end_time']}")
        if not sure:
            return

        # BACKEND INTEGRATION POINT: backend.cancel_booking
        result = backend.cancel_booking(booking["booking_id"])
        self.refresh()   # redraw first, then show the message
        if result["success"]:
            self.message.show_success(f"Booking {booking['booking_id']} has been cancelled.")
        else:
            self.message.show_error(result["message"])

    def open_seat_layout(self):
        self.app.selected_seat = None
        self.app.selected_slot = None
        self.app.show_screen("seats")
