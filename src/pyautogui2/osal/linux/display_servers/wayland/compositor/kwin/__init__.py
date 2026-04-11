"""KWin backend parts for Wayland OSAL.

Provides compositor-specific parts (Pointer, Keyboard, etc.)
for the KWin Wayland compositor.
"""

def get_kwin_osal_parts() -> dict[str, type]:
    """Return KWin-specific OSAL parts for Wayland integration."""
    from .keyboard import KWinKeyboardPart
    from .pointer import KWinPointerPart
    from .screen import KWinScreenPart

    return {
        "pointer": KWinPointerPart,
        "keyboard": KWinKeyboardPart,
        "screen": KWinScreenPart,
    }
