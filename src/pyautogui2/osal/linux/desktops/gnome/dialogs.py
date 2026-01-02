"""GnomeDialogsPart - Desktop part for all Linux dialogs.
"""

from ....abstract_cls import AbstractDialogs


class GnomeDialogsPart(AbstractDialogs):
    """GNOME desktop dialogs implementation.

    Inherits all functionality from LinuxDialogsPart without modifications.
    GNOME uses the same pymsgbox-based dialogs as the base Linux implementation.
    """
    pass
