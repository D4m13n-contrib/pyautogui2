"""KWinScreenPart - Wayland compositor part for KWin screen geometry queries."""

from .......utils.types import Size
from ......abstract_cls import AbstractScreen
from ._backend import KwinBackend


class KWinScreenPart(AbstractScreen):
    """KWin on Wayland screen geometry provider via DBus.

    Queries monitor layout and resolution from the KDE KScreen DBus service.
    Computes the virtual screen bounding box from all active monitors,
    following the same convention as GnomeShellScreenPart.

    DBus Interface:
        - Service:    ``org.kde.KScreen``
        - Object:     ``/``
        - Methods:    ``getOutputs()``

    Implementation Notes:
        - ``get_size_max()`` returns the bounding box of all active monitors
          (same semantic as GnomeShellScreenPart).
        - Delegates all DBus communication to ``KwinBackend``.
        - Returns ``Size(0, 0)`` if no active monitor is found.

    See Also:
        - _backend.py: KwinBackend DBus implementation.
        - KwinKeyboardPart: Keyboard layout queries.
    """

    def __init__(self, *args, **kwargs):
        """Initialize KwinScreenPart with a shared KwinBackend instance."""
        super().__init__(*args, **kwargs)
        self._backend = KwinBackend()

    def get_size(self) -> Size:
        """Get the current screen size by parsing xrandr output.

        Returns:
            Size: Named tuple ``(width, height)`` in pixels representing
                the primary screen size.
                Returns ``Size(0, 0)`` if no active monitor is found.
        """
        return self._backend.get_size()

    def get_size_max(self) -> Size:
        """Get the bounding box of all active monitors.

        Computes the maximum extent of the virtual screen space by finding
        the rightmost and bottommost edges across all connected monitors.
        Monitors that are disabled are excluded.

        Returns:
            Size: Named tuple ``(width, height)`` in pixels representing
                the full virtual screen bounding box.
                Returns ``Size(0, 0)`` if no active monitor is found.
        """
        return self._backend.get_size_max()

