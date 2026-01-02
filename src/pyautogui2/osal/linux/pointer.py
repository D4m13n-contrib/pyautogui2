"""LinuxPointerPart - Base part for all Linux pointers.
"""
from typing import Any

from ...utils.lazy_import import lazy_import
from ...utils.types import ButtonName
from ..abstract_cls import AbstractPointer


class LinuxPointerPart(AbstractPointer):
    """Base Linux pointer implementation providing platform-independent operations.

    Provides high-level pointer operations that work identically across all Linux
    configurations (desktop environments and display servers). Low-level operations
    like position queries and hardware interaction are delegated to display server
    Parts (X11/Wayland-specific).

    Implementation Notes:
        - Uses mouseinfo for cursor information utilities
        - Drag operation combines move_to() and button control from subclasses
        - Desktop/display server Parts handle actual hardware interaction
        - This Part focuses on cross-platform Linux abstractions
    """

    _mouseinfo = lazy_import("mouseinfo")

    def mouse_info(self) -> None:
        self._mouseinfo.MouseInfoWindow()

    def drag_to(self, x: int, y: int, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        self.button_down(button, _pause=False)
        self.move_to(x, y, _pause=False)
        self.button_up(button, _pause=False)
