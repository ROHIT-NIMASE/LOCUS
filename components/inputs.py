"""
components/inputs.py - one helper for "label + text box", used by Login and Register.
"""
import customtkinter as ctk
from theme import COLORS, font


def labeled_entry(parent, label_text, placeholder="", show=None, width=360):
    """Creates a label and an entry box, packs them, and returns the entry.
    Use show="•" for password boxes. Read the text later with entry.get()."""
    ctk.CTkLabel(parent, text=label_text, font=font(13, True),
                 text_color=COLORS["text"]).pack(anchor="w", pady=(10, 2))
    entry = ctk.CTkEntry(parent, placeholder_text=placeholder, show=show, width=width,
                         height=40, corner_radius=8, font=font(14),
                         fg_color="white", text_color=COLORS["text"],
                         border_color=COLORS["border"])
    entry.pack()
    return entry
