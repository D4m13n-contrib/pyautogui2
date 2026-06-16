"""Controller manager."""

import atexit

from typing import Optional

from ..osal import get_osal
from ..utils.singleton import Singleton
from .dialogs import DialogsController
from .keyboard import KeyboardController
from .pointer import PointerController
from .screen import ScreenController


class ControllerManager(metaclass=Singleton):
    """Central manager that provides access to all individual controllers.

    This class is used by PyAutoGUI (POO entrypoint) and allows controllers
    to communicate with each other if needed.
    """

    def __init__(self,
                 pointer: Optional[PointerController] = None,
                 keyboard: Optional[KeyboardController] = None,
                 screen: Optional[ScreenController] = None,
                 dialogs: Optional[DialogsController] = None) -> None:

        # Branch explicitly so mypy understands _osal is never None when accessed
        if pointer and keyboard and screen and dialogs:
            self._pointer = pointer
            self._keyboard = keyboard
            self._screen = screen
            self._dialogs = dialogs
        else:
            _osal = get_osal()
            self._pointer = pointer or PointerController(osal=_osal.pointer)
            self._keyboard = keyboard or KeyboardController(osal=_osal.keyboard)
            self._screen = screen or ScreenController(osal=_osal.screen)
            self._dialogs = dialogs or DialogsController(osal=_osal.dialogs)

        setup_context = {
            "controller_manager": self,
        }

        # Setup each controller
        self._screen.setup_postinit(**setup_context)    # Screen First to permit to use get_size()
        self._pointer.setup_postinit(**setup_context)
        self._keyboard.setup_postinit(**setup_context)
        self._dialogs.setup_postinit(**setup_context)

        atexit.register(self.teardown)

    def teardown(self) -> None:
        """Tear down all controllers in reverse setup order.

        Calls teardown_postinit() on each controller in the reverse order of
        setup_postinit() calls, ensuring dependencies are released cleanly.
        Must be called before removing the ControllerManager singleton instance.
        """
        self._pointer.teardown_postinit()
        self._keyboard.teardown_postinit()
        self._screen.teardown_postinit()
        self._dialogs.teardown_postinit()

    @property
    def pointer(self) -> PointerController:
        return self._pointer

    @property
    def keyboard(self) -> KeyboardController:
        return self._keyboard

    @property
    def screen(self) -> ScreenController:
        return self._screen

    @property
    def dialogs(self) -> DialogsController:
        return self._dialogs

    def __repr__(self) -> str:
        return (
            f"<ControllerManager "
            f"pointer={self.pointer.__class__.__name__}, "
            f"keyboard={self.keyboard.__class__.__name__}, "
            f"screen={self.screen.__class__.__name__}, "
            f"dialogs={self.dialogs.__class__.__name__}>"
        )


__all__ = [
    "ControllerManager",
    "PointerController",
    "KeyboardController",
    "ScreenController",
    "DialogsController",
]
