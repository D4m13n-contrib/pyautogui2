"""Pytest fixtures for DialogsController testing with mock OSALs."""
import pytest


@pytest.fixture
def dialogs_controller(controller_manager):
    """Provide isolated DialogsController with mock OSAL.

    Creates a DialogsController with MockDialogsOSAL for testing dialog
    operations in isolation.

    Returns:
        controller: DialogsController instance

    Example:
        def test_dialogs_alert(dialogs_controller):
            ctrl = dialogs_controller

            # Test alert
            result = ctrl.alert("Warning!")

            # Verify OSAL call
            ctrl._osal.alert.assert_called_once_with("Warning!", title=None)
            assert result == "Alert Ok"
    """
    return controller_manager.dialogs


__all__ = [
    "dialogs_controller",
]
