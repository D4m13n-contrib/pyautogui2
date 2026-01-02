"""Gnome desktop parts for OSAL."""

from .dialogs import GnomeDialogsPart
from .keyboard import GnomeKeyboardPart
from .pointer import GnomePointerPart
from .screen import GnomeScreenPart


def get_gnome_osal_parts() -> dict[str, type]:
    """Return Gnome desktop-specific OSAL parts for Linux integration."""
    return {
        "pointer": GnomePointerPart,
        "keyboard": GnomeKeyboardPart,
        "screen": GnomeScreenPart,
        "dialogs": GnomeDialogsPart,
    }
