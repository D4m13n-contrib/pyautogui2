"""Tests for FailsafeManager and failsafe_decorator."""

from unittest.mock import MagicMock, patch

import pytest

from pyautogui2.utils.decorators.failsafe import (
    FailSafeException,
    FailsafeManager,
    failsafe_decorator,
)


class TestFailsafeManagerInit:
    """Test FailsafeManager initialization and singleton behavior."""

    def test_singleton_same_instance(self, failsafe_manager_mocked):
        """Multiple calls return same instance."""
        manager1 = failsafe_manager_mocked
        manager2 = FailsafeManager()

        assert manager1 is manager2

    def test_singleton_id_equality(self, failsafe_manager_mocked):
        """Instances have same id."""
        manager1 = failsafe_manager_mocked
        manager2 = FailsafeManager()

        assert id(manager1) == id(manager2)

    def test_default_state(self, failsafe_manager_real):
        """Manager initializes with default state."""
        assert failsafe_manager_real._enabled is None  # Not initialized yet
        assert failsafe_manager_real.trigger_points == [(0, 0)]
        assert failsafe_manager_real._get_position is None


class TestEnabledProperty:
    """Test enabled property getter/setter."""

    def test_get_enabled_before_init(self, failsafe_manager_mocked, isolated_settings):
        """Enabled returns settings value before initialization."""
        with patch.object(isolated_settings, 'FAILSAFE', True):
            assert failsafe_manager_mocked.enabled is True

        with patch.object(isolated_settings, 'FAILSAFE', False):
            assert failsafe_manager_mocked.enabled is False

    def test_get_enabled_after_set(self, failsafe_manager_mocked):
        """Enabled returns set value after initialization."""
        failsafe_manager_mocked.enabled = True
        assert failsafe_manager_mocked.enabled is True

        failsafe_manager_mocked.enabled = False
        assert failsafe_manager_mocked.enabled is False

    def test_set_enabled_with_bool(self, failsafe_manager_mocked):
        """Can set enabled with boolean values."""
        failsafe_manager_mocked.enabled = True
        assert failsafe_manager_mocked._enabled is True

        failsafe_manager_mocked.enabled = False
        assert failsafe_manager_mocked._enabled is False

    def test_set_enabled_type_validation(self, failsafe_manager_mocked):
        """Setting enabled with non-bool raises TypeError."""
        with pytest.raises(TypeError, match="Enabled must be boolean"):
            failsafe_manager_mocked.enabled = "true"

        with pytest.raises(TypeError, match="Enabled must be boolean"):
            failsafe_manager_mocked.enabled = 1

        with pytest.raises(TypeError, match="Enabled must be boolean"):
            failsafe_manager_mocked.enabled = None


class TestTriggerPoints:
    """Test trigger point management."""

    def test_default_trigger_point(self, failsafe_manager_mocked):
        """Default trigger point is (0, 0)."""
        assert failsafe_manager_mocked.trigger_points == [(0, 0)]

    def test_add_trigger_point(self, failsafe_manager_mocked):
        """Can add new trigger points."""
        failsafe_manager_mocked.add_trigger_point((1919, 0))

        assert (0, 0) in failsafe_manager_mocked.trigger_points
        assert (1919, 0) in failsafe_manager_mocked.trigger_points
        assert len(failsafe_manager_mocked.trigger_points) == 2

    def test_add_trigger_point_duplicate(self, failsafe_manager_mocked):
        """Adding duplicate trigger point is ignored."""
        failsafe_manager_mocked.add_trigger_point((100, 100))
        failsafe_manager_mocked.add_trigger_point((100, 100))

        assert failsafe_manager_mocked.trigger_points.count((100, 100)) == 1

    def test_add_multiple_trigger_points(self, failsafe_manager_mocked):
        """Can add multiple distinct trigger points."""
        failsafe_manager_mocked.add_trigger_point((1919, 0))      # Top-right
        failsafe_manager_mocked.add_trigger_point((1919, 1079))   # Bottom-right
        failsafe_manager_mocked.add_trigger_point((0, 1079))      # Bottom-left

        assert len(failsafe_manager_mocked.trigger_points) == 4  # Including default (0, 0)

    def test_reset_trigger_points(self, failsafe_manager_mocked):
        """Reset removes custom points and restores default."""
        failsafe_manager_mocked.add_trigger_point((100, 100))
        failsafe_manager_mocked.add_trigger_point((200, 200))
        assert len(failsafe_manager_mocked.trigger_points) == 3

        failsafe_manager_mocked.reset_to_defaults()

        assert failsafe_manager_mocked.trigger_points == [(0, 0)]
        assert failsafe_manager_mocked._enabled is None
        assert failsafe_manager_mocked._get_position is None


class TestPositionGetter:
    """Test position getter registration and usage."""

    def test_register_get_position_replaces_previous(self, failsafe_manager_mocked):
        """Registering new getter replaces previous one."""
        getter1 = MagicMock()
        getter2 = MagicMock()

        failsafe_manager_mocked.register_get_position(getter1)
        assert failsafe_manager_mocked._get_position is getter1

        failsafe_manager_mocked.register_get_position(getter2)
        assert failsafe_manager_mocked._get_position is getter2


class TestCheckMethod:
    """Test position checking and exception raising."""

    def test_check_disabled_does_nothing(self, failsafe_manager_mocked):
        """Check does nothing when disabled."""
        failsafe_manager_mocked.enabled = False
        failsafe_manager_mocked._mocks["get_pos"].return_value = (0, 0)  # Trigger point

        # Should not raise
        failsafe_manager_mocked.check()

        # Should not even call get_position
        failsafe_manager_mocked._mocks["get_pos"].assert_not_called()

    def test_check_enabled_no_position_getter(self, failsafe_manager_mocked):
        """Check does nothing when no position getter registered."""
        failsafe_manager_mocked.enabled = True
        # Don't register position getter
        failsafe_manager_mocked._get_position = None

        # Should not raise
        failsafe_manager_mocked.check()

    def test_check_safe_position(self, failsafe_manager_mocked):
        """Check passes when position is safe."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (500, 500)  # Safe position

        # Should not raise
        failsafe_manager_mocked.check()

        failsafe_manager_mocked._mocks["get_pos"].assert_called_once()

    def test_check_trigger_position_raises(self, failsafe_manager_mocked):
        """Check raises FailSafeException at trigger point."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (0, 0)  # Trigger point

        with pytest.raises(FailSafeException, match="Fail-safe triggered"):
            failsafe_manager_mocked.check()

    def test_check_multiple_trigger_points(self, failsafe_manager_mocked):
        """Check detects all registered trigger points."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked.add_trigger_point((1919, 0))

        # Test default trigger
        failsafe_manager_mocked._mocks["get_pos"].return_value = (0, 0)
        with pytest.raises(FailSafeException):
            failsafe_manager_mocked.check()

        # Test custom trigger
        failsafe_manager_mocked._mocks["get_pos"].return_value = (1919, 0)
        with pytest.raises(FailSafeException):
            failsafe_manager_mocked.check()

    def test_check_position_getter_exception(self, failsafe_manager_mocked):
        """Check handles exception from position getter."""
        failsafe_manager_mocked.enabled = True

        failing_getter = MagicMock(side_effect=Exception("Hardware error"))
        failsafe_manager_mocked.register_get_position(failing_getter)

        with pytest.raises(Exception, match="Hardware error"):
            failsafe_manager_mocked.check()

        failing_getter.assert_called_once()


class TestFailsafeDecorator:
    """Test @failsafe_decorator behavior."""

    def test_decorator_calls_check_before_function(self, failsafe_manager_mocked):
        """Decorator calls failsafe_manager_mocked.check() before executing function."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (100, 100)  # Safe

        call_order = []

        @failsafe_decorator
        def test_func():
            call_order.append("func")
            return "result"

        # Patch check to track call order
        original_check = failsafe_manager_mocked.check
        def tracked_check():
            call_order.append("check")
            original_check()

        with patch.object(failsafe_manager_mocked, 'check', tracked_check):
            result = test_func()

        assert call_order == ["check", "func"]
        assert result == "result"

    def test_decorator_on_method(self, failsafe_manager_mocked):
        """Decorator works on instance methods."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (100, 100)

        class TestClass:
            @failsafe_decorator
            def method(self):
                return "method_result"

        obj = TestClass()
        result = obj.method()

        assert result == "method_result"
        failsafe_manager_mocked._mocks["get_pos"].assert_called()

    def test_decorator_on_function_without_self(self, failsafe_manager_mocked):
        """Decorator works on standalone functions."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (100, 100)

        @failsafe_decorator
        def standalone_func(a, b):
            return a + b

        result = standalone_func(5, 3)

        assert result == 8
        failsafe_manager_mocked._mocks["get_pos"].assert_called()

    def test_decorator_propagates_exception(self, failsafe_manager_mocked):
        """Decorator propagates FailSafeException from check()."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (0, 0)  # Trigger

        @failsafe_decorator
        def test_func():
            return "should_not_reach"

        with pytest.raises(FailSafeException):
            test_func()

    def test_decorator_preserves_function_metadata(self):
        """Decorator preserves original function metadata."""
        @failsafe_decorator
        def documented_func():
            """Original docstring."""
            pass

        assert documented_func.__name__ == "documented_func"
        assert documented_func.__doc__ == "Original docstring."

    def test_decorator_handles_args_and_kwargs(self, failsafe_manager_mocked):
        """Decorator correctly passes through args and kwargs."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (100, 100)

        @failsafe_decorator
        def func_with_params(a, b, c=10, d=20):
            return a + b + c + d

        result = func_with_params(1, 2, c=3, d=4)

        assert result == 10  # 1+2+3+4


class TestIntegrationScenarios:
    """Test realistic usage scenarios."""

    def test_typical_usage_flow(self, failsafe_manager_mocked):
        """Test typical setup and usage pattern."""
        # Setup
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked.add_trigger_point((1919, 1079))  # Bottom-right corner

        # Safe operations
        failsafe_manager_mocked._mocks["get_pos"].return_value = (960, 540)  # Center

        @failsafe_decorator
        def automation_step():
            return "step_complete"

        assert automation_step() == "step_complete"

        # Trigger failsafe
        failsafe_manager_mocked._mocks["get_pos"].return_value = (1919, 1079)

        with pytest.raises(FailSafeException):
            automation_step()

    def test_disable_during_operation(self, failsafe_manager_mocked):
        """Can disable failsafe mid-operation."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (0, 0)  # Would trigger

        @failsafe_decorator
        def risky_operation():
            return "done"

        # Would raise
        with pytest.raises(FailSafeException):
            risky_operation()

        # Disable and retry
        failsafe_manager_mocked.enabled = False
        result = risky_operation()

        assert result == "done"

    def test_reset_clears_custom_configuration(self, failsafe_manager_mocked):
        """Reset clears all custom configuration."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked.add_trigger_point((100, 100))
        failsafe_manager_mocked.add_trigger_point((200, 200))

        failsafe_manager_mocked.reset_to_defaults()

        assert failsafe_manager_mocked.trigger_points == [(0, 0)]
        assert failsafe_manager_mocked._enabled is None
        assert failsafe_manager_mocked._get_position is None


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_check_with_none_position(self, failsafe_manager_mocked):
        """Check handles None from position getter."""
        failsafe_manager_mocked.enabled = True

        none_getter = MagicMock(return_value=None)
        failsafe_manager_mocked.register_get_position(none_getter)

        # Should not raise (can't check None position)
        failsafe_manager_mocked.check()

        none_getter.assert_called_once()

    def test_check_with_partial_position(self, failsafe_manager_mocked):
        """Check handles incomplete position tuples."""
        failsafe_manager_mocked.enabled = True

        # Missing y coordinate
        partial_getter = MagicMock(return_value=(100,))
        failsafe_manager_mocked.register_get_position(partial_getter)

        # Should not crash
        failsafe_manager_mocked.check()

    def test_multiple_decorators_on_same_function(self, failsafe_manager_mocked):
        """Multiple decorated functions share same failsafe_manager_mocked."""
        failsafe_manager_mocked.enabled = True
        failsafe_manager_mocked._mocks["get_pos"].return_value = (100, 100)

        @failsafe_decorator
        def func1():
            return "func1"

        @failsafe_decorator
        def func2():
            return "func2"

        assert func1() == "func1"
        assert func2() == "func2"

        # Both should trigger failsafe
        failsafe_manager_mocked._mocks["get_pos"].return_value = (0, 0)

        with pytest.raises(FailSafeException):
            func1()

        with pytest.raises(FailSafeException):
            func2()
