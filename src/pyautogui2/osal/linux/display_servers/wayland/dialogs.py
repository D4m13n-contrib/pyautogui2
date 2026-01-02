"""WaylandDialogsPart - Display server part for all Linux dialogs.
"""
from ....abstract_cls import AbstractDialogs


class WaylandDialogsPart(AbstractDialogs):
    """Wayland display server dialogs implementation.

    Empty placeholder class that inherits all functionality from AbstractDialogs.
    The actual implementation comes from LinuxDialogsPart through multiple
    inheritance in the dynamically composed Linux class.

    Implementation Notes:
        - No Wayland-specific dialog behavior needed
        - pymsgbox (inherited via LinuxDialogsPart) works on Wayland
        - This class exists for architectural consistency
    """
    pass
