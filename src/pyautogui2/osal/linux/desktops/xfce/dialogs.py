"""XfceDialogsPart - Desktop part for all Linux dialogs.
"""

from ..gnome.dialogs import GnomeDialogsPart


class XfceDialogsPart(GnomeDialogsPart):
    """XFCE desktop dialogs implementation.

    Inherits all functionality from GnomeDialogsPart (which itself inherits
    from LinuxDialogsPart). XFCE uses the same pymsgbox-based dialogs as
    GNOME and the base Linux implementation.

    Note:
        Inherits from GnomeDialogsPart for consistency with other XFCE components,
        though functionally identical to direct LinuxDialogsPart inheritance.
    """
    pass
