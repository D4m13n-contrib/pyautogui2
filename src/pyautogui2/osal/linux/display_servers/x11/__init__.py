"""X11 display server OSAL loader."""

from .dialogs import X11DialogsPart
from .keyboard import X11KeyboardPart
from .pointer import X11PointerPart
from .screen import X11ScreenPart


def get_x11_osal_parts() -> dict[str, type]:
    """Return X11-specific OSAL parts for Linux integration."""
    return {
        "pointer": X11PointerPart,
        "keyboard": X11KeyboardPart,
        "screen": X11ScreenPart,
        "dialogs": X11DialogsPart,
    }
