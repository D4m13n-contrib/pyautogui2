"""Tests for ControllerManager orchestration and lifecycle.

The ControllerManager is responsible for:
- Creating and initializing all controllers
- Ensuring each controller gets the appropriate OSAL implementation
- Providing unified access to all controllers
- Managing controller references and lifecycle

These tests verify the manager's orchestration logic using mock OSALs.
"""
from unittest.mock import patch

import pytest

from pyautogui2.controllers import ControllerManager
from pyautogui2.controllers.abstract_cls import (
    AbstractDialogsController,
    AbstractKeyboardController,
    AbstractPointerController,
    AbstractScreenController,
)


class TestControllerManagerInitialization:
    """Test controller manager initialization and setup."""

    def test_manager_initializes_all_controllers(self, controller_manager):
        """Test that manager creates all four controllers."""
        assert isinstance(controller_manager, ControllerManager)

        # Verify all controllers exist and are correct type
        assert isinstance(controller_manager.pointer, AbstractPointerController)
        assert isinstance(controller_manager.keyboard, AbstractKeyboardController)
        assert isinstance(controller_manager.screen, AbstractScreenController)
        assert isinstance(controller_manager.dialogs, AbstractDialogsController)

    def test_each_controller_has_its_osal(self, controller_manager):
        """Test that each controller has access to its OSAL implementation."""
        # Each controller should have its own OSAL
        assert controller_manager.pointer._osal is not None
        assert controller_manager.keyboard._osal is not None
        assert controller_manager.screen._osal is not None
        assert controller_manager.dialogs._osal is not None

    def test_controllers_have_different_osals(self, controller_manager):
        """Test that each controller has a different OSAL instance."""
        # Controllers manage different aspects, so different OSALs
        pointer_osal = controller_manager.pointer._osal
        keyboard_osal = controller_manager.keyboard._osal
        screen_osal = controller_manager.screen._osal
        dialogs_osal = controller_manager.dialogs._osal

        # All should be different objects
        osals = [pointer_osal, keyboard_osal, screen_osal, dialogs_osal]
        assert len(set(osals)) == 4, \
            "Each controller should have its own OSAL instance"

    def test_controller_references_are_stable(self, controller_manager):
        """Test that controller references don't change after creation."""
        # Get references
        pointer1 = controller_manager.pointer
        keyboard1 = controller_manager.keyboard
        screen1 = controller_manager.screen
        dialogs1 = controller_manager.dialogs

        # Get references again
        pointer2 = controller_manager.pointer
        keyboard2 = controller_manager.keyboard
        screen2 = controller_manager.screen
        dialogs2 = controller_manager.dialogs

        # Should be same objects
        assert pointer1 is pointer2
        assert keyboard1 is keyboard2
        assert screen1 is screen2
        assert dialogs1 is dialogs2


class TestControllerManagerRepresentation:
    """Test string representations of the manager."""

    def test_repr_contains_all_controller_names(self, controller_manager):
        """Test that __repr__ shows all controller types."""
        rep = repr(controller_manager)

        # Should mention all controllers
        assert "PointerController" in rep
        assert "KeyboardController" in rep
        assert "ScreenController" in rep
        assert "DialogsController" in rep

    def test_repr_format_is_valid_python_like(self, controller_manager):
        """Test that __repr__ looks like a constructor call."""
        rep = repr(controller_manager)

        # Should look like: <ControllerManager ...>
        assert rep.startswith("<ControllerManager ")
        assert rep.endswith(">")

    def test_str_is_user_friendly(self, controller_manager):
        """Test that __str__ provides user-friendly output."""
        string = str(controller_manager)

        # Should be readable (exact format depends on implementation)
        assert len(string) > 0
        assert "Controller" in string or "Manager" in string


class TestControllerManagerIntegration:
    """Test integration between controllers through the manager."""

    def test_controllers_can_operate_independently(self, controller_manager):
        """Test that controllers don't interfere with each other."""
        # Each controller should work independently

        # Pointer operation
        controller_manager.pointer.get_position()

        # Keyboard operation
        controller_manager.keyboard.key_down('a')

        # Screen operation
        controller_manager.screen.get_size()

        # Dialogs operation (would show dialog in real scenario)
        # controller_manager.dialogs.alert("test")  # Skip in unit test

        # All should work without errors

    def test_multiple_manager_instances_are_same(self, osal_mocked):
        """Test that multiple manager instances are same."""
        with patch("pyautogui2.controllers.get_osal", return_value=osal_mocked):
            manager1 = ControllerManager()
            manager2 = ControllerManager()

            # Should be different instances
            assert manager1 is manager2

            # Controllers should also be different
            assert manager1.pointer is manager2.pointer
            assert manager1.keyboard is manager2.keyboard
            assert manager1.screen is manager2.screen
            assert manager1.dialogs is manager2.dialogs


class TestControllerManagerAttributes:
    """Test manager attributes and properties."""

    def test_manager_has_all_expected_attributes(self, controller_manager):
        """Test that manager exposes all expected controller attributes."""
        # Should have all four controllers as attributes
        assert hasattr(controller_manager, 'pointer')
        assert hasattr(controller_manager, 'keyboard')
        assert hasattr(controller_manager, 'screen')
        assert hasattr(controller_manager, 'dialogs')

    def test_manager_controllers_are_not_none(self, controller_manager):
        """Test that no controller is None after initialization."""
        assert controller_manager.pointer is not None
        assert controller_manager.keyboard is not None
        assert controller_manager.screen is not None
        assert controller_manager.dialogs is not None

    def test_manager_controllers_are_readonly_like(self, controller_manager):
        """Test that controller references shouldn't be easily overwritten."""
        with pytest.raises(AttributeError):
            controller_manager.pointer = "fake"
        assert controller_manager.pointer != "fake"

        with pytest.raises(AttributeError):
            controller_manager.keyboard = "fake"
        assert controller_manager.keyboard != "fake"

        with pytest.raises(AttributeError):
            controller_manager.screen = "fake"
        assert controller_manager.screen != "fake"

        with pytest.raises(AttributeError):
            controller_manager.dialogs = "fake"
        assert controller_manager.dialogs != "fake"
