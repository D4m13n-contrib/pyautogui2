"""GnomeShellDialogsPart - Wayland part for all Linux dialogs.
"""
from ......abstract_cls import AbstractDialogs


class GnomeShellDialogsPart(AbstractDialogs):
    """GNOME Shell on Wayland dialogs implementation.

    Empty placeholder class that inherits all functionality from AbstractDialogs.
    The actual implementation comes from LinuxDialogsPart through multiple
    inheritance in the dynamically composed Linux class.

    Implementation Notes:
        - No GNOME Shell-specific dialog behavior needed
        - pymsgbox (inherited via LinuxDialogsPart) works on GNOME/Wayland
        - This class exists for architectural consistency
    """
    pass
