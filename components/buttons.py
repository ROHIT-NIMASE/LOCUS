"""
components/buttons.py - the 4 button styles used across LOCUS.
Using these (instead of raw CTkButton) keeps every button consistent.
"""
import customtkinter as ctk
from theme import COLORS, font


def primary_button(parent, text, command, width=360, height=42):
    """Main action (Login, Confirm Booking...)."""
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=height,
                         corner_radius=8, font=font(14, True),
                         fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                         text_color="white")


def secondary_button(parent, text, command, width=360, height=42):
    """Less important action (Back, Create Account...). White with blue outline."""
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=height,
                         corner_radius=8, font=font(14, True),
                         fg_color="white", hover_color=COLORS["primary_light"],
                         text_color=COLORS["primary"],
                         border_width=1, border_color=COLORS["primary"])


def danger_button(parent, text, command, width=160, height=36):
    """Destructive action (Cancel Booking)."""
    return ctk.CTkButton(parent, text=text, command=command, width=width, height=height,
                         corner_radius=8, font=font(13, True),
                         fg_color="#DC2626", hover_color="#B91C1C", text_color="white")


def link_button(parent, text, command):
    """Plain text button for small links (Logout...)."""
    return ctk.CTkButton(parent, text=text, command=command, height=28, width=0,
                         fg_color="transparent", hover_color=COLORS["primary_light"],
                         text_color=COLORS["primary"], font=font(13, True))
