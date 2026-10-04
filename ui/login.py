"""ui/login.py - Screen 1: Login."""
import customtkinter as ctk
from services import backend
from theme import COLORS, APP_NAME, TAGLINE, font
from components.buttons import primary_button, secondary_button
from components.inputs import labeled_entry
from components.messages import MessageBanner


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, app, notice=None):
        # app    = the main window (used to switch screens and store the logged-in user)
        # notice = optional success text, e.g. shown after registering
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        # White card in the middle of the window
        card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=16,
                            border_width=1, border_color=COLORS["border"])
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=36)

        # Logo / name
        ctk.CTkLabel(inner, text=APP_NAME, font=font(38, True),
                     text_color=COLORS["primary"]).pack()
        ctk.CTkLabel(inner, text=TAGLINE, font=font(14),
                     text_color=COLORS["text_muted"]).pack(pady=(0, 18))
        ctk.CTkLabel(inner, text="Sign in to your account", font=font(18, True),
                     text_color=COLORS["text"]).pack(anchor="w")

        # Input fields
        self.identifier_entry = labeled_entry(inner, "Email or username", "student@college.edu")
        self.password_entry = labeled_entry(inner, "Password", "Enter your password", show="•")
        self.password_entry.bind("<Return>", lambda event: self.handle_login())  # Enter key logs in

        # Message area (errors / success)
        self.message = MessageBanner(inner)
        self.message.pack(pady=(14, 8))
        if notice:
            self.message.show_success(notice)

        # Buttons
        primary_button(inner, "Login", self.handle_login).pack(pady=(0, 10))
        secondary_button(inner, "Create Account",
                         lambda: self.app.show_screen("register")).pack()

        # TEMPORARY: demo credentials hint. Delete this label once the real backend is connected.
        ctk.CTkLabel(inner, text="Demo login:  student  /  locus123", font=font(12),
                     text_color=COLORS["text_muted"]).pack(pady=(16, 0))

    def handle_login(self):
        identifier = self.identifier_entry.get().strip()
        password = self.password_entry.get()

        # 1. Frontend validation: empty fields
        if not identifier or not password:
            self.message.show_error("Please enter both your email/username and password.")
            return

        # 2. Ask the backend (BACKEND INTEGRATION POINT: backend.login_user)
        result = backend.login_user(identifier, password)

        # 3. Show the result
        if result["success"]:
            self.app.current_user = result["data"]   # remember who is logged in
            self.app.show_screen("dashboard")
        else:
            self.message.show_error(result["message"])
