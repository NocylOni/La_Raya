"""Visual theme: a sober, modern flat theme (ttkbootstrap "flatly") plus a
few small custom style tweaks (row height, heading weight, card padding)."""
from __future__ import annotations

import tkinter.font as tkfont

import ttkbootstrap as tb

THEME_NAME = "flatly"
FONT_FAMILY = "Helvetica"

# Semantic bootstyle names used consistently across the app so the same
# action always looks the same everywhere (green = save, red = delete, etc).
STYLE_PRIMARY_BUTTON = "primary"
STYLE_SECONDARY_BUTTON = "secondary"
STYLE_SUCCESS_BUTTON = "success"
STYLE_DANGER_BUTTON = "danger"
STYLE_OUTLINE_BUTTON = "outline"


def create_root() -> tb.Window:
    root = tb.Window(themename=THEME_NAME)
    _configure_fonts(root)
    _configure_custom_styles()
    return root


def _configure_fonts(root: tb.Window) -> None:
    for name in ("TkDefaultFont", "TkTextFont", "TkHeadingFont", "TkMenuFont", "TkTooltipFont"):
        try:
            font = tkfont.nametofont(name)
            font.configure(family=FONT_FAMILY, size=10)
        except Exception:
            pass


def _configure_custom_styles() -> None:
    style = tb.Style()
    style.configure("Treeview", rowheight=26, font=(FONT_FAMILY, 10))
    style.configure("Treeview.Heading", font=(FONT_FAMILY, 10, "bold"))
    style.configure("TNotebook.Tab", padding=(10, 6), font=(FONT_FAMILY, 10))
    style.configure("TLabelframe.Label", font=(FONT_FAMILY, 10, "bold"))
    style.configure("Header.TFrame", background=style.colors.primary)
    style.configure(
        "Header.TLabel", background=style.colors.primary, foreground=style.colors.get("bg"),
        font=(FONT_FAMILY, 15, "bold"),
    )
    style.configure(
        "HeaderSubtitle.TLabel", background=style.colors.primary,
        foreground=style.colors.get("bg"), font=(FONT_FAMILY, 9),
    )
    style.configure("StatusBar.TFrame", background=style.colors.light)
    style.configure("StatusBar.TLabel", background=style.colors.light, font=(FONT_FAMILY, 9))
