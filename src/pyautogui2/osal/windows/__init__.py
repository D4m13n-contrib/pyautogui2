"""Top-level Windows backend loader.
"""
from ..abstract_cls import OSAL
from .dialogs import WindowsDialogs
from .keyboard import WindowsKeyboard
from .pointer import WindowsPointer
from .screen import WindowsScreen


def get_osal() -> OSAL:
    """Build and return the fully assembled Windows OSAL object.

    Returns:
        An OSAL instance containing the concrete Windows classes for:
        - pointer
        - keyboard
        - screen
        - dialogs
    """
    return OSAL(
        pointer=WindowsPointer(),
        keyboard=WindowsKeyboard(),
        screen=WindowsScreen(),
        dialogs=WindowsDialogs(),
    )
