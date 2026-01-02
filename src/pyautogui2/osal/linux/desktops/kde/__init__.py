"""KDE desktop parts for OSAL."""

from .dialogs import KdeDialogsPart
from .keyboard import KdeKeyboardPart
from .pointer import KdePointerPart
from .screen import KdeScreenPart


def get_kde_osal_parts() -> dict[str, type]:
    """Return KDE desktop-specific OSAL parts for Linux integration."""
    return {
        "pointer": KdePointerPart,
        "keyboard": KdeKeyboardPart,
        "screen": KdeScreenPart,
        "dialogs": KdeDialogsPart,
    }
