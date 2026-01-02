"""Pytest fixtures for ScreenController testing with mock OSALs."""
import pytest


@pytest.fixture
def screen_controller(controller_manager):
    """Provide isolated ScreenController with mock OSAL.

    Creates a ScreenController with MockScreenOSAL for testing screen
    operations in isolation.

    Returns:
        controller: ScreenController instance

    Example:
        def test_screen_get_size(screen_controller):
            ctrl = screen_controller

            # Test get size
            size = ctrl.get_size()

            # Verify OSAL call
            ctrl._osal.get_size.assert_called_once()
            assert size == (1920, 1080)
    """
    return controller_manager.screen


__all__ = [
    "screen_controller"
]
