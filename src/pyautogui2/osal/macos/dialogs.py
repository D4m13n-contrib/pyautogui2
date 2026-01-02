"""MacOSDialogs."""
from typing import Any, Optional

from ...utils.lazy_import import lazy_import
from ..abstract_cls import AbstractDialogs


class MacOSDialogs(AbstractDialogs):
    """Common MacOS-specific dialogs logic."""
    _pymsgbox = lazy_import("pymsgbox")

    def alert(
        self,
        text: str,
        title: str = '',
        button: str = 'OK',
        root: Optional[Any] = None,
        timeout: Optional[float] = None
    ) -> str:
        result: str = self._pymsgbox.alert(text, title, button, root, timeout)
        return result

    def confirm(
        self,
        text: str,
        title: str = '',
        buttons: tuple[str, ...] = ('OK', 'Cancel'),
        root: Optional[Any] = None,
        timeout: Optional[float] = None
    ) -> Optional[str]:
        result: Optional[str] = self._pymsgbox.confirm(text, title, buttons, root, timeout)
        return result

    def prompt(
        self,
        text: str,
        title: str = '',
        default: str = '',
        root: Optional[Any] = None,
        timeout: Optional[float] = None
    ) -> Optional[str]:
        result: Optional[str] = self._pymsgbox.prompt(text, title, default, root, timeout)
        return result

    def password(
        self,
        text: str,
        title: str = '',
        default: str = '',
        mask: str = '*',
        root: Optional[Any] = None,
        timeout: Optional[float] = None
    ) -> Optional[str]:
        result: Optional[str] = self._pymsgbox.password(text, title, default, mask, root, timeout)
        return result
