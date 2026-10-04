"""ui/seats.py - Screen 4: Seat Layout (choose date/time, then click a seat)."""
from datetime import datetime, timedelta
import customtkinter as ctk
from services import backend
from theme import COLORS, SEAT_COLORS, font
from components.buttons import primary_button, secondary_button
from components.messages import MessageBanner
from components.page_header import page_header
from components.seat_card import SeatCard

# Library opening hours and how far ahead students can book.
# (The real rules belong to the backend - these only control what the dropdowns offer.)
OPEN_HOUR = 8
CLOSE_HOUR = 22
DAYS_AHEAD = 7
TIME_OPTIONS = [f"{hour:02d}:00" for hour in range(OPEN_HOUR, CLOSE_HOUR + 1)]


def build_date_options():
    """Returns {label shown to the user: 'YYYY-MM-DD'} for today and the next days."""
    options = {}
    today = datetime.now().date()
    for offset in range(DAYS_AHEAD):
        day = today + timedelta(days=offset)
        if offset == 0:
            label = "Today, " + day.strftime("%d %b")
        elif offset == 1:
            label = "Tomorrow, " + day.strftime("%d %b")
        else:
            label = day.strftime("%a, %d %b")
        options[label] = day.isoformat()
    return options


def default_slot():
    """A sensible first choice: the next full hour (or tomorrow morning if the library is closing)."""
    now = datetime.now()
    start_hour = now.hour + 1
    day = now.date()
    if start_hour < OPEN_HOUR:
        start_hour = OPEN_HOUR
    elif start_hour >= CLOSE_HOUR:
        start_hour = OPEN_HOUR
        day = day + timedelta(days=1)
    return day.isoformat(), f"{start_hour:02d}:00", f"{start_hour + 1:02d}:00"


class SeatLayoutScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app
        self.date_options = build_date_options()   # label -> iso date
        self.seat_cards = {}                       # seat_id -> SeatCard (filled by render_seats)

        page_header(self, app, "Select a seat")
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=(18, 16))

        self.build_time_controls(content)
        self.message = MessageBanner(content, width=820, height=44)
        self.message.pack(anchor="w", pady=(10, 6))

        body = ctk.CTkFrame(content, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=290)
        self.build_seat_map_area(body)
        self.build_side_panel(body)

        self.load_seats()

    # ---------------- date / time pickers ----------------
    def build_time_controls(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.pack(fill="x")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(anchor="w", padx=22, pady=14)

        # Start from the slot chosen earlier (when coming back from the booking screen)
        day, start, end = self.app.selected_slot or default_slot()
        date_label = next((label for label, iso in self.date_options.items() if iso == day), None)
        if date_label is None:
            day, start, end = default_slot()
            date_label = next((label for label, iso in self.date_options.items() if iso == day),
                              list(self.date_options)[0])

        self.date_menu = self.make_menu(row, "Date", list(self.date_options), date_label)
        self.start_menu = self.make_menu(row, "Start time", TIME_OPTIONS[:-1], start)
        self.end_menu = self.make_menu(row, "End time", TIME_OPTIONS[1:], end)

    def make_menu(self, parent, label, values, initial):
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.pack(side="left", padx=(0, 22))
        ctk.CTkLabel(box, text=label, font=font(12, True),
                     text_color=COLORS["text_muted"]).pack(anchor="w")
        menu = ctk.CTkOptionMenu(box, values=values, command=self.on_slot_changed,
                                 width=170, height=38, font=font(14), dropdown_font=font(14),
                                 fg_color=COLORS["bg"], text_color=COLORS["text"],
                                 button_color=COLORS["primary_light"],
                                 button_hover_color="#C7D2FE",
                                 dropdown_fg_color="white", dropdown_text_color=COLORS["text"],
                                 dropdown_hover_color=COLORS["primary_light"])
        menu.set(initial)
        menu.pack()
        return menu

    def read_slot(self):
        """Returns (date, start_time, end_time) as currently chosen in the dropdowns."""
        return (self.date_options[self.date_menu.get()],
                self.start_menu.get(), self.end_menu.get())

    def on_slot_changed(self, _value=None):
        self.load_seats()

    # ---------------- seat map (left side) ----------------
    def build_seat_map_area(self, body):
        card = ctk.CTkFrame(body, fg_color=COLORS["card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        ctk.CTkLabel(card, text="Reading hall", font=font(15, True),
                     text_color=COLORS["text"]).pack(anchor="w", padx=22, pady=(16, 0))
        ctk.CTkLabel(card, text="Click an available seat to select it.", font=font(12),
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=22)
        self.grid_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.grid_frame.pack(expand=True, pady=14)

    def clear_seat_map(self):
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.seat_cards = {}

    def show_map_placeholder(self, text):
        self.clear_seat_map()
        ctk.CTkLabel(self.grid_frame, text=text, font=font(14),
                     text_color=COLORS["text_muted"]).pack(padx=40, pady=60)

    def render_seats(self, seats):
        """Draws one SeatCard per seat. The grid shape comes from the seat IDs
        (letter = row, number = column), so it adapts if the backend adds seats."""
        self.clear_seat_map()
        rows = sorted({seat["seat_id"][0] for seat in seats})
        for seat in seats:
            row = rows.index(seat["seat_id"][0])
            column = int(seat["seat_id"][1:]) - 1
            card = SeatCard(self.grid_frame, seat["seat_id"], seat["status"], self.on_seat_click)
            card.grid(row=row, column=column, padx=8, pady=8)
            self.seat_cards[seat["seat_id"]] = card

    # ---------------- legend + selection (right side) ----------------
    def build_side_panel(self, body):
        side = ctk.CTkFrame(body, fg_color="transparent")
        side.grid(row=0, column=1, sticky="new")

        # Legend
        legend = ctk.CTkFrame(side, fg_color=COLORS["card"], corner_radius=12,
                              border_width=1, border_color=COLORS["border"])
        legend.pack(fill="x")
        ctk.CTkLabel(legend, text="Legend", font=font(15, True),
                     text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(14, 6))
        for state, text in [("available", "Available"), ("occupied", "Occupied"),
                            ("selected", "Selected"), ("unavailable", "Temporarily unavailable")]:
            row = ctk.CTkFrame(legend, fg_color="transparent")
            row.pack(anchor="w", padx=20, pady=3)
            ctk.CTkFrame(row, width=22, height=22, corner_radius=6, border_width=2,
                         fg_color=SEAT_COLORS[state]["bg"],
                         border_color=SEAT_COLORS[state]["border"]).pack(side="left")
            ctk.CTkLabel(row, text=text, font=font(13),
                         text_color=COLORS["text"]).pack(side="left", padx=10)
        ctk.CTkLabel(legend, text="", height=4).pack()   # bottom spacing

        # Selection summary + Continue button
        selection = ctk.CTkFrame(side, fg_color=COLORS["card"], corner_radius=12,
                                 border_width=1, border_color=COLORS["border"])
        selection.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(selection, text="Your selection", font=font(15, True),
                     text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(14, 0))
        self.seat_label = ctk.CTkLabel(selection, text="—", font=font(34, True),
                                       text_color=COLORS["text_muted"])
        self.seat_label.pack(pady=(4, 0))
        self.seat_hint = ctk.CTkLabel(selection, text="", font=font(12), wraplength=240,
                                      text_color=COLORS["text_muted"])
        self.seat_hint.pack(pady=(0, 10))
        self.continue_button = primary_button(selection, "Continue to Booking",
                                              self.go_to_booking, width=240)
        self.continue_button.pack(padx=20)
        secondary_button(selection, "Back to Dashboard",
                         lambda: self.back_to_dashboard(), width=240).pack(padx=20, pady=(8, 16))

    def update_selection_panel(self):
        seat_id = self.app.selected_seat
        if seat_id:
            day, start, end = self.read_slot()
            self.seat_label.configure(text=seat_id, text_color=COLORS["primary"])
            self.seat_hint.configure(text=f"{self.date_menu.get()}\n{start} – {end}")
            self.continue_button.configure(state="normal", fg_color=COLORS["primary"],
                                           hover_color=COLORS["primary_hover"])
        else:
            self.seat_label.configure(text="—", text_color=COLORS["text_muted"])
            self.seat_hint.configure(text="No seat selected yet.")
            self.continue_button.configure(state="disabled", fg_color="#9CA3AF",
                                           hover_color="#9CA3AF")

    # ---------------- logic ----------------
    def check_slot(self, day, start, end):
        """Basic checks on the chosen time. Returns an error text, or None if fine."""
        if end <= start:
            return "End time must be after start time."
        now = datetime.now()
        if day == now.date().isoformat() and int(start[:2]) < now.hour:
            return "That start time has already passed. Please choose a later time."
        return None

    def load_seats(self):
        """Asks the backend for the seat statuses of the chosen date/time and redraws the map."""
        day, start, end = self.read_slot()

        error = self.check_slot(day, start, end)
        if error:
            self.message.show_error(error)
            self.show_map_placeholder("Choose a valid date and time to see seats.")
            self.app.selected_seat = None
            self.update_selection_panel()
            return

        # BACKEND INTEGRATION POINT: backend.get_seat_statuses
        result = backend.get_seat_statuses(day, start, end)
        if not result["success"]:
            self.message.show_error(result["message"])
            self.show_map_placeholder("Could not load the seat layout.")
            self.app.selected_seat = None
            self.update_selection_panel()
            return

        seats = result["data"]
        status_by_id = {seat["seat_id"]: seat["status"] for seat in seats}
        previous_choice = self.app.selected_seat
        self.render_seats(seats)
        self.message.clear()

        # Keep the earlier choice only if that seat is still free for the new time
        if previous_choice and status_by_id.get(previous_choice) == "available":
            self.seat_cards[previous_choice].set_selected(True)
        elif previous_choice:
            self.app.selected_seat = None
            self.message.show_info(f"Seat {previous_choice} is not available for this time. "
                                   "Please choose another seat.")

        if "available" not in status_by_id.values():
            self.message.show_error("No seats are available for this time. "
                                    "Try another date or time.")
        self.update_selection_panel()

    def on_seat_click(self, seat_id, status):
        if status == "occupied":
            self.message.show_error(f"Seat {seat_id} is already booked for this time.")
            return
        if status == "unavailable":
            self.message.show_error(f"Seat {seat_id} is temporarily unavailable.")
            return

        self.message.clear()
        previous = self.app.selected_seat
        if previous in self.seat_cards:
            self.seat_cards[previous].set_selected(False)   # un-highlight the old seat
        self.app.selected_seat = seat_id
        self.seat_cards[seat_id].set_selected(True)
        self.update_selection_panel()

    def go_to_booking(self):
        if not self.app.selected_seat:
            self.message.show_error("Please select a seat first.")
            return
        self.app.selected_slot = self.read_slot()   # (date, start, end) for the next screen
        self.app.show_screen("booking")

    def back_to_dashboard(self):
        self.app.selected_seat = None
        self.app.selected_slot = None
        self.app.show_screen("dashboard")
