"""Controller manager."""
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

        # Call get_osal() only if not all controllers are given
        _osal = None if all([pointer, keyboard, screen, dialogs]) else get_osal()

        # Create each controller
        self._pointer: PointerController = pointer or PointerController(osal = _osal.pointer)        # type: ignore[union-attr]
        self._keyboard: KeyboardController = keyboard or KeyboardController(osal = _osal.keyboard)   # type: ignore[union-attr]
        self._screen: ScreenController = screen or ScreenController(osal = _osal.screen)             # type: ignore[union-attr]
        self._dialogs: DialogsController = dialogs or DialogsController(osal = _osal.dialogs)        # type: ignore[union-attr]

        setup_context = {
            "controller_manager": self,
        }

        # Setup each controller
        self._screen.setup_postinit(**setup_context)    # Screen First to permit to use get_size()
        self._pointer.setup_postinit(**setup_context)
        self._keyboard.setup_postinit(**setup_context)
        self._dialogs.setup_postinit(**setup_context)

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
