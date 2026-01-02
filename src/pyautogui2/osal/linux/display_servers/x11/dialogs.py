"""X11DialogsPart - Display server part for all Linux dialogs.
"""
from ....abstract_cls import AbstractDialogs


class X11DialogsPart(AbstractDialogs):
    """X11 display server dialogs implementation.

    Empty placeholder class that inherits all functionality from AbstractDialogs.
    The actual implementation comes from LinuxDialogsPart through multiple
    inheritance in the dynamically composed Linux class.

    Implementation Notes:
        - No X11-specific dialog behavior needed
        - pymsgbox (inherited via LinuxDialogsPart) works on X11
        - This class exists for architectural consistency
    """
    pass
