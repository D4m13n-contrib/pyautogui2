"""WaylandScreenPart - Display server part for all Linux screens.
"""
from ....abstract_cls import AbstractScreen


class WaylandScreenPart(AbstractScreen):
    """Wayland display server screen implementation.

    Empty placeholder class that inherits all functionality from AbstractScreen.
    Wayland-specific screen dimension handling is delegated to compositor-specific
    Parts (e.g., GnomeShellScreenPart) that communicate with the compositor via
    D-Bus or other IPC mechanisms.

    Implementation Notes:
        - Wayland has no direct screen query API (security by design)
        - Screen operations require compositor-specific backends
        - Screenshot and window management inherited from LinuxScreenPart work
          through compositor-provided protocols (e.g., xdg-desktop-portal)
        - This class exists for architectural consistency
    """
    pass
