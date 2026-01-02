"""KdePointerPart - Desktop part for all Linux pointers.
"""

from ..gnome.pointer import GnomePointerPart


class KdePointerPart(GnomePointerPart):
    """KDE desktop pointer configuration handler.

    Inherits GNOME's left-handed detection logic as KDE uses compatible
    configuration mechanisms. No KDE-specific pointer behavior required.
    """
    pass
