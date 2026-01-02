"""XfceKeyboardPart - Desktop part for all Linux keyboards.
"""

from ..gnome.keyboard import GnomeKeyboardPart


class XfceKeyboardPart(GnomeKeyboardPart):
    """XFCE desktop keyboard implementation.

    Inherits all functionality from GnomeKeyboardPart (which is a placeholder).
    The actual implementation comes from LinuxKeyboardPart and display server
    Parts through multiple inheritance.

    Implementation Notes:
        - No XFCE-specific keyboard behavior at the desktop level
        - Layout detection handled by display server Parts (X11/Wayland)
        - Inherits from GnomeKeyboardPart for consistency with other XFCE components
    """
    pass
