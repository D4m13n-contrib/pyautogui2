"""Pytest fixtures for PointerController testing with mock OSALs."""
import pytest


@pytest.fixture
def pointer_controller(controller_manager):
    """Provide isolated PointerController with mock OSAL.

    Creates a PointerController with MockPointerOSAL for testing pointer
    operations in isolation.

    Returns:
        controller: PointerController instance

    Example:
        def test_pointer_move_to(pointer_controller):
            ctrl = pointer_controller

            # Test move
            ctrl.move_to(100, 200)

            # Verify OSAL call
            ctrl._osal.move_to.assert_called_once_with(100, 200)

            # Verify state updated
            assert ctrl.get_pos() == Point(100, 200)

    Note:
        Mocks are reset after fixture setup, so call counts start at zero
        for each test.
    """
    return controller_manager.pointer


__all__ = [
    "pointer_controller",
]
