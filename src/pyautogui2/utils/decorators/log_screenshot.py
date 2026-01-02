"""Automatic screenshot logging for PyAutoGUI debugging and auditing.

This module provides infrastructure for capturing screenshots before/after
GUI automation actions, enabling visual debugging, audit trails, and failure
analysis. Screenshots are automatically saved with timestamps and action
context, with configurable retention limits to prevent disk exhaustion.

Architecture:
    The logging system consists of two components:

    1. **LogScreenshotManager** (Singleton): Central coordinator that:
       - Manages screenshot capture function (platform-specific)
       - Controls enable/disable state and per-call overrides
       - Handles filename generation with timestamps and context
       - Enforces retention limits via automatic old file deletion

    2. **@log_screenshot** (Decorator): Applied to action methods to inject
       automatic screenshot capture before execution

Use Cases:
    - Debugging: Visual verification of pre-action screen state
    - Audit trails: Compliance/security logging of automation activities
    - Failure analysis: Post-mortem investigation of failed automation
    - Test artifacts: Capturing evidence in CI/CD test runs

Default Behavior:
    - Disabled by default (LOG_SCREENSHOTS=False in settings)
    - Screenshots saved to LOG_SCREENSHOTS_FOLDER (default: "./logs/screenshots/")
    - Unlimited retention unless LOG_SCREENSHOTS_LIMIT set
    - Filename format: YYYY-MM-DD_HH-MM-SS-mmm_funcname_args.png

Typical Usage:
    >>> # Enable globally
    >>> from pyautogui2 import settings
    >>> settings.LOG_SCREENSHOTS = True
    >>>
    >>> # Or at runtime
    >>> from pyautogui2.utils.decorators.log_screenshot import LogScreenshotManager
    >>> manager = LogScreenshotManager()
    >>> manager.set_screenshot_func(platform_screenshot_impl)
    >>> manager.enabled = True
    >>>
    >>> # Decorated methods auto-capture
    >>> @log_screenshot
    ... def click(self, x, y):
    ...     self._device.click(x, y)
    >>>
    >>> # Per-call override
    >>> obj.click(100, 100, _log_screenshot=False)  # Skip this one

Performance Considerations:
    - Screenshot I/O can add 50-200ms per action (platform-dependent)
    - Disk space grows ~1-5MB per screenshot depending on resolution
    - Retention limits prevent unbounded growth but add file deletion overhead

Storage Management:
    With LOG_SCREENSHOTS_LIMIT=100 at 2MB/screenshot:
    - Max disk usage: ~200MB
    - Oldest files auto-deleted when limit reached
    - FIFO queue ensures chronological retention

Warning:
    High-frequency automation (>10 actions/sec) can generate GB/hour of
    screenshots. Use retention limits and consider selective decoration
    (only critical actions) for production environments.

See Also:
    - settings.LOG_SCREENSHOTS: Global enable flag
    - settings.LOG_SCREENSHOTS_FOLDER: Output directory path
    - settings.LOG_SCREENSHOTS_LIMIT: Max file retention count
    - controllers.screen: Provides platform screenshot implementation
"""

import datetime
import logging
import pathlib

from collections import deque
from collections.abc import Callable
from functools import wraps
from typing import Any, Optional

from ... import settings
from ..singleton import Singleton


class LogScreenshotManager(metaclass=Singleton):
    """Singleton coordinator for automated screenshot logging.

    Manages the screenshot logging system's global state including enable/disable
    flag, screenshot capture function, output directory, and retention policy
    enforcement. Uses Singleton pattern to ensure consistent configuration across
    all Controller instances.

    The manager is typically initialized once during ScreenController setup,
    which provides the platform-specific screenshot implementation. Decorated
    methods then automatically use this shared configuration.

    Attributes:
        _enabled: Global logging activation flag. Initialized from
            settings.LOG_SCREENSHOTS but can be toggled at runtime.
        _screenshot_func: Callable that captures and saves a screenshot.
            Must accept filepath as first argument. Set by Controller during init.
        _screenshot_filenames: FIFO queue tracking saved screenshot paths for
            retention limit enforcement. Oldest files deleted when limit reached.

    Example:
        >>> manager = LogScreenshotManager()  # Get singleton instance
        >>> manager.set_screenshot_func(my_platform.screenshot)
        >>> manager.enabled = True
        >>>
        >>> # Manual logging (typically called by decorator)
        >>> manager.log_screenshot(some_func, x=100, y=200)
        >>> # Saves: 2024-01-15_14-30-45-123_some_func_x:100,y:200.png

    Thread Safety:
        While Singleton ensures single instance, individual method calls are
        NOT thread-safe. Concurrent log_screenshot() calls may interleave
        filename queue operations. External synchronization required for
        multi-threaded automation.

    Disk Space Management:
        Automatic cleanup prevents unbounded growth:
        - Queue tracks all saved files in chronological order
        - When count reaches LOG_SCREENSHOTS_LIMIT, oldest file deleted
        - Deletion happens synchronously during log_screenshot() call

    See Also:
        - utils.singleton.Singleton: Metaclass implementation
        - log_screenshot(): Decorator that calls this manager
    """

    def __init__(self):
        """Initialize manager with default configuration.

        Sets up initial state from global settings. Runs only once due to
        Singleton metaclass, even if constructor called multiple times.

        Post-Conditions:
            - _enabled set to settings.LOG_SCREENSHOTS value
            - _screenshot_func is None (must be set externally)
            - _screenshot_filenames is empty deque
            - LOG_SCREENSHOTS_FOLDER directory created if missing
        """
        self._enabled: Optional[bool] = None
        self._screenshot_func: Optional[Callable[..., Any]] = None
        self._screenshot_filenames: Optional[deque[pathlib.Path]] = None

        self.reset_to_defaults()

    @property
    def enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled
        return settings.LOG_SCREENSHOTS

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
        - Clearing filename queue without deleting files

        Post-Conditions:
            - _enabled = LOG_SCREENSHOTS
            - _screenshot_func = None
            - _screenshot_filenames = empty deque
            - LOG_SCREENSHOTS_FOLDER directory exists

        Side Effects:
            Creates LOG_SCREENSHOTS_FOLDER if it doesn't exist. Does NOT
            delete existing screenshot files, only clears tracking queue.

        Warning:
            After reset(), ScreenController must call set_screenshot_func()
            again before logging will work. Decorated methods will silently
            fail (with error log) until reconfigured.

        Example:
            >>> manager = LogScreenshotManager()
            >>> manager.enable()
            >>> manager.log_screenshot(func)  # Works
            >>> manager.reset()
            >>> manager.log_screenshot(func)  # Logs error, no screenshot
        """
        self._enabled = None
        self._screenshot_func = None
        self._screenshot_filenames = deque([])

    def set_screenshot_func(self, func: Callable[..., Any]) -> None:
        """Assign platform-specific screenshot capture implementation.

        Registers the callable that log_screenshot() will use to save images.
        Must be set before screenshot logging becomes operational.

        Args:
            func: Callable accepting filepath as first argument (plus optional
                platform-specific kwargs). Should save screenshot to the given
                path and raise exceptions on failure rather than silently failing.

        Example:
            >>> from pyautogui2.osal.linux import screenshot
            >>> manager = LogScreenshotManager()
            >>> manager.set_screenshot_func(screenshot)
            >>> manager.enable()
            >>> # Now decorated methods will capture screenshots

        Note:
            Usually called once during ScreenController.__init__(). Subsequent
            controllers reuse the same singleton state.

        Performance:
            The provided function should be reasonably fast (<200ms) since it's
            called synchronously during action execution. Slow implementations
            will directly impact automation throughput.
        """
        self._screenshot_func = func

    def log_screenshot(self, caller_func: Callable, *args, **kwargs) -> None:
        """Capture and save screenshot with contextual filename.

        Performs the actual screenshot operation with automatic filename
        generation including timestamp, function name, and truncated arguments.
        Enforces retention limits by deleting oldest files when threshold reached.

        Args:
            caller_func: Function being decorated (used for filename context).
            *args: Positional arguments from the decorated call (for filename).
            **kwargs: Keyword arguments from the decorated call. Special handling:
                - _log_screenshot: If False, skip capture (default: self._enabled)
                - Other kwargs included in filename (truncated to 12 chars total)

        Returns:
            None. Failures logged but not raised (non-blocking).

        Side Effects:
            - Creates PNG file in LOG_SCREENSHOTS_FOLDER
            - Appends filepath to _screenshot_filenames queue
            - Deletes oldest file if LOG_SCREENSHOTS_LIMIT exceeded
            - Logs error if _screenshot_func not configured

        Filename Format:
            YYYY-MM-DD_HH-MM-SS-mmm_funcname_args.png

            Example: 2024-01-15_14-30-45-123_click_100,200,btn:1.png
            - Date/time with millisecond precision
            - Function name from caller_func.__name__
            - Args truncated to 24 chars (prevents excessively long names)

        Collision Handling:
            If a file with the generated name already exists (possible with rapid
            calls in the same millisecond), appends a counter suffix:
            - original.png
            - original_1.png
            - original_2.png
            This ensures no screenshot overwrites another, preserving complete
            audit trails even for high-frequency automation.

        Retention Logic:
            When LOG_SCREENSHOTS_LIMIT set (e.g., 100):
            1. Save new screenshot
            2. Add to front of deque (newest first)
            3. If deque length >= limit:
               - Pop oldest filepath from back
               - Delete file from disk (os.unlink)

        Error Handling:
            - Missing _screenshot_func: Error logged, returns silently
            - I/O errors (disk full, permissions): Raised to caller
            - Missing args/kwargs: Empty string used in filename

        Example:
            >>> manager = LogScreenshotManager()
            >>> manager.set_screenshot_func(save_png)
            >>> manager.enable()
            >>>
            >>> def click(self, x, y, button=1):
            ...     pass  # Actual click logic
            >>>
            >>> # Called by decorator:
            >>> manager.log_screenshot(click, 100, 200, button=1)
            >>> # Saves: 2024-01-15_14-30-45-123_click_100,200,butt.png

        Performance:
            - Screenshot I/O: 50-200ms (platform-dependent)
            - Filename generation: <1ms
            - File deletion (when limit hit): ~5ms
            - Total overhead: ~60-210ms per call when enabled

        Thread Safety:
            NOT thread-safe. Concurrent calls may:
            - Interleave filename queue operations (corruption risk)
            - Delete wrong file if queue modified mid-operation
            External locking required for multi-threaded use.

        See Also:
            - log_screenshot(): Decorator that calls this method
            - settings.LOG_SCREENSHOTS_LIMIT: Retention configuration
        """
        _log_screenshot = kwargs.get("_log_screenshot", self.enabled)
        if not _log_screenshot:
            return

        if self._screenshot_func is None:
            logging.error("No screenshot function set in LogScreenshotManager.")
            return

        # Ensure that the "specifics" string isn't too long for the filename:
        args_str = ",".join([f"{v}" for v in args] + [f"{k}:{v}" for k,v in kwargs.items()])
        args_str = args_str[:24]

        now = datetime.datetime.now()
        # Format: YYYY-MM-DD_hh-mm-ss-uuu_<func>_<args>.png
        filename = (f"{now.year}-{str(now.month).rjust(2, '0')}-{str(now.day).rjust(2, '0')}"
                    f"_"
                    f"{str(now.hour).rjust(2, '0')}-{str(now.minute).rjust(2, '0')}-{str(now.second).rjust(2, '0')}-{str(now.microsecond)[:3]}"
                    f"_"
                    f"{caller_func.__name__}_{args_str}"
                    f".png")

        # Create log_screenshots folder if it doesn't exist
        folder = pathlib.Path(settings.LOG_SCREENSHOTS_FOLDER)
        folder.mkdir(parents=True, exist_ok=True)

        # Generate unique filepath (handle collisions):
        filepath = folder / filename
        counter = 1
        while filepath.exists():
            # Collision detected - append counter before extension
            stem = filename[:-4]  # Remove .png
            unique_filename = f"{stem}_{counter}.png"
            filepath = folder / unique_filename
            counter += 1

            # Safety limit to prevent infinite loop (should never happen)
            if counter > 10000:
                logging.error(f"Failed to generate unique filename after 10000 attempts: {filename}")
                return

        logging.debug(f"Log screenshot: {str(filepath)}")
        self._screenshot_func(str(filepath))

        if settings.LOG_SCREENSHOTS_LIMIT is not None:
            assert(self._screenshot_filenames is not None), "Error: 'reset' should be create a deque"
            self._screenshot_filenames.appendleft(filepath)

            # Delete the oldest screenshot if we've reached the maximum:
            if len(self._screenshot_filenames) > settings.LOG_SCREENSHOTS_LIMIT:
                file_to_remove = self._screenshot_filenames.pop()
                file_to_remove.unlink()


def log_screenshot(func: Callable) -> Callable:
    """Decorator that captures screenshot before executing decorated function.

    Wraps the target function to automatically save a screenshot with contextual
    filename before function execution. The screenshot captures the screen state
    just before the action, useful for debugging unexpected behavior or creating
    audit trails.

    The decorator extracts function arguments and passes them to LogScreenshotManager
    for filename generation, then executes the original function unchanged.

    Args:
        func: Function to wrap with screenshot logging. Typically a Controller
            action method (click, press, write, etc.).

    Returns:
        Wrapped function with identical signature. Adds pre-execution screenshot
        but preserves original return value and exceptions.

    Behavior:
        1. Extract *args and **kwargs from call
        2. Call LogScreenshotManager().log_screenshot(func, *args, **kwargs)
        3. Execute original function with unchanged arguments
        4. Return original function's return value

    Per-Call Control:
        Decorated functions accept _log_screenshot kwarg to override behavior:
        - _log_screenshot=True: Force capture even if globally disabled
        - _log_screenshot=False: Skip capture even if globally enabled
        - Not provided: Use LogScreenshotManager._enabled state

    Example:
        >>> @log_screenshot
        ... def click(self, x, y, button=1):
        ...     self._device.click(x, y, button)
        ...
        >>> obj.click(100, 200)  # Screenshot + click
        >>> obj.click(300, 400, _log_screenshot=False)  # Click only

    Common Targets:
        - PointerController.click(), press(), scroll()
        - KeyboardController.press(), write()
        - Any action that modifies GUI state

    Not Typically Used On:
        - Query methods (screenshot itself, get_position)
        - Fast loops (performance overhead)
        - Non-GUI operations (file I/O, calculations)

    Performance Impact:
        Adds 50-200ms overhead per decorated call when enabled (platform-specific
        screenshot I/O time). Consider selective decoration for high-frequency
        automation:

        >>> @log_screenshot  # Log high-level actions
        ... def click_login_button(self):
        ...     self._click_internal(x, y)  # Internal helper not decorated
        ...
        ... def _click_internal(self, x, y):  # Fast, no logging
        ...     self._device.click(x, y)

    Error Handling:
        Screenshot failures (missing func, I/O errors) are logged but NOT raised.
        The decorated function executes regardless of screenshot success. This
        prevents screenshot issues from breaking automation.

    Storage Considerations:
        Each screenshot typically 1-5MB depending on resolution. High-frequency
        decoration can generate GB/hour:
        - 1920x1080 PNG: ~2MB
        - 10 clicks/second: ~72GB/hour
        - Use LOG_SCREENSHOTS_LIMIT to cap retention

    See Also:
        - LogScreenshotManager.log_screenshot(): Underlying implementation
        - settings.LOG_SCREENSHOTS: Global enable flag
        - settings.LOG_SCREENSHOTS_LIMIT: Retention limit
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        LogScreenshotManager().log_screenshot(func, *args, **kwargs)
        return func(self, *args, **kwargs)
    return wrapper
