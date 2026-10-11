"""ui/register.py - Screen 2: Registration."""
import re
import customtkinter as ctk
from services import backend
from theme import COLORS, APP_NAME, font
from components.buttons import primary_button, secondary_button
from components.inputs import labeled_entry
from components.messages import MessageBanner


class RegisterScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"])
        self.app = app

        card = ctk.CTkFrame(self, fg_color=COLORS["card"], corner_radius=16,
                            border_width=1, border_color=COLORS["border"])
        card.place(relx=0.5, rely=0.5, anchor="center")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=44, pady=28)

        ctk.CTkLabel(inner, text=APP_NAME, font=font(30, True),
                     text_color=COLORS["primary"]).pack()
        ctk.CTkLabel(inner, text="Create your account", font=font(16, True),
                     text_color=COLORS["text"]).pack(pady=(2, 4))

        self.name_entry = labeled_entry(inner, "Full name", "e.g. Sam Patil")
        self.student_id_entry = labeled_entry(inner, "Student ID", "e.g. S1234")
        self.email_entry = labeled_entry(inner, "Email", "student@college.edu")
        self.password_entry = labeled_entry(inner, "Password", "At least 6 characters", show="•")
        self.confirm_entry = labeled_entry(inner, "Confirm password", "Re-enter your password", show="•")

        self.message = MessageBanner(inner)
        self.message.pack(pady=(12, 6))

        primary_button(inner, "Register", self.handle_register).pack(pady=(0, 8))
        secondary_button(inner, "Back to Login",
                         lambda: self.app.show_screen("login")).pack()

    def validate(self, name, student_id, email, password, confirm):
        """Basic frontend checks. Returns an error message, or None if everything is fine.
        (The backend must still validate again - never trust the UI alone.)"""
        if not (name and student_id and email and password and confirm):
            return "Please fill in all fields."
        if not student_id.isalnum():
            return "Student ID can contain only letters and numbers."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return "Please enter a valid email address."
        if len(password) < 6:
            return "Password must be at least 6 characters."
        if password != confirm:
            return "Passwords do not match."
        return None

    def handle_register(self):
        name = self.name_entry.get().strip()
        student_id = self.student_id_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        error = self.validate(name, student_id, email, password, confirm)
        if error:
            self.message.show_error(error)
            return

        # BACKEND INTEGRATION POINT: backend.register_user
        result = backend.register_user(name, student_id, email, password)

        if result["success"]:
            # Go back to login and show a success message there
            self.app.show_screen("login", notice="Account created! You can now log in.")
        else:
            self.message.show_error(result["message"])
