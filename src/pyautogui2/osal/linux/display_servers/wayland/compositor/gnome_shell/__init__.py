"""GNOME Shell backend parts for Wayland OSAL.

Provides compositor-specific parts (Pointer, Keyboard, etc.)
for the GNOME Shell Wayland compositor.

This backend communicates with the GNOME Shell extension 'gnome-wayland@pyautogui.org'
via D-Bus to provide input and screen information.
"""

def get_gnome_shell_osal_parts() -> dict[str, type]:
    """Return GNOME Shell-specific OSAL parts for Wayland integration."""
    from .keyboard import GnomeShellKeyboardPart
    from .pointer import GnomeShellPointerPart
    from .screen import GnomeShellScreenPart

    return {
        "pointer": GnomeShellPointerPart,
        "keyboard": GnomeShellKeyboardPart,
        "screen": GnomeShellScreenPart,
    }
