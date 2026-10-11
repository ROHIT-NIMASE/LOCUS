"""
components/messages.py - success / error / info messages and empty states.
"""
import customtkinter as ctk
from theme import COLORS, font

# kind -> (background colour, text colour)
_STYLES = {
    "success": (COLORS["success_bg"], COLORS["success"]),
    "error": (COLORS["error_bg"], COLORS["error"]),
    "info": (COLORS["info_bg"], COLORS["info"]),
}


class MessageBanner(ctk.CTkFrame):
    """A coloured message box. It keeps a fixed height even when empty, so the
    layout does not jump when a message appears.

    Usage:
        self.message = MessageBanner(parent)
        self.message.pack()
        self.message.show_error("Invalid login")
        self.message.clear()
    """

    def __init__(self, parent, width=360, height=50):
        super().__init__(parent, width=width, height=height, corner_radius=8,
                         fg_color="transparent")
        self.pack_propagate(False)  # keep the fixed size
        self.label = ctk.CTkLabel(self, text="", font=font(13), anchor="w",
                                  justify="left", wraplength=width - 30)
        self.label.pack(fill="both", expand=True, padx=12)

    def _show(self, kind, text):
        background, text_colour = _STYLES[kind]
        self.configure(fg_color=background)
        self.label.configure(text=text, text_color=text_colour)

    def show_success(self, text):
        self._show("success", text)

    def show_error(self, text):
        self._show("error", text)

    def show_info(self, text):
        self._show("info", text)

    def clear(self):
        self.configure(fg_color="transparent")
        self.label.configure(text="")


def empty_state(parent, title, message):
    """A friendly 'nothing here' box (e.g. 'No bookings yet'). Pack it yourself."""
    box = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12,
                       border_width=1, border_color=COLORS["border"])
    ctk.CTkLabel(box, text=title, font=font(18, True),
                 text_color=COLORS["text"]).pack(padx=40, pady=(28, 4))
    ctk.CTkLabel(box, text=message, font=font(13),
                 text_color=COLORS["text_muted"]).pack(padx=40, pady=(0, 28))
    return box
