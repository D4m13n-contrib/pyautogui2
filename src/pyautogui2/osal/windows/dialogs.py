"""WindowsDialogs.
"""
from typing import Any, Optional

from ...utils.lazy_import import lazy_import
from ..abstract_cls import AbstractDialogs


class WindowsDialogs(AbstractDialogs):
    """Common Windows-specific dialogs logic."""
    _pymsgbox = lazy_import("pymsgbox")

    def alert(
        self,
        text: str,
        title: str = '',
        button: str = 'OK',
        root: Optional[Any] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Implementation Notes:
        - Uses pymsgbox library which provides native Windows dialogs.
        - The timeout parameter is supported but may not work on all Windows versions.
        - The root parameter is platform-specific and typically unused on Windows.
        """
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
        """Implementation Notes:
        - Uses pymsgbox library which provides native Windows dialogs.
        - The timeout parameter is supported but may not work on all Windows versions.
        - The root parameter is platform-specific and typically unused on Windows.
        - The buttons parameter accepts a tuple of button labels.
        """
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
        """Implementation Notes:
        - Uses pymsgbox library which provides native Windows dialogs.
        - The timeout parameter is supported but may not work on all Windows versions.
        - The root parameter is platform-specific and typically unused on Windows.
        - The default parameter provides initial text in the input field.
        """
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
        """Implementation Notes:
        - Uses pymsgbox library which provides native Windows dialogs.
        - The timeout parameter is supported but may not work on all Windows versions.
        - The root parameter is platform-specific and typically unused on Windows.
        - The default parameter provides initial text in the password field.
        - Text is masked with asterisks as it's typed.
        """
        result: Optional[str] = self._pymsgbox.password(text, title, default, mask, root, timeout)
        return result
