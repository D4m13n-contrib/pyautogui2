"""Tests for LinuxPointerPart."""

from unittest.mock import call

from pyautogui2.utils.types import ButtonName


class TestLinuxPointerMouseInfo:
    """Tests for mouse_info() function."""

    def test_mouse_info_delegate(self, linux_pointer):
        """Call mouse_info() delegates to mouseinfo library."""
        linux_pointer.mouse_info()
        linux_pointer._mouseinfo.MouseInfoWindow.assert_called_once()


class TestLinuxPointerDragTo:
    """Tests for drag_to() function."""

    def test_drag_to_delegate(self, linux_pointer):
        """Call drag_to() delegates button_down(), move_to(), and button_up()."""
        linux_pointer.drag_to(100, 100)
        linux_pointer.mocks.assert_has_calls([
            call.button_down(ButtonName.PRIMARY, _pause=False),
            call.move_to(100, 100, _pause=False),
            call.button_up(ButtonName.PRIMARY, _pause=False),
        ])
