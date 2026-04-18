"""DialogsController for PyAutoGUI.

See AbstractDialogsController for documentation.
"""
from typing import Any, Optional

from ..osal.abstract_cls import AbstractDialogs
from ..utils.exceptions import PyAutoGUIException
from .abstract_cls import AbstractDialogsController


class DialogsController(AbstractDialogsController):
    """Concrete implementation of dialog box controller.

    This implementation delegates all operations directly to the OSAL layer
    without additional processing. See AbstractDialogsController for detailed
    method documentation.

    Implementation Notes:
        - Pure OSAL delegation (no parameter normalization)
        - No platform-specific behavior at this level
        - All customization handled by OSAL implementations
    """

    def __init__(self, osal: AbstractDialogs, *args, **kwargs):
        """Store OSAL backend reference for dialogs operations.

        Args:
            osal: Platform-specific dialogs OSAL implementation.
            *args: List arguments (internal usage).
            **kwargs: Keyword arguments (internal usage).

        Raises:
            ValueError: If osal is not an AbstractDialogs subclass.

        Implementation Notes:
            - Validates OSAL type at instantiation
        """
        super().__init__(*args, **kwargs)

        if not isinstance(osal, AbstractDialogs):
            raise PyAutoGUIException(f"Error: '{osal}' should be a subclass of AbstractDialogs")
        self._osal = osal

    def setup_postinit(self, *args, **kwargs):
        super().setup_postinit(*args, **kwargs)
        self._osal.setup_postinit(*args, **kwargs)

    def teardown_postinit(self, *args, **kwargs):
        self._osal.teardown_postinit(*args, **kwargs)
        super().teardown_postinit(*args, **kwargs)

    def alert(self,
              text: str = '', title: str = '', button: str = 'OK',
              root: Optional[Any] = None, timeout: Optional[float] = None, **_kwargs: Any) -> str:
        return self._osal.alert(text, title, button, root, timeout)

    def confirm(self,
                text: str = '', title: str = '', buttons: tuple[str, ...] = ('OK', 'Cancel'),
                root: Optional[Any] = None, timeout: Optional[float] = None, **_kwargs: Any) -> Optional[str]:
        return self._osal.confirm(text, title, buttons, root, timeout)

    def prompt(self,
               text: str = '', title: str = '', default: str = '',
               root: Optional[Any] = None, timeout: Optional[float] = None, **_kwargs: Any) -> Optional[str]:
        return self._osal.prompt(text, title, default, root, timeout)

    def password(self,
                 text: str = '', title: str = '', default: str = '', mask: str = '*',
                 root: Optional[Any] = None, timeout: Optional[float] = None, **_kwargs: Any) -> Optional[str]:
        return self._osal.password(text, title, default, mask, root, timeout)
