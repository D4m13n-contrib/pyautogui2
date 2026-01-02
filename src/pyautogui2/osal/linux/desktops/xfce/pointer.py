"""XfcePointerPart - Desktop part for all Linux pointers.
"""

from ..gnome.pointer import GnomePointerPart


class XfcePointerPart(GnomePointerPart):
    """XFCE desktop pointer configuration handler.

    Inherits GNOME's left-handed detection logic as XFCE uses compatible
    configuration mechanisms. No XFCE-specific pointer behavior required.
    """
    pass
