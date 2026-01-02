"""Pause decorator and manager for PyAutoGUI.

Provides automatic pauses between actions to prevent overwhelming applications
and allow time for UI updates.
"""

import time

from collections.abc import Callable
from functools import wraps
from typing import Any

from ... import settings
from ..singleton import Singleton


class PauseManager(metaclass=Singleton):
    """Singleton manager for pause durations in PyAutoGUI.

    Manages two types of pauses:
    - controller_duration: Pause after high-level controller actions
      (e.g., after keyboard.write(), pointer.click())
    - osal_duration: Pause after low-level OSAL (platform) calls
      (e.g., after each key_down/key_up in write())

    Examples:
        >>> # Simple usage
        >>> manager = PauseManager()
        >>> manager.controller_duration = 0.5  # 500ms after each action

        >>> # Advanced: Fine-tune OSAL pauses
        >>> manager.osal_duration = 0.01  # 10ms between key presses

        >>> # Enable debug output
        >>> manager.debug = True
    """

    def __init__(self):
        # Initialize with defaults from settings
        self._controller_duration = settings.PAUSE_CONTROLLER_DURATION
        self._osal_duration = settings.PAUSE_OSAL_DURATION
        self._debug = settings.PAUSE_DEBUG

    @property
    def controller_duration(self) -> float:
        """Pause duration after controller-level actions (seconds).

        Applied after high-level methods like:
        - keyboard.write()
        - keyboard.hotkey()
        - pointer.click()
        - pointer.move_to()
        """
        return self._controller_duration

    @controller_duration.setter
    def controller_duration(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"Duration must be numeric, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"Duration must be >= 0, got {value}")
        self._controller_duration = float(value)

    @property
    def osal_duration(self) -> float:
        """Pause duration after platform-level actions (seconds).

        Applied after low-level OSAL calls like:
        - Each key_down()/key_up() within write()
        - Each mouse button press/release

        Useful for fine-tuning timing between individual operations.

        Warning:
            High values will significantly slow down operations.
            For write("hello"), a 0.1s OSAL pause = 1 second total
            (5 chars × 2 operations/char × 0.1s)
        """
        return self._osal_duration

    @osal_duration.setter
    def osal_duration(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"Duration must be numeric, got {type(value).__name__}")
        if value < 0:
            raise ValueError(f"Duration must be >= 0, got {value}")
        self._osal_duration = float(value)

    @property
    def debug(self) -> bool:
        """Enable debug output showing pause durations.

        When enabled, prints messages like:
            [PAUSE] KeyboardController.write(_pause=0.1): sleep 0.1s
            [PAUSE] press_key.key_down(_pause=0.01): sleep 0.01s
        """
        return self._debug

    @debug.setter
    def debug(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"Debug must be boolean, got {type(value).__name__}")
        self._debug = value

    def reset_to_defaults(self) -> None:
        """Reset all durations to default values from settings."""
        self._controller_duration = settings.PAUSE_CONTROLLER_DURATION
        self._osal_duration = settings.PAUSE_OSAL_DURATION
        self._debug = settings.PAUSE_DEBUG

    def disable_all(self) -> None:
        """Disable all pauses (set durations to 0)."""
        self._controller_duration = 0.0
        self._osal_duration = 0.0


def pause_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that adds an automatic pause after function execution.

    The pause duration is determined by:

        1. Explicit `_pause` kwarg value (if provided and numeric)
        2. Automatic detection based on the inherited abstract class:
           - `AbstractOSAL` -> Uses PAUSE_OSAL_DURATION
           - `AbstractController` -> Uses PAUSE_CONTROLLER_DURATION
        3. No pause if `_pause=False` or `_pause=0.0`

    Examples:
        >>> @pause_decorator
        ... def my_action():
        ...     print("Action executed")
        ...     # Automatic pause after this function

        >>> @pause_decorator
        ... def my_quick_action(_pause=False):
        ...     print("Action executed")
        ...     # No pause after this function

    Note:
        The pause duration is read dynamically from PauseManager,
        so changes to pause settings take effect immediately.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)

        duration = 0.0

        _pause = kwargs.get("_pause", True)    # True (by default)
        if _pause is True or _pause > 0.0:     # use "is True" to force bool type checking
            manager = PauseManager()
            if isinstance(_pause, (float, int)) and not isinstance(_pause, bool):
                duration = float(_pause)
            else:
                # args[0] should be self
                cls = args[0].__class__ if args else None
                if cls:
                    from ..abstract_cls import AbstractController, AbstractOSAL
                    if issubclass(cls, AbstractOSAL):
                        duration = manager.osal_duration
                    elif issubclass(cls, AbstractController):
                        duration = manager.controller_duration

        # Apply pause if needed
        if duration > 0.0:
            if manager.debug:
                func_name = getattr(func, '__qualname__', func.__name__)
                print(f"[PAUSE] {func_name}(_pause={_pause}): sleep {duration}s")
            time.sleep(duration)

        return result
    return wrapper


__all__ = [
    'PauseManager',
    'pause_decorator',
]

