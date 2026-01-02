"""MacOS-specific installation tests."""

import pytest

from tests.fixtures.helpers import is_macos


if not is_macos():
    pytest.skip("Requires MacOS (Darwin) platform", allow_module_level=True)


@pytest.mark.macos
class TestMacOSInstallation:
    """Tests specific to MacOS (Darwin) platform."""

    def test_pyobjc_core_installed(self):
        """Test that pyobjc-core is installed."""
        try:
            import objc
            assert objc is not None
        except ImportError:
            pytest.fail("pyobjc-core is not installed (required for MacOS)")

    def test_pyobjc_quartz_installed(self):
        """Test that pyobjc-framework-Quartz is installed."""
        try:
            import Quartz
            assert Quartz is not None
        except ImportError:
            pytest.fail("pyobjc-framework-Quartz is not installed (required for MacOS)")

    def test_quartz_core_graphics_available(self):
        """Test that Quartz Core Graphics is accessible."""
        try:
            from Quartz import CGEventCreateMouseEvent, CGEventPost
            assert CGEventPost is not None
            assert CGEventCreateMouseEvent is not None
        except ImportError:
            pytest.fail("Quartz Core Graphics not accessible")

    def test_macos_modules_import(self):
        """Test that MacOS-specific modules can be imported."""
        from pyautogui2.osal.macos import MacOSKeyboard, MacOSPointer, MacOSScreen
        assert MacOSKeyboard is not None
        assert MacOSPointer is not None
        assert MacOSScreen is not None

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


@pytest.mark.macos
class TestMacOSAccessibility:
    """Tests for MacOS accessibility permissions."""

    def test_accessibility_api_available(self):
        """Test that MacOS Accessibility API is available."""
        try:
            from Quartz import CGEventPost
            assert CGEventPost is not None
        except ImportError:
            pytest.fail("MacOS Accessibility API not available")

    @pytest.mark.real
    def test_accessibility_permissions_check(self):
        """Test accessibility permissions (might need manual grant)."""
        import time

        from pyautogui2 import PyAutoGUI

        gui = PyAutoGUI()

        try:
            # Try to move mouse (requires accessibility permissions)
            x, y = gui.pointer.get_position()
            gui.pointer.move_to(x + 1, y + 1)
            time.sleep(0.1)
            gui.pointer.move_to(x, y)

            # If we get here, permissions are OK
            assert True

        except Exception as e:
            # If permissions denied, provide helpful message
            if "accessibility" in str(e).lower() or "permission" in str(e).lower():
                pytest.fail(
                    "Accessibility permissions not granted. "
                    "Go to System Preferences > Security & Privacy > Privacy > Accessibility "
                    "and grant access to Terminal/Python"
                )
            else:
                # Re-raise unexpected errors
                raise


@pytest.mark.macos
class TestMacOSCatchUpTime:
    """Tests for MacOS DARWIN_CATCH_UP_TIME setting."""

    def test_darwin_catch_up_time_setting_exists(self, isolated_settings):
        """Test that DARWIN_CATCH_UP_TIME setting exists."""
        assert isolated_settings.DARWIN_CATCH_UP_TIME is not None
        assert isinstance(isolated_settings.DARWIN_CATCH_UP_TIME, (int, float))
        assert isolated_settings.DARWIN_CATCH_UP_TIME >= 0

    @pytest.mark.real
    def test_rapid_mouse_movements(self):
        """Test rapid mouse movements with catch-up time."""
        import time

        from pyautogui2 import PyAutoGUI

        gui = PyAutoGUI()

        # Get starting position
        x1, y1 = gui.pointer.get_position()

        # Perform rapid movements
        for i in range(5):
            gui.pointer.move_to(x1 + 10 * i, y1 + 10 * i)
            time.sleep(0.05)  # Small delay

        # Return to start
        gui.pointer.move_to(x1, y1)

        # Verify we're back (accounting for catch-up time)
        time.sleep(0.1)
        x2, y2 = gui.pointer.get_position()
        assert abs(x2 - x1) <= 5
        assert abs(y2 - y1) <= 5


@pytest.mark.macos
class TestMacOSInputSimulation:
    """Tests for MacOS input simulation specifics."""

    def test_quartz_event_types_available(self):
        """Test that Quartz event types are defined."""
        from Quartz import (
            kCGEventKeyDown,
            kCGEventKeyUp,
            kCGEventLeftMouseDown,
            kCGEventLeftMouseUp,
            kCGEventRightMouseDown,
            kCGEventRightMouseUp,
        )
        assert kCGEventLeftMouseDown is not None
        assert kCGEventLeftMouseUp is not None
        assert kCGEventRightMouseDown is not None
        assert kCGEventRightMouseUp is not None
        assert kCGEventKeyDown is not None
        assert kCGEventKeyUp is not None

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

    @pytest.mark.real
    def test_keyboard_mappings_exist(self):
        """Test that keyboard mappings are defined."""
        from pyautogui2.osal.macos.keyboard import MacOSKeyboard
        keyboard = MacOSKeyboard()

        # Check that keyboard mapping exists
        assert hasattr(keyboard, 'keyboardMapping') or hasattr(keyboard, '_key_to_keycode')
