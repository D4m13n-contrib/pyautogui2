"""GnomeKeyboardPart - Desktop part for all Linux keyboards.
"""

from ....abstract_cls import AbstractKeyboard


class GnomeKeyboardPart(AbstractKeyboard):
    """GNOME desktop keyboard implementation.

    Empty placeholder class that inherits all functionality from AbstractKeyboard.
    The actual implementation comes from LinuxKeyboardPart (codepoint input) and
    display server Parts (X11/Wayland key actions and layout detection) through
    multiple inheritance in the dynamically composed Linux class.

    Implementation Notes:
        - No GNOME-specific keyboard behavior at the desktop level
        - Layout detection handled by display server Parts (X11/Wayland)
        - Key actions delegated to display server Parts
        - This class exists for architectural consistency
    """
    pass
