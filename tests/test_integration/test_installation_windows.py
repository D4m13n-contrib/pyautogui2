"""Windows-specific installation tests."""

import pytest

from tests.fixtures.helpers import is_windows


if not is_windows():
    pytest.skip("Requires Windows platform", allow_module_level=True)


@pytest.mark.windows
class TestWindowsInstallation:
    """Tests specific to Windows platform."""

    def test_pygetwindow_installed(self):
        """Test that pygetwindow is installed."""
        try:
            import pygetwindow
            assert pygetwindow is not None
        except ImportError:
            pytest.fail("pygetwindow is not installed (required for Windows)")

    def test_ctypes_windll_available(self):
        """Test that ctypes.windll is available."""
        import ctypes
        assert hasattr(ctypes, 'windll'), "ctypes.windll not available (Windows-specific)"
        assert ctypes.windll is not None

    def test_win32api_imports(self):
        """Test that Windows-specific modules can be imported."""
        from pyautogui2.osal.windows import _common
        assert _common is not None

    @pytest.mark.real
    def test_mouse_position(self):
        """Test mouse position retrieval (real system call)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        x, y = gui.pointer.get_position()
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))
        assert x >= 0
        assert y >= 0

    @pytest.mark.real
    def test_screen_size(self):
        """Test screen size retrieval (real system call)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        size = gui.screen.get_size()
        assert size.width > 0
        assert size.height > 0

    @pytest.mark.real
    def test_mouse_move(self):
        """Test mouse movement (real system action)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        # Force stable position before test
        gui.pointer.move_to(100, 100)

        # Get current position
        x1, y1 = gui.pointer.get_position()

        # Move to new position
        target_x, target_y = x1 + 10, y1 + 10
        gui.pointer.move_to(target_x, target_y)

        # Verify movement
        x2, y2 = gui.pointer.get_position()
        assert x2 == target_x
        assert y2 == target_y

        # Move back
        gui.pointer.move_to(x1, y1)

    @pytest.mark.real
    def test_keyboard_typing(self):
        """Test keyboard typing (real system action - basic check)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        # Just verify the method exists and doesn't crash
        # (actual typing test would require a text field)
        assert hasattr(gui.keyboard, 'write')

    @pytest.mark.real
    def test_screenshot(self):
        """Test screenshot functionality (real system call)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        screenshot = gui.screen.screenshot()
        assert screenshot is not None
        assert screenshot.width > 0
        assert screenshot.height > 0


@pytest.mark.windows
class TestWindowsInputSimulation:
    """Tests for Windows input simulation specifics."""

    def test_sendinput_available(self):
        """Test that SendInput Win32 API is accessible."""
        from pyautogui2.osal.windows._common import send_input
        assert send_input is not None

    @pytest.mark.real
    def test_vk_codes_available(self):
        """Test that virtual key codes are defined."""
        from pyautogui2.osal.windows.keyboard import WindowsKeyboard
        keyboard = WindowsKeyboard()

        # Check some common VK codes exist
        assert hasattr(keyboard, '_key_to_vk') or hasattr(keyboard, 'keyboardMapping')

    @pytest.mark.real
    def test_mouse_click(self):
        """Test mouse click (real system action - be careful!)."""
        import time

        from pyautogui2 import PyAutoGUI

        gui = PyAutoGUI()

        # Get current position (don't click anywhere dangerous)
        x, y = gui.pointer.get_position()

        # Small delay to allow user to move mouse if needed
        time.sleep(0.5)

        # Click at safe location (current position)
        gui.pointer.click(x, y, button='left', clicks=1)

        # Verify no crash
        assert True


@pytest.mark.windows
class TestWindowsDPIAwareness:
    """Tests for Windows DPI awareness."""

    def test_dpi_awareness_function_exists(self):
        """Test that DPI awareness function exists."""
        from pyautogui2.osal.windows._common import ensure_dpi_aware
        assert ensure_dpi_aware is not None

    @pytest.mark.real
    def test_screen_coordinates_accurate(self):
        """Test that screen coordinates account for DPI scaling."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()

        # Get mouse position at corner
        gui.pointer.move_to(1, 1)
        x, y = gui.pointer.get_position()

        # Should be at/near origin (accounting for DPI)
        assert x <= 5
        assert y <= 5
