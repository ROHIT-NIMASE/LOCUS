"""
main.py - starts LOCUS. Run with:   python main.py

There is ONE window. Each screen is a frame; show_screen() destroys the current
frame and shows another one. That is all the "navigation" there is.
"""
import customtkinter as ctk
from theme import COLORS, APP_NAME
from ui.login import LoginScreen
from ui.register import RegisterScreen
from ui.dashboard import DashboardScreen
from ui.seats import SeatLayoutScreen
from ui.booking import BookingScreen
from ui.confirmation import ConfirmationScreen
from ui.bookings import MyBookingsScreen
from ui.checkin import CheckInScreen
from ui.checkout import CheckOutScreen


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Smart Library Seating")
        self.geometry("1000x740")
        self.minsize(900, 700)
        self.configure(fg_color=COLORS["bg"])

        # ---- Shared state: any screen can read/write these through `app` ----
        self.current_user = None     # set after login (dictionary from backend)
        self.selected_seat = None    # seat chosen on the seat layout screen
        self.selected_slot = None    # (date, start_time, end_time) chosen by the user

        # ---- Screen registry: name -> screen class. Add new screens here. ----
        self.screens = {
            "login": LoginScreen,
            "register": RegisterScreen,
            "dashboard": DashboardScreen,
            "seats": SeatLayoutScreen,
            "booking": BookingScreen,
            "confirmation": ConfirmationScreen,
            "bookings": MyBookingsScreen,
            "checkin": CheckInScreen,
            "checkout": CheckOutScreen,
        }
        self.current_frame = None
        self.show_screen("login")

    def show_screen(self, name, **kwargs):
        """Switch to another screen. Extra keyword arguments go to the screen."""
        if self.current_frame is not None:
            self.current_frame.destroy()
        self.current_frame = self.screens[name](self, self, **kwargs)
        self.current_frame.pack(fill="both", expand=True)

    def logout(self):
        self.current_user = None
        self.selected_seat = None
        self.selected_slot = None
        self.show_screen("login")


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    App().mainloop()
