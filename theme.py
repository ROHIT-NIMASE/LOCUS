"""
theme.py - the LOCUS look and feel.
All colours and fonts are defined here ONCE, so every screen looks consistent.
To change the colour scheme of the whole app, edit only this file.
"""
import customtkinter as ctk

APP_NAME = "LOCUS"
TAGLINE = "Smart Library Seating"

COLORS = {
    "primary": "#1E3A8A",        # deep blue = LOCUS identity colour
    "primary_hover": "#1E40AF",
    "primary_light": "#E0E7FF",
    "bg": "#F3F5F9",             # window background
    "card": "#FFFFFF",           # white cards
    "border": "#D9DEE8",
    "text": "#1F2937",
    "text_muted": "#6B7280",
    "success": "#166534",
    "success_bg": "#DCFCE7",
    "error": "#991B1B",
    "error_bg": "#FEE2E2",
    "info": "#1E3A8A",
    "info_bg": "#E0E7FF",
}

# Colours for each seat state (used by seat_card.py and the legend later)
SEAT_COLORS = {
    "available":   {"bg": "#DCFCE7", "border": "#22C55E", "text": "#166534", "hover": "#BBF7D0"},
    "occupied":    {"bg": "#FEE2E2", "border": "#EF4444", "text": "#991B1B", "hover": "#FEE2E2"},
    "unavailable": {"bg": "#F3F4F6", "border": "#9CA3AF", "text": "#6B7280", "hover": "#F3F4F6"},
    "selected":    {"bg": "#1E3A8A", "border": "#1E3A8A", "text": "#FFFFFF", "hover": "#1E40AF"},
}

FONT_FAMILY = "Segoe UI"  # falls back to a default font on Mac/Linux


def font(size=14, bold=False):
    """Returns a font so every screen uses the same typeface."""
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold" if bold else "normal")

# Colours for booking status badges (used by components/booking_card.py)
STATUS_COLORS = {
    "Upcoming":  {"bg": "#DBEAFE", "text": "#1E40AF"},
    "Active":    {"bg": "#DCFCE7", "text": "#166534"},
    "Completed": {"bg": "#F3F4F6", "text": "#4B5563"},
    "Cancelled": {"bg": "#FEE2E2", "text": "#991B1B"},
    "No-show":   {"bg": "#FEF3C7", "text": "#92400E"},
}
