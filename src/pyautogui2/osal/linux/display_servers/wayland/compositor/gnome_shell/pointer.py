"""GnomeShellPointerPart - Wayland part for all Linux pointers.
"""
from typing import TYPE_CHECKING, Optional

from .......utils.types import Point
from ......abstract_cls import AbstractPointer


if TYPE_CHECKING:
    from ._backend import GnomeShellBackend


class GnomeShellPointerPart(AbstractPointer):
    """GNOME Shell on Wayland pointer position provider via D-Bus extension.

    Provides pointer position queries for Wayland+GNOME environments where
    the compositor restricts direct position access. Communicates with the
    custom GNOME Shell extension via D-Bus to retrieve cursor coordinates.

    All pointer actions (movement, clicks, scroll) are inherited from
    WaylandPointerPart (uinput-based).

    Implementation Notes:
        - Only implements get_pos() - all actions use WaylandPointerPart.
        - Lazy loads GnomeShellBackend on first position query.
        - Requires GNOME Shell extension installed and enabled.
        - Removes default decorator from get_pos() for direct D-Bus query.

    Dependencies:
        - GNOME Shell extension: gnome-wayland@pyautogui.org.
        - GnomeShellBackend D-Bus interface.
        - Extension must be enabled in GNOME Extensions app.

    See Also:
        - _backend.py: GnomeShellBackend implementation.
        - extension/: GNOME Shell extension source code.
    """

    def __init__(self, *args, **kwargs):
        """Initialize GNOME Shell pointer without establishing D-Bus connection.

        Defers D-Bus backend connection until first get_pos() call (lazy loading).
        """
        super().__init__(*args, **kwargs)
        self._backend: Optional[GnomeShellBackend] = None

    @property
    def backend(self) -> "GnomeShellBackend":
        """Get or create the D-Bus backend connection to GNOME Shell extension.

        Lazy-loads the GnomeShellBackend singleton that handles D-Bus communication
        with the extension. Connection is established on first access.

        Returns:
            GnomeShellBackend: Singleton D-Bus backend instance.

        Implementation Notes:
            - Imports GnomeShellBackend only when needed.
            - Backend is shared across all OSAL components.
            - Raises RuntimeError if extension not installed/enabled.
        """
        if self._backend is None:
            from ._backend import GnomeShellBackend
            self._backend = GnomeShellBackend()
        return self._backend

    def get_pos(self) -> Point:
        """Implementation Notes:
            - Calls backend.get_pointer_position() (D-Bus GetPosition method).
            - Converts float coordinates to integers.
            - Works across all monitors in multi-monitor setups.
            - No decorator applied (bypasses default position handling).

        Raises:
            RuntimeError: If D-Bus backend connection fails (extension issue).
        """
        x, y = self.backend.get_pointer_position()
        return Point(int(x), int(y))
