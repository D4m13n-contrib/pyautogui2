"""Pytest fixtures for KeyboardController testing with mock OSALs."""
import pytest


@pytest.fixture
def keyboard_controller(controller_manager):
    """Provide isolated KeyboardController with mock OSAL.

    Creates a KeyboardController with MockKeyboardOSAL for testing keyboard
    operations in isolation.

    Returns:
        controller: KeyboardController instance

    Example:
        def test_keyboard_write(keyboard_controller):
            ctrl = keyboard_controller

            # Test write
            ctrl.write("Hello")

            # Verify OSAL calls
            ctrl._osal.mocks.assert_has_calls([
                call.key_down("h"),
                call.key_up("h"),
                call.key_down("e"),
                call.key_up("e"),
                # ... etc
            ])
    """
    return controller_manager.keyboard


__all__ = [
    "keyboard_controller",
]
