"""XfceScreenPart - Desktop part for all Linux screens.
"""

from ..gnome.screen import GnomeScreenPart


class XfceScreenPart(GnomeScreenPart):
    """XFCE desktop screen implementation.

    Inherits all functionality from GnomeScreenPart (which is a placeholder).
    The actual implementation comes from LinuxScreenPart through multiple
    inheritance in the dynamically composed Linux class.

    Implementation Notes:
        - No XFCE-specific screen behavior at the desktop level
        - Screen dimensions are handled by display server Parts (X11/Wayland)
        - Inherits from GnomeScreenPart for consistency with other XFCE components
    """
    pass
