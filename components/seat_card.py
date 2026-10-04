"""
components/seat_card.py - one seat on the layout screen.
A SeatCard is just a button whose colour depends on the seat's status.
"""
import customtkinter as ctk
from theme import SEAT_COLORS, font


class SeatCard(ctk.CTkButton):
    def __init__(self, parent, seat_id, status, on_click):
        """
        seat_id  : "A01"
        status   : "available" | "occupied" | "unavailable"  (comes from the backend)
        on_click : function(seat_id, status) called when the seat is clicked
        """
        super().__init__(parent, text=seat_id, width=90, height=70, corner_radius=10,
                         border_width=2, font=font(16, True),
                         command=lambda: on_click(self.seat_id, self.status))
        self.seat_id = seat_id
        self.status = status
        self.selected = False   # "selected" is a UI-only state, never sent to backend
        self._apply_colours()

    def set_selected(self, is_selected):
        # Only an available seat can look selected
        self.selected = is_selected and self.status == "available"
        self._apply_colours()

    def _apply_colours(self):
        state = "selected" if self.selected else self.status
        colours = SEAT_COLORS[state]
        self.configure(fg_color=colours["bg"], border_color=colours["border"],
                       text_color=colours["text"], hover_color=colours["hover"])
