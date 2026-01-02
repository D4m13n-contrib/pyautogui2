"""GnomeScreenPart - Desktop part for all Linux screens.
"""

from ....abstract_cls import AbstractScreen


class GnomeScreenPart(AbstractScreen):
    """GNOME desktop screen implementation.

    Empty placeholder class that inherits all functionality from AbstractScreen.
    The actual implementation comes from LinuxScreenPart through multiple
    inheritance in the dynamically composed Linux class.

    Implementation Notes:
        - No GNOME-specific screen behavior at the desktop level
        - Screen dimensions are handled by display server Parts (X11/Wayland)
        - This class exists for architectural consistency
    """
    pass
