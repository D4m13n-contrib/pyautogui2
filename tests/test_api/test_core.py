"""Tests for PyAutoGUI core wrapper class."""
from unittest.mock import patch

from pyautogui2.core import PyAutoGUI
from pyautogui2.utils.decorators.failsafe import FailsafeManager
from pyautogui2.utils.decorators.pause import PauseManager


class TestFailsafeProperty:
    """Tests for PyAutoGUI.FAILSAFE property."""

    def test_failsafe_getter_returns_manager_state(self, pyautogui_mocked):
        """FAILSAFE getter returns FailsafeManager.enabled state."""
        # Set via manager directly
        FailsafeManager().enabled = True
        assert pyautogui_mocked.FAILSAFE is True

        FailsafeManager().enabled = False
        assert pyautogui_mocked.FAILSAFE is False

    def test_failsafe_setter_updates_manager(self, pyautogui_mocked):
        """FAILSAFE setter updates FailsafeManager.enabled."""
        # Set via property
        pyautogui_mocked.FAILSAFE = False
        assert FailsafeManager().enabled is False

        pyautogui_mocked.FAILSAFE = True
        assert FailsafeManager().enabled is True

    def test_failsafe_roundtrip(self, pyautogui_mocked):
        """Setting FAILSAFE via property reflects in getter."""
        pyautogui_mocked.FAILSAFE = False
        assert pyautogui_mocked.FAILSAFE is False

        pyautogui_mocked.FAILSAFE = True
        assert pyautogui_mocked.FAILSAFE is True


class TestPauseProperty:
    """Tests for PyAutoGUI.PAUSE property."""

    def test_pause_getter_returns_manager_duration(self, pyautogui_mocked):
        """PAUSE getter returns PauseManager.controller_duration."""
        # Set via manager directly
        PauseManager().controller_duration = 0.5
        assert pyautogui_mocked.PAUSE == 0.5

        PauseManager().controller_duration = 1.0
        assert pyautogui_mocked.PAUSE == 1.0

    def test_pause_setter_updates_manager(self, pyautogui_mocked):
        """PAUSE setter updates PauseManager.controller_duration."""
        # Set via property
        pyautogui_mocked.PAUSE = 0.25
        assert PauseManager().controller_duration == 0.25

        pyautogui_mocked.PAUSE = 2.0
        assert PauseManager().controller_duration == 2.0

    def test_pause_roundtrip(self, pyautogui_mocked):
        """Setting PAUSE via property reflects in getter."""
        pyautogui_mocked.PAUSE = 0.75
        assert pyautogui_mocked.PAUSE == 0.75

        pyautogui_mocked.PAUSE = 0.0
        assert pyautogui_mocked.PAUSE == 0.0

    def test_pause_accepts_zero(self, pyautogui_mocked):
        """PAUSE property accepts zero (disable pause)."""
        pyautogui_mocked.PAUSE = 0.0
        assert pyautogui_mocked.PAUSE == 0.0
        assert PauseManager().controller_duration == 0.0

    def test_pause_accepts_float(self, pyautogui_mocked):
        """PAUSE property accepts arbitrary float values."""
        pyautogui_mocked.PAUSE = 3.14159
        assert pyautogui_mocked.PAUSE == 3.14159


class TestPropertyIndependence:
    """Tests that FAILSAFE and PAUSE properties are independent."""

    def test_failsafe_does_not_affect_pause(self, pyautogui_mocked):
        """Changing FAILSAFE does not affect PAUSE."""
        pyautogui_mocked.PAUSE = 0.5

        pyautogui_mocked.FAILSAFE = False
        assert pyautogui_mocked.PAUSE == 0.5

        pyautogui_mocked.FAILSAFE = True
        assert pyautogui_mocked.PAUSE == 0.5

    def test_pause_does_not_affect_failsafe(self, pyautogui_mocked):
        """Changing PAUSE does not affect FAILSAFE."""
        pyautogui_mocked.FAILSAFE = True

        pyautogui_mocked.PAUSE = 1.0
        assert pyautogui_mocked.FAILSAFE is True

        pyautogui_mocked.PAUSE = 0.0
        assert pyautogui_mocked.FAILSAFE is True


class TestManagerSingletonIntegration:
    """Tests that properties interact with singleton manager instances."""

    def test_multiple_instances_share_failsafe_state(self, osal_mocked):
        """Multiple PyAutoGUI instances share FailsafeManager state."""
        with patch("pyautogui2.controllers.get_osal", return_value=osal_mocked):
            instance1 = PyAutoGUI()
            instance2 = PyAutoGUI()

            instance1.FAILSAFE = False
            assert instance2.FAILSAFE is False

            instance2.FAILSAFE = True
            assert instance1.FAILSAFE is True

    def test_multiple_instances_share_pause_state(self, osal_mocked):
        """Multiple PyAutoGUI instances share PauseManager state."""
        with patch("pyautogui2.controllers.get_osal", return_value=osal_mocked):
            instance1 = PyAutoGUI()
            instance2 = PyAutoGUI()

            instance1.PAUSE = 0.3
            assert instance2.PAUSE == 0.3

            instance2.PAUSE = 0.7
            assert instance1.PAUSE == 0.7

    def test_property_reflects_external_manager_changes(self, osal_mocked):
        """Properties reflect changes made directly to managers."""
        with patch("pyautogui2.controllers.get_osal", return_value=osal_mocked):
            # Change via manager
            FailsafeManager().enabled = False
            PauseManager().controller_duration = 5.0

            # Verify via properties
            assert PyAutoGUI().FAILSAFE is False
            assert PyAutoGUI().PAUSE == 5.0
