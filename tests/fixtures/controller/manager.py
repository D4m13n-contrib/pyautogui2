"""Pytest fixtures for ControllerManager testing with mock OSALs."""

import pytest


@pytest.fixture
def controller_manager():
    """Provide a complete ControllerManager with all mock OSALs.

    This fixture creates a fully functional ControllerManager where all
    OSAL implementations are mocked. Useful for integration tests that
    need multiple controllers interacting (e.g., pointer using screen size).

    All mocks are reset after manager initialization to clear any
    setup_postinit() calls, so tests start with clean call history.

    Returns:
        manager: ControllerManager instance

    Example:
        def test_manager_integration(controller_manager):
            manager = controller_manager["manager"]

            # Use controllers
            manager.pointer.move_to(100, 200)
            manager.keyboard.write("Hello")

            # Verify calls on underlying mocks
            manager.pointer._osal.move_to.assert_called_once_with(100, 200)
            manager.keyboard._osal.mocks.assert_has_calls([
                call.key_down("h"),
                call.key_up("h"),
                # ... etc
            ])

    Note:
        The manager is recreated for each test function, ensuring complete
        isolation between tests.
    """
    from pyautogui2.controllers import ControllerManager
    from pyautogui2.controllers.dialogs import DialogsController
    from pyautogui2.controllers.keyboard import KeyboardController
    from pyautogui2.controllers.pointer import PointerController
    from pyautogui2.controllers.screen import ScreenController
    from tests.mocks.osal.generic.mock_dialogs_osal import MockDialogsOSAL
    from tests.mocks.osal.generic.mock_keyboard_osal import MockKeyboardOSAL
    from tests.mocks.osal.generic.mock_pointer_osal import MockPointerOSAL
    from tests.mocks.osal.generic.mock_screen_osal import MockScreenOSAL

    # Create Controllers with mocked OSALs
    mock_pointer = PointerController(osal=MockPointerOSAL())
    mock_keyboard = KeyboardController(osal=MockKeyboardOSAL())
    mock_screen = ScreenController(osal=MockScreenOSAL())
    mock_dialogs = DialogsController(osal=MockDialogsOSAL())

    # Create manager with mocked Controllers
    manager = ControllerManager(
        pointer=mock_pointer,
        keyboard=mock_keyboard,
        screen=mock_screen,
        dialogs=mock_dialogs,
    )

    # Reset all mocks to clear setup_postinit() calls
    manager.pointer._osal.reset_mocks()
    manager.keyboard._osal.reset_mocks()
    manager.screen._osal.reset_mocks()
    manager.dialogs._osal.reset_mocks()

    try:
        yield manager
    finally:
        pass


__all__ = [
    "controller_manager",
]
