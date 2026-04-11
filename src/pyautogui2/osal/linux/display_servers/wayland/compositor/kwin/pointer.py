"""KWinPointerPart - Wayland compositor part for KWin pointer position."""
import logging

from .......utils.types import Point
from .......utils.decorators.failsafe import FailsafeManager
from ......abstract_cls import AbstractPointer


class KWinPointerPart(AbstractPointer):
    """KWin on Wayland pointer position provider.

    KWin (Wayland) does not expose cursor position via any DBus interface.
    ``get_pos()`` is therefore unavailable under this compositor.

    All pointer actions (movement, clicks, scroll) are inherited from
    WaylandPointerPart (uinput-based).

    Implementation Notes:
        - ``get_pos()`` raises ``NotImplementedError``.
        - All other pointer methods are provided by WaylandPointerPart.
    """

    def setup_postinit(self, *args, **kwargs):
        """Deactivates FailSafe mechanism because get_pos() method is not implemented."""
        super().setup_postinit(*args, **kwargs)

        logging.warning("FailSafe mechanism is deactivated because get_pos() function is not implemented.")
        FailsafeManager().enabled = False

    def get_pos(self) -> Point:
        """Unavailable under KWin/Wayland.

        KWin does not expose any DBus interface for querying cursor coordinates
        under Wayland.

        Raises:
            NotImplementedError: Always. Cursor position cannot be retrieved
                under KWin/Wayland.
        """
        raise NotImplementedError(
            "Cursor position is not available under KWin/Wayland. "
            "KWin does not expose a DBus interface for pointer coordinates."
        )
