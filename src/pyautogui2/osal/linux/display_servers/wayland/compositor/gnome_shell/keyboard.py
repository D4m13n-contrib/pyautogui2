"""GnomeShellKeyboardPart - Wayland part for all Linux keyboards.
"""
from typing import TYPE_CHECKING, Optional

from .......utils.exceptions import PyAutoGUIException
from .......utils.keyboard_layouts import KEYBOARD_LAYOUTS
from ......abstract_cls import AbstractKeyboard


if TYPE_CHECKING:
    from ._backend import GnomeShellBackend


class GnomeShellKeyboardPart(AbstractKeyboard):
    """GNOME Shell on Wayland keyboard layout provider via D-Bus extension.

    Provides keyboard layout queries for Wayland+GNOME environments where
    the compositor restricts direct layout access. Communicates with the
    custom GNOME Shell extension via D-Bus to retrieve active layout.

    All key actions (press/release) are inherited from WaylandKeyboardPart
    (uinput-based).

    Implementation Notes:
        - Only implements get_layout() - all actions use WaylandKeyboardPart.
        - Lazy loads GnomeShellBackend on first layout query.
        - Requires GNOME Shell extension installed and enabled.

    Dependencies:
        - GNOME Shell extension: gnome-wayland@pyautogui.org.
        - GnomeShellBackend D-Bus interface.

    See Also:
        - _backend.py: GnomeShellBackend implementation.
        - extension/: GNOME Shell extension source code.
    """

    def __init__(self, *args, **kwargs):
        """Initialize GNOME Shell keyboard without establishing D-Bus connection.

        Defers D-Bus backend connection until first get_layout() call (lazy loading).
        """
        super().__init__(*args, **kwargs)
        self._backend: Optional[GnomeShellBackend] = None

    @property
    def backend(self) -> "GnomeShellBackend":
        """Get or create the D-Bus backend connection to GNOME Shell extension.

        Implementation Notes:
            - Imports GnomeShellBackend only when needed.
            - Backend is shared across all OSAL components.
            - Raises RuntimeError if extension not installed/enabled.
        """
        if self._backend is None:
            from ._backend import GnomeShellBackend
            self._backend = GnomeShellBackend()
        return self._backend

    def get_layout(self) -> str:
        """Implementation Notes:
            - Calls backend.get_keyboard_layout() (D-Bus GetKeyboardLayout method).
            - Required on Wayland due to security restrictions.
            - Returns currently active layout (not all configured layouts).

        Raises:
            RuntimeError: If D-Bus backend connection fails (extension issue).
        """
        layout = self.backend.get_keyboard_layout()

        if layout not in KEYBOARD_LAYOUTS['linux']:
            raise PyAutoGUIException(f"Layout '{layout}' is unsupported by PyAutoGUI")

        return KEYBOARD_LAYOUTS['linux'][layout]['layout']
