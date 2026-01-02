"""OSAL builder utilities for Linux tests."""

from contextlib import contextmanager
from itertools import chain
from typing import Any, Optional


@contextmanager
def clean_linux_osal_ctx(component: str, osal_cls_parts: list[type],
                         mocks: Optional[dict[str, Any]] = None, attr_mocks: Optional[dict[str, Any]] = None):
    """Create a Linux OSAL class with combining parts."""
    from pyautogui2.controllers.keyboard import KeyboardController as KC
    from pyautogui2.osal.linux import _compose_linux_class

    mocks = {} if mocks is None else mocks
    attr_mocks = {} if attr_mocks is None else attr_mocks

    osal_cls = _compose_linux_class(component, *osal_cls_parts)
    osal = osal_cls()

    for attr_name, mock in attr_mocks.items():
        setattr(osal, attr_name, mock)

    setup_kwargs = {
        "screen_size_max": (1920, 1080),
        "key_names": KC.KEY_NAMES,
        "all_keymapping": KC.KEYBOARD_MAPPINGS,
    }
    osal.setup_postinit(**setup_kwargs)

    osal._mocks = mocks

    # Reset setup_postinit() mock calls
    for mock in chain(osal._mocks.values(), attr_mocks.values()):
        if mock is not None:
            mock.reset_mock()

    try:
        yield osal
    finally:
        # Cleanup mocks
        for mock in chain(osal._mocks.values(), attr_mocks.values()):
            if mock is not None:
                mock.reset_mock()
