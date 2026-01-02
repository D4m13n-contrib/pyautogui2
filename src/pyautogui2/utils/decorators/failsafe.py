"""Emergency interrupt mechanism for PyAutoGUI automation.

This module implements a fail-safe system that immediately halts automation
when the mouse cursor reaches predefined "panic zones" on the screen. This
provides users with a reliable emergency stop mechanism during runaway scripts
or unexpected automation behavior.

Architecture:
    The fail-safe system consists of two components:

    1. **FailsafeManager** (Singleton): Central coordinator that:
       - Maintains list of trigger point coordinates
       - Holds reference to platform-specific position getter
       - Performs actual position checks and raises exceptions

    2. **@failsafe_decorator** (Decorator): Applied to action methods to inject
       automatic position verification before execution

Default Behavior:
    - Enabled by default (FAILSAFE=True in settings)
    - Triggers on mouse at (0, 0) - top-left corner
    - Additional points can be registered dynamically
    - Raises FailSafeException when triggered

Typical Usage:
    The system is automatically configured by Controller classes during
    initialization. Manual usage is rarely needed:

    >>> manager = FailsafeManager()
    >>> manager.register_get_position(platform_specific_getter)
    >>> manager.add_trigger_point((1919, 0))  # Top-right corner
    >>>
    >>> @failsafe_decorator
    ... def dangerous_operation(self):
    ...     # Position checked before execution
    ...     self._perform_action()

Disabling (NOT RECOMMENDED):
    >>> from pyautogui2 import settings
    >>> settings.FAILSAFE = False  # Global disable
    >>>
    >>> # Or at runtime:
    >>> FailsafeManager().enabled = False

Warning:
    Disabling fail-safe removes the primary emergency stop mechanism.
    Users should maintain alternative interrupt methods (Ctrl+C, etc.)
    if disabling this feature.

See Also:
    - utils.exceptions.FailSafeException: Exception raised on trigger
    - settings.FAILSAFE: Global enable/disable flag
    - controllers.pointer: Registers position getter during init
"""

import functools

from collections.abc import Callable
from typing import Optional

from ... import settings
from ..exceptions import FailSafeException
from ..singleton import Singleton


class FailsafeManager(metaclass=Singleton):
    """Singleton coordinator for fail-safe position checking.

    Manages the fail-safe system's global state including enable/disable flag,
    trigger point registry, and position getter function. Uses Singleton pattern
    to ensure consistent state across all Controller instances.

    The manager is typically initialized once during PointerController setup,
    which provides the platform-specific position getter. Other controllers
    then inherit this configuration automatically.

    Attributes:
        enabled: Global fail-safe activation flag. Can be toggled at runtime.
        trigger_points: List of (x, y) coordinates that trigger fail-safe.
            Defaults to [(0, 0)]. Duplicates are automatically prevented.
        _get_position: Callable that returns current mouse (x, y) position.
            Must be set by Controller before fail-safe becomes operational.

    Example:
        >>> manager = FailsafeManager()  # Get singleton instance
        >>> manager.register_get_position(my_platform.get_mouse_pos)
        >>> manager.add_trigger_point((1919, 1079))  # Bottom-right
        >>> manager.check()  # Raises if mouse at trigger point

    Thread Safety:
        While the Singleton pattern ensures single instance, individual
        method calls are NOT thread-safe. External synchronization required
        for concurrent access.

    See Also:
        - utils.singleton.Singleton: Metaclass implementation
        - check(): Main position verification method
    """

    def __init__(self):
        """Initialize manager with default configuration.

        Sets up initial state from global settings. This runs only once
        due to Singleton metaclass, even if constructor is called multiple
        times.

        Post-Conditions:
            - enabled is None
            - trigger_points contains [(0, 0)]
            - _get_position is None (must be set externally)
        """
        self._enabled: Optional[bool] = None
        self.trigger_points: list[tuple[int, int]] = []
        self._get_position: Optional[Callable[[], tuple[int, int]]] = None

        self.reset_to_defaults()

    @property
    def enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled
        return settings.FAILSAFE

    @enabled.setter
    def enabled(self, value) -> None:
        if not isinstance(value, bool):
            raise TypeError("Enabled must be boolean")
        self._enabled = bool(value)

    def reset_to_defaults(self) -> None:
        """Reset manager to default state from global settings.

        Useful for:
            - Test isolation (clean slate between test cases)
            - Runtime reconfiguration (reload from settings)
            - Recovery from invalid state

        Post-Conditions:
            - enabled = None
            - trigger_points = [(0, 0)]
            - _get_position = None

        Warning:
            Clears all custom trigger points and position getter.
            Controllers must re-register after reset.

        Example:
            >>> manager = FailsafeManager()
            >>> manager.add_trigger_point((100, 100))
            >>> manager.reset()  # Custom point removed
            >>> assert manager.trigger_points == [(0, 0)]
        """
        self._enabled = None
        self.trigger_points = [(0, 0)]
        self._get_position = None

    def add_trigger_point(self, trigger_point: tuple[int, int]) -> None:
        """Register additional fail-safe trigger coordinate.

        Adds a new (x, y) position that will trigger fail-safe when the
        mouse cursor reaches it. Automatically prevents duplicate entries.

        Common use cases:
            - Screen corners for easy emergency access
            - Application-specific safe zones
            - Multi-monitor setups with distinct panic areas

        Args:
            trigger_point: Screen coordinate tuple (x, y) in pixels.
                Must be within valid screen bounds for reliable triggering.

        Example:
            >>> manager = FailsafeManager()
            >>> manager.add_trigger_point((1919, 0))    # Top-right
            >>> manager.add_trigger_point((1919, 1079)) # Bottom-right
            >>> manager.add_trigger_point((1919, 0))    # Duplicate ignored
            >>> len(manager.trigger_points)
            3  # (0,0) + 2 unique additions

        Note:
            Negative coordinates are technically allowed but may not work
            reliably depending on platform position reporting.
        """
        if trigger_point not in self.trigger_points:
            self.trigger_points.append(trigger_point)

    def register_get_position(self, func: Callable[[], tuple[int, int]]) -> None:
        """Assign platform-specific mouse position getter function.

        Registers the callable that check() will use to query current cursor
        location. Must be set before fail-safe becomes operational.

        Args:
            func: Zero-argument callable returning (x, y) pixel coordinates.
                Should be fast (called before every action) and thread-safe
                if automation runs multi-threaded.

        Example:
            >>> from pyautogui2.osal.linux import get_mouse_position
            >>> manager = FailsafeManager()
            >>> manager.register_get_position(get_mouse_position)
            >>> manager.check()  # Now operational

        Note:
            Usually called once during PointerController.__init__().
            Subsequent controllers reuse the same singleton state.
        """
        self._get_position = func

    def check(self) -> None:
        """Verify cursor position and raise if at trigger point.

        Performs the actual fail-safe check by querying current mouse position
        and comparing against registered trigger points. This is the core
        method called by the @failsafe_decorator decorator.

        Raises:
            FailSafeException: When cursor position matches any trigger point.
                Contains detailed message with exact position and disable
                instructions.

        Behavior:
            - Returns silently if enabled=False
            - Returns silently if _get_position is None (not configured)
            - Returns silently if position not in trigger list
            - Raises exception if position matches trigger

        Example:
            >>> manager = FailsafeManager()
            >>> manager.register_get_position(lambda: (0, 0))
            >>> manager.check()  # Raises FailSafeException
            >>>
            >>> manager.register_get_position(lambda: (100, 100))
            >>> manager.check()  # Returns silently

        Performance:
            Designed for frequent calls (before every action). Position getter
            should be optimized accordingly. List lookup is O(n) but typically
            n <= 4 (screen corners).

        Thread Safety:
            Safe to call concurrently if _get_position is thread-safe.
            No state modification occurs during check.

        See Also:
            - utils.exceptions.FailSafeException: Exception details
            - failsafe_decorator(): Decorator that calls this method
        """
        if not self.enabled or self._get_position is None:
            return

        pointer_pos = self._get_position()
        if pointer_pos in self.trigger_points:
            raise FailSafeException(
                f"Fail-safe triggered: mouse at {pointer_pos}. "
                f"To disable this fail-safe, set pyautogui.settings.FAILSAFE to False. "
                f"DISABLING FAIL-SAFE IS NOT RECOMMENDED."
            )


def failsafe_decorator(func: Callable) -> Callable:
    """Decorator that injects fail-safe position check before function execution.

    Wraps the target function to automatically verify mouse cursor position
    against fail-safe triggers before allowing execution. If cursor is at a
    trigger point, raises FailSafeException instead of executing the function.

    This decorator is typically applied to "dangerous" action methods in
    Controller classes - operations that could cause harm if executed
    unintentionally (clicks, key presses, etc.).

    Args:
        func: Function to protect with fail-safe check. Can be any callable
            but typically a Controller method.

    Returns:
        Wrapped function with identical signature. Adds pre-execution check
        but preserves original return value and exceptions.

    Raises:
        FailSafeException: Propagated from FailsafeManager.check() if cursor
            at trigger point. Original function is NOT executed in this case.

    Example:
        >>> @failsafe_decorator
        ... def click(self, x, y):
        ...     self._device.click(x, y)
        ...
        >>> # If mouse at (0,0), click never executes:
        >>> obj.click(100, 100)  # Raises FailSafeException

    Not Typically Used On:
        - Query methods (get_position, screenshot)
        - Configuration setters
        - Non-destructive operations

    Performance:
        Adds ~1ms overhead per decorated call (position query + comparison).
        Negligible for human-speed automation but could accumulate in tight
        loops with thousands of operations.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        FailsafeManager().check()
        return func(*args, **kwargs)

    return wrapper


__all__ = [
    'FailsafeManager',
    'failsafe_decorator',
]
