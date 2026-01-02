"""Tests for PauseManager and pause_decorator."""

import pytest

from pyautogui2.utils.decorators.pause import PauseManager, pause_decorator


class TestPauseManagerInit:
    """Test PauseManager initialization and singleton behavior."""

    def test_singleton_same_instance(self, pause_manager_mocked):
        """Multiple calls return same instance."""
        manager1 = pause_manager_mocked
        manager2 = PauseManager()

        assert manager1 is manager2

    def test_singleton_id_equality(self, pause_manager_mocked):
        """Instances have same id."""
        manager1 = pause_manager_mocked
        manager2 = PauseManager()

        assert id(manager1) == id(manager2)

    def test_default_values(self, pause_manager_real, isolated_settings):
        """Manager initializes with settings defaults."""
        assert pause_manager_real.controller_duration == isolated_settings.PAUSE_CONTROLLER_DURATION
        assert pause_manager_real.osal_duration == isolated_settings.PAUSE_OSAL_DURATION
        assert pause_manager_real.debug == isolated_settings.PAUSE_DEBUG


class TestControllerDuration:
    """Test controller_duration property validation."""

    def test_get_controller_duration(self, pause_manager_mocked):
        """Getter returns current value."""
        assert isinstance(pause_manager_mocked.controller_duration, float)

    def test_set_controller_duration_valid_float(self, pause_manager_mocked):
        """Can set float value."""
        pause_manager_mocked.controller_duration = 1.5
        assert pause_manager_mocked.controller_duration == 1.5

    def test_set_controller_duration_valid_int(self, pause_manager_mocked):
        """Can set int value (converted to float)."""
        pause_manager_mocked.controller_duration = 2
        assert pause_manager_mocked.controller_duration == 2.0
        assert isinstance(pause_manager_mocked.controller_duration, float)

    def test_set_controller_duration_zero(self, pause_manager_mocked):
        """Can set zero value."""
        pause_manager_mocked.controller_duration = 0
        assert pause_manager_mocked.controller_duration == 0.0

    def test_set_controller_duration_invalid_type(self, pause_manager_mocked):
        """Raises TypeError for non-numeric value."""
        with pytest.raises(TypeError, match="Duration must be numeric, got str"):
            pause_manager_mocked.controller_duration = "invalid"

    def test_set_controller_duration_negative(self, pause_manager_mocked):
        """Raises ValueError for negative value."""
        with pytest.raises(ValueError, match="Duration must be >= 0, got -1"):
            pause_manager_mocked.controller_duration = -1


class TestOsalDuration:
    """Test osal_duration property validation."""

    def test_get_osal_duration(self, pause_manager_mocked):
        """Getter returns current value."""
        assert isinstance(pause_manager_mocked.osal_duration, float)

    def test_set_osal_duration_valid_float(self, pause_manager_mocked):
        """Can set float value."""
        pause_manager_mocked.osal_duration = 0.5
        assert pause_manager_mocked.osal_duration == 0.5

    def test_set_osal_duration_valid_int(self, pause_manager_mocked):
        """Can set int value (converted to float)."""
        pause_manager_mocked.osal_duration = 3
        assert pause_manager_mocked.osal_duration == 3.0
        assert isinstance(pause_manager_mocked.osal_duration, float)

    def test_set_osal_duration_zero(self, pause_manager_mocked):
        """Can set zero value."""
        pause_manager_mocked.osal_duration = 0
        assert pause_manager_mocked.osal_duration == 0.0

    def test_set_osal_duration_invalid_type(self, pause_manager_mocked):
        """Raises TypeError for non-numeric value."""
        with pytest.raises(TypeError, match="Duration must be numeric, got list"):
            pause_manager_mocked.osal_duration = []

    def test_set_osal_duration_negative(self, pause_manager_mocked):
        """Raises ValueError for negative value."""
        with pytest.raises(ValueError, match="Duration must be >= 0, got -0.5"):
            pause_manager_mocked.osal_duration = -0.5


class TestDebugProperty:
    """Test debug property validation."""

    def test_get_debug(self, pause_manager_mocked):
        """Getter returns current value."""
        assert isinstance(pause_manager_mocked.debug, bool)

    def test_set_debug_true(self, pause_manager_mocked):
        """Can set to True."""
        pause_manager_mocked.debug = True
        assert pause_manager_mocked.debug is True

    def test_set_debug_false(self, pause_manager_mocked):
        """Can set to False."""
        pause_manager_mocked.debug = False
        assert pause_manager_mocked.debug is False

    def test_set_debug_invalid_type(self, pause_manager_mocked):
        """Raises TypeError for non-boolean value."""
        with pytest.raises(TypeError, match="Debug must be boolean, got int"):
            pause_manager_mocked.debug = 1

        with pytest.raises(TypeError, match="Debug must be boolean, got str"):
            pause_manager_mocked.debug = "true"


class TestPauseManagerMethods:
    """Test PauseManager utility methods."""

    def test_reset_to_defaults(self, pause_manager_mocked, isolated_settings):
        """reset_to_defaults restores settings values."""
        # Modify values
        pause_manager_mocked.controller_duration = 999.0
        pause_manager_mocked.osal_duration = 888.0
        pause_manager_mocked.debug = not isolated_settings.PAUSE_DEBUG

        # Reset
        pause_manager_mocked.reset_to_defaults()

        # Check restored
        assert pause_manager_mocked.controller_duration == isolated_settings.PAUSE_CONTROLLER_DURATION
        assert pause_manager_mocked.osal_duration == isolated_settings.PAUSE_OSAL_DURATION
        assert pause_manager_mocked.debug == isolated_settings.PAUSE_DEBUG

    def test_disable_all(self, pause_manager_mocked):
        """disable_all sets durations to zero."""
        pause_manager_mocked.controller_duration = 1.0
        pause_manager_mocked.osal_duration = 2.0

        pause_manager_mocked.disable_all()

        assert pause_manager_mocked.controller_duration == 0.0
        assert pause_manager_mocked.osal_duration == 0.0


class TestPauseDecoratorBasic:
    """Test pause_decorator basic behavior."""

    def test_decorator_without_pause(self, pause_manager_mocked):
        """Function executes without pause when _pause=False."""
        pause_manager_mocked.controller_duration = 1.0

        @pause_decorator
        def dummy_func(*_a, **_kw):
            return "result"

        result = dummy_func(_pause=False)

        assert result == "result"
        pause_manager_mocked._mocks["time_sleep"].assert_not_called()

    def test_decorator_with_custom_pause(self, pause_manager_mocked):
        """Function uses custom _pause duration."""
        @pause_decorator
        def dummy_func(*_a, **_kw):
            return "result"

        result = dummy_func(_pause=0.5)

        assert result == "result"
        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(0.5)

    def test_decorator_with_zero_pause(self, pause_manager_mocked):
        """_pause=0 or _pause=0.0 disables pause."""
        @pause_decorator
        def dummy_func(*_a, **_kw):
            return "result"

        # Test with int 0
        dummy_func(_pause=0)
        pause_manager_mocked._mocks["time_sleep"].assert_not_called()

        # Test with float 0.0
        dummy_func(_pause=0.0)
        pause_manager_mocked._mocks["time_sleep"].assert_not_called()


class TestPauseDecoratorWithOSAL:
    """Test pause_decorator with AbstractOSAL classes."""

    def test_osal_uses_osal_duration(self, pause_manager_mocked):
        """AbstractOSAL subclass uses osal_duration."""
        from pyautogui2.utils.abstract_cls import AbstractOSAL

        pause_manager_mocked.osal_duration = 0.3
        pause_manager_mocked.controller_duration = 9.9  # Should NOT be used

        class DummyOSAL(AbstractOSAL):
            @pause_decorator
            def action(self):
                return "osal_result"

        osal = DummyOSAL()
        result = osal.action()  # _pause=True by default

        assert result == "osal_result"
        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(0.3)

    def test_osal_respects_custom_pause(self, pause_manager_mocked):
        """AbstractOSAL can override with custom _pause."""
        from pyautogui2.utils.abstract_cls import AbstractOSAL

        pause_manager_mocked.osal_duration = 0.3

        class DummyOSAL(AbstractOSAL):
            @pause_decorator
            def action(self, *_a, **_kw):
                return "result"

        osal = DummyOSAL()
        osal.action(_pause=1.5)

        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(1.5)


class TestPauseDecoratorWithController:
    """Test pause_decorator with AbstractController classes."""

    def test_controller_uses_controller_duration(self, pause_manager_mocked):
        """AbstractController subclass uses controller_duration."""
        from pyautogui2.utils.abstract_cls import AbstractController

        pause_manager_mocked.controller_duration = 0.7
        pause_manager_mocked.osal_duration = 9.9  # Should NOT be used

        class DummyController(AbstractController):
            @pause_decorator
            def action(self, *_a, **_kw):
                return "controller_result"

        controller = DummyController()
        result = controller.action()  # _pause=True by default

        assert result == "controller_result"
        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(0.7)

    def test_controller_respects_custom_pause(self, pause_manager_mocked):
        """AbstractController can override with custom _pause."""
        from pyautogui2.utils.abstract_cls import AbstractController

        pause_manager_mocked.controller_duration = 0.7

        class DummyController(AbstractController):
            @pause_decorator
            def action(self, *_a, **_kw):
                return "result"

        controller = DummyController()
        controller.action(_pause=2.5)

        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(2.5)


class TestPauseDecoratorDebug:
    """Test pause_decorator debug output."""

    def test_debug_mode_prints_info(self, pause_manager_mocked, capsys):
        """Debug mode prints pause information."""
        pause_manager_mocked.debug = True
        pause_manager_mocked.controller_duration = 0.1

        from pyautogui2.utils.abstract_cls import AbstractController

        class DummyController(AbstractController):
            @pause_decorator
            def action(self, *_a, **_kw):
                return "result"

        controller = DummyController()
        controller.action()

        captured = capsys.readouterr()
        assert "[PAUSE]" in captured.out
        assert "action" in captured.out
        assert "_pause=True" in captured.out
        assert "0.1s" in captured.out

    def test_debug_mode_disabled_no_print(self, pause_manager_mocked, capsys):
        """Debug mode off produces no output."""
        pause_manager_mocked.debug = False
        pause_manager_mocked.controller_duration = 0.1

        from pyautogui2.utils.abstract_cls import AbstractController

        class DummyController(AbstractController):
            @pause_decorator
            def action(self, *_a, **_kw):
                return "result"

        controller = DummyController()
        controller.action()

        captured = capsys.readouterr()
        assert captured.out == ""


class TestPauseDecoratorEdgeCases:
    """Test pause_decorator edge cases."""

    def test_function_without_self_arg(self, pause_manager_mocked):
        """Standalone function (no args[0]) doesn't crash."""
        pause_manager_mocked.controller_duration = 0.2

        @pause_decorator
        def standalone(*_a, **_kw):
            return "standalone"

        # Should not crash, but won't detect class type
        # So no pause applied (no cls detected)
        result = standalone()

        assert result == "standalone"
        # No class detected, so no duration applied
        pause_manager_mocked._mocks["time_sleep"].assert_not_called()

    def test_pause_true_as_bool(self, pause_manager_mocked):
        """_pause=True (explicit bool) uses class-based duration."""
        from pyautogui2.utils.abstract_cls import AbstractController

        pause_manager_mocked.controller_duration = 0.4

        class DummyController(AbstractController):
            @pause_decorator
            def action(self, *_a, **_kw):
                return "result"

        controller = DummyController()
        controller.action(_pause=True)  # Explicit True

        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(0.4)

    def test_pause_with_other_kwargs(self, pause_manager_mocked):
        """_pause works alongside other kwargs."""
        @pause_decorator
        def func_with_kwargs(a, b=10, *_a, **_kw):
            return a + b

        result = func_with_kwargs(5, b=15, _pause=0.1)

        assert result == 20
        pause_manager_mocked._mocks["time_sleep"].assert_called_once_with(0.1)

    def test_pause_unknown_class_duration_stays_zero(self, pause_manager_mocked):
        """Cover cls is neither AbstractOSAL nor AbstractController.

        When the decorated method belongs to an unrelated class, neither branch
        is taken and duration stays 0.0, no sleep is called.
        """
        pause_manager_mocked.osal_duration = 0.5
        pause_manager_mocked.controller_duration = 0.5

        class UnrelatedClass:
            @pause_decorator
            def action(self, **kwargs):
                return "result"

        obj = UnrelatedClass()
        result = obj.action()

        assert result == "result"
        pause_manager_mocked._mocks["time_sleep"].assert_not_called()
