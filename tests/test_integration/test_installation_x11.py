"""X11-specific installation tests."""

import pytest

from tests.fixtures.helpers import is_linux_ds_x11


if not is_linux_ds_x11():
    pytest.skip("Requires X11 display server", allow_module_level=True)


@pytest.mark.linux
@pytest.mark.linux_x11
class TestX11Installation:
    """Tests specific to X11 display server."""

    def test_xlib_installed(self):
        """Test that python-xlib is installed."""
        try:
            import Xlib
            assert Xlib is not None
        except ImportError:
            pytest.fail("python-xlib is not installed (required for X11)")

    @pytest.mark.real
    def test_mouse_move(self, pyautogui_real):
        """Test mouse movement (real system action)."""
        # Force stable position before test
        pyautogui_real.pointer.move_to(100, 100)

        # Get current position
        x1, y1 = pyautogui_real.pointer.get_position()

        # Move to new position
        target_x, target_y = x1 + 10, y1 + 10
        pyautogui_real.pointer.move_to(target_x, target_y)

        # Verify movement
        x2, y2 = pyautogui_real.pointer.get_position()
        assert x2 == target_x
        assert y2 == target_y

        # Move back
        pyautogui_real.pointer.move_to(x1, y1)

    @pytest.mark.real
    def test_keyboard_typing(self, pyautogui_real):
        """Test keyboard typing (real system action - basic check)."""
        # Just verify the method exists and doesn't crash
        # (actual typing test would require a text field)
        assert hasattr(pyautogui_real.keyboard, 'write')
