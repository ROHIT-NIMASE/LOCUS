"""
components/page_header.py - the top bar shown on every screen after the dashboard.
Shows the LOCUS name, the screen title, and a Home button.
"""
import customtkinter as ctk
from theme import COLORS, APP_NAME, font
from components.buttons import link_button


def page_header(parent, app, title):
    """Creates AND packs the header bar at the top of `parent`."""
    header = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=0, height=64)
    header.pack(fill="x")
    header.pack_propagate(False)

    ctk.CTkLabel(header, text=APP_NAME, font=font(24, True),
                 text_color=COLORS["primary"]).pack(side="left", padx=(40, 14))
    ctk.CTkLabel(header, text=f"›   {title}", font=font(16, True),
                 text_color=COLORS["text_muted"]).pack(side="left")
    link_button(header, "Home", lambda: app.show_screen("dashboard")).pack(side="right", padx=40)

    # thin line under the header
    ctk.CTkFrame(parent, fg_color=COLORS["border"], height=1, corner_radius=0).pack(fill="x")
