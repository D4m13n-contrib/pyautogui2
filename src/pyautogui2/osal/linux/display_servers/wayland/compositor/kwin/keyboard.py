"""KWinKeyboardPart - Wayland compositor part for KWin keyboard layout queries."""

from .......utils.exceptions import PyAutoGUIException
from .......utils.keyboard_layouts import KEYBOARD_LAYOUTS
from ......abstract_cls import AbstractKeyboard
from ._backend import KwinBackend


class KWinKeyboardPart(AbstractKeyboard):
    """KWin on Wayland keyboard layout provider via DBus.

    Queries the active keyboard layout from the KDE keyboard DBus service
    (``org.kde.keyboard``). Returns the layout name (e.g. ``"QWERTY"``,
    ``"AZERTY"``) of the currently active layout.

    DBus Interface:
        - Service:    ``org.kde.keyboard``
        - Object:     ``/Layouts``
        - Methods:    ``getLayoutsList()``, ``getLayout()``

    Implementation Notes:
        - Delegates all DBus communication to ``KwinBackend``.
        - All other keyboard methods (key_down, key_up, etc.) are provided
          by WaylandKeyboardPart (uinput-based).

    See Also:
        - _backend.py: KwinBackend DBus implementation.
        - KwinScreenPart: Screen geometry queries.
    """

    def __init__(self, *args, **kwargs):
        """Initialize KwinKeyboardPart with a shared KwinBackend instance."""
        super().__init__(*args, **kwargs)
        self._backend = KwinBackend()

    def get_layout(self) -> str:
        """Raises:
            PyAutoGUIException: If the layout is not supported.
        """
        layout = self._backend.get_keyboard_layout()
        if layout not in KEYBOARD_LAYOUTS['linux']:
            raise PyAutoGUIException(f"Layout '{layout}' is unsupported by PyAutoGUI")

        return KEYBOARD_LAYOUTS['linux'][layout]['layout']
