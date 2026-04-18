"""LinuxParts mocks for tests."""
from collections.abc import Generator
from typing import Any, Optional
from unittest.mock import MagicMock

from pyautogui2.osal.abstract_cls import (
    AbstractDialogs,
    AbstractKeyboard,
    AbstractPointer,
    AbstractScreen,
)
from pyautogui2.utils.types import ButtonName, Point, Size

from ..generic.base import MockOSALBase


# ============================================================================
# Pointer Parts
# ============================================================================

class MockBasePointerPart(AbstractPointer, MockOSALBase):
    BACKEND_ID = "MockBasePointerPart"

    def mouse_info(self) -> None: pass
    def drag_to(self, x: int, y: int, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "mouse_info": {},
            "drag_to": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockDEPointerPart(AbstractPointer, MockOSALBase):
    BACKEND_ID = "MockDEPointerPart"

    def get_primary_button(self) -> ButtonName: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "get_primary_button": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockDSPointerPart(AbstractPointer, MockOSALBase):
    BACKEND_ID = "MockDSPointerPart"

    def get_pos(self) -> Point: pass
    def move_to(self, x: int, y: int, **_kwargs: Any) -> None: pass
    def button_down(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None: pass
    def button_up(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None: pass
    def scroll(self, dx: Optional[int] = None, dy: Optional[int] = None, **_kwargs: Any) -> None: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "get_pos": {},
            "move_to": {},
            "button_down": {},
            "button_up": {},
            "scroll": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockWaylandCompositorPointerPart(AbstractPointer, MockOSALBase):
    BACKEND_ID = "MockWaylandCompositorPointerPart"

    def get_pos(self) -> Point: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "get_pos": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


# ============================================================================
# Keyboard Parts
# ============================================================================

class MockBaseKeyboardPart(AbstractKeyboard, MockOSALBase):
    BACKEND_ID = "MockBaseKeyboardPart"

    def type_codepoint_value(self, hexstr: str) -> None: pass
    def codepoint_ctx(self) -> Generator["AbstractKeyboard.AbstractCodepointCtx", None, None]: pass

    def __init__(self):
        super().__init__()

        _mock_type_codepoint_value = MagicMock()
        # Wrap all methods with MagicMock for call tracking
        methods = {
            "codepoint_ctx": {},
            "type_codepoint_value": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockDEKeyboardPart(AbstractKeyboard, MockOSALBase):
    BACKEND_ID = "MockDEKeyboardPart"


class MockDSKeyboardPart(AbstractKeyboard, MockOSALBase):
    BACKEND_ID = "MockDSKeyboardPart"

    def key_is_mapped(self, key: str) -> bool: pass
    def key_down(self, key: str, **_kwargs) -> None: pass
    def key_up(self, key: str, **_kwargs) -> None: pass
    def get_layout(self) -> str: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "key_is_mapped": {},
            "key_down": {},
            "key_up": {},
            "get_layout": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockWaylandCompositorKeyboardPart(AbstractKeyboard, MockOSALBase):
    BACKEND_ID = "MockWaylandCompositorKeyboardPart"

    def get_layout(self) -> str: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "get_layout": {"return_value":"QWERTY"},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


# ============================================================================
# Screen Parts
# ============================================================================

class MockBaseScreenPart(AbstractScreen, MockOSALBase):
    BACKEND_ID = "MockBaseScreenPart"

    def locate(self, *args, **kwargs): pass
    def locate_all(self, *args, **kwargs): pass
    def locate_all_on_screen(self, *args, **kwargs): pass
    def locate_center_on_screen(self, *args, **kwargs): pass
    def locate_on_screen(self, *args, **kwargs): pass
    def locate_on_window(self, *args, **kwargs): pass
    def center(self, *args, **kwargs): pass
    def pixel(self, *args, **kwargs): pass
    def pixel_matches_color(self, *args, **kwargs): pass
    def screenshot(self, *args, **kwargs): pass
    def window(self, *args, **kwargs): pass
    def get_active_window(self, *args, **kwargs): pass
    def get_active_window_title(self, *args, **kwargs): pass
    def get_windows_at(self, *args, **kwargs): pass
    def get_windows_with_title(self, *args, **kwargs): pass
    def get_all_windows(self, *args, **kwargs): pass
    def get_all_titles(self, *args, **kwargs): pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "locate": {},
            "locate_all": {},
            "locate_all_on_screen": {},
            "locate_center_on_screen": {},
            "locate_on_screen": {},
            "locate_on_window": {},
            "center": {},
            "pixel": {},
            "pixel_matches_color": {},
            "screenshot": {},
            "window": {},
            "get_active_window": {},
            "get_active_window_title": {},
            "get_windows_at": {},
            "get_windows_with_title": {},
            "get_all_windows": {},
            "get_all_titles": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockDEScreenPart(AbstractScreen, MockOSALBase):
    BACKEND_ID = "MockDEScreenPart"


class MockDSScreenPart(AbstractScreen, MockOSALBase):
    BACKEND_ID = "MockDSScreenPart"

    def get_size(self) -> Size: pass
    def get_size_max(self) -> Size: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "_take_screenshot": {},
            "get_size": {},
            "get_size_max": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockWaylandCompositorScreenPart(AbstractScreen, MockOSALBase):
    BACKEND_ID = "MockWaylandCompositorScreenPart"

    def get_size(self) -> Size: pass
    def get_size_max(self) -> Size: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "get_size": {},
            "get_size_max": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


# ============================================================================
# Dialogs Parts
# ============================================================================

class MockBaseDialogsPart(AbstractDialogs, MockOSALBase):
    BACKEND_ID = "MockBaseDialogsPart"

    def alert(self, text: str, title: str = '', button: str = 'OK', root: Optional[Any] = None, timeout: Optional[float] = None ) -> str: pass
    def confirm(self, text: str, title: str = '', buttons: tuple[str, ...] = ('OK', 'Cancel'), root: Optional[Any] = None, timeout: Optional[float] = None ) -> Optional[str]: pass
    def prompt( self, text: str, title: str = '', default: str = '', root: Optional[Any] = None, timeout: Optional[float] = None ) -> Optional[str]: pass
    def password( self, text: str, title: str = '', default: str = '', mask: str = '*', root: Optional[Any] = None, timeout: Optional[float] = None ) -> Optional[str]: pass

    def __init__(self):
        super().__init__()

        # Wrap all methods with MagicMock for call tracking
        methods = {
            "alert": {},
            "confirm": {},
            "prompt": {},
            "password": {},
        }
        for method_name, mock_params in methods.items():
            mock = MagicMock(**mock_params)
            self.register_mock(mock, method_name)


class MockDEDialogsPart(AbstractDialogs, MockOSALBase):
    BACKEND_ID = "MockDEDialogsPart"


class MockDSDialogsPart(AbstractDialogs, MockOSALBase):
    BACKEND_ID = "MockDSDialogsPart"


class MockWaylandCompositorDialogsPart(AbstractDialogs, MockOSALBase):
    BACKEND_ID = "MockWaylandCompositorDialogsPart"
