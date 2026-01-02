"""KdeDialogsPart - Desktop part for all Linux dialogs.
"""

from ..gnome.dialogs import GnomeDialogsPart


class KdeDialogsPart(GnomeDialogsPart):
    """KDE desktop dialogs implementation.

    Inherits all functionality from LinuxDialogsPart without modifications.
    KDE uses the same pymsgbox-based dialogs as the base Linux implementation.
    """
    pass
