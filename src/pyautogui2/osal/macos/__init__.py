"""Top-level MacOS backend loader."""
from ..abstract_cls import OSAL
from .dialogs import MacOSDialogs
from .keyboard import MacOSKeyboard
from .pointer import MacOSPointer
from .screen import MacOSScreen


def get_osal() -> OSAL:
    """Build and return the fully assembled MacOS OSAL object.

    Returns:
        An OSAL instance containing the concrete MacOS classes for:
        - pointer
        - keyboard
        - screen
        - dialogs
    """
    return OSAL(
        pointer=MacOSPointer(),
        keyboard=MacOSKeyboard(),
        screen=MacOSScreen(),
        dialogs=MacOSDialogs(),
    )
