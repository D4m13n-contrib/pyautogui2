"""Common installation tests for all platforms."""

import pytest


@pytest.mark.real
class TestCommonInstallation:
    """Tests that should pass on all platforms."""

    def test_import_pyautogui2(self):
        """Test that pyautogui2 can be imported."""
        from pyautogui2 import PyAutoGUI
        assert PyAutoGUI is not None

    def test_create_instance(self):
        """Test that PyAutoGUI instance can be created."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()
        assert gui is not None

    def test_controllers_exist(self):
        """Test that all controllers are accessible."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()
        assert hasattr(gui, 'pointer')
        assert hasattr(gui, 'keyboard')
        assert hasattr(gui, 'screen')
        assert hasattr(gui, 'dialogs')

    def test_mouse_position(self):
        """Test mouse position retrieval (real system call)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()
        x, y = gui.pointer.get_position()
        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))
        assert x >= 0
        assert y >= 0

    def test_screen_size(self):
        """Test screen size retrieval (real system call)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()
        size = gui.screen.get_size()
        assert size.width > 0
        assert size.height > 0

    def test_keyboard_layout(self):
        """Test keyboard layout retrieval (real system call)."""
        from pyautogui2 import PyAutoGUI
        gui = PyAutoGUI()
        layout = gui.keyboard.get_layout()
        assert len(layout) > 0


class TestDependencies:
    """Test that required dependencies are installed."""

    def test_pyscreeze_installed(self):
        """Test that pyscreeze is installed."""
        import pyscreeze
        assert pyscreeze is not None

    def test_pymsgbox_installed(self):
        """Test that pymsgbox is installed."""
        import pymsgbox
        assert pymsgbox is not None

    def test_pytweening_installed(self):
        """Test that pytweening is installed."""
        import pytweening
        assert pytweening is not None
