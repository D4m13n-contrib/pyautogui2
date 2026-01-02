"""XFCE desktop parts for OSAL."""

from .dialogs import XfceDialogsPart
from .keyboard import XfceKeyboardPart
from .pointer import XfcePointerPart
from .screen import XfceScreenPart


def get_xfce_osal_parts() -> dict[str, type]:
    """Return XFCE desktop-specific OSAL parts for Linux integration."""
    return {
        "pointer": XfcePointerPart,
        "keyboard": XfceKeyboardPart,
        "screen": XfceScreenPart,
        "dialogs": XfceDialogsPart,
    }
