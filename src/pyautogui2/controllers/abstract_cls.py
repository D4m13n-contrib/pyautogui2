"""Abstract base classes for high-level PyAutoGUI controllers.

This module defines the controller layer that sits between the user-facing
API and the platform-specific OSAL implementations. Each controller manages
a specific aspect of GUI automation:

- AbstractPointerController: Mouse/touchpad cursor control and clicks
- AbstractKeyboardController: Keyboard input and text entry
- AbstractScreenController: Screenshot capture and image recognition
- AbstractDialogsController: Modal dialog boxes (alert, confirm, prompt)

Controllers handle cross-platform logic, coordinate with the ControllerManager,
and delegate platform-specific operations to their respective OSAL backends.
"""

from abc import abstractmethod
from collections.abc import Iterable
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Optional, Union

from ..utils.abstract_cls import AbstractController
from ..utils.decorators import DEFAULTS as DECORATORS_TO_REMOVE
from ..utils.types import ArgCoordX, ArgCoordY, Box, ButtonName, Point, Size


if TYPE_CHECKING:
    from PIL import Image


class AbstractPointerController(AbstractController):
    """Abstract base class for mouse/touchpad pointer control.

    This controller manages all pointer-related operations including:
    - Cursor positioning (absolute and relative movement)
    - Mouse button events (down, up, click sequences)
    - Drag operations
    - Scroll/wheel events

    The controller delegates platform-specific implementations to its OSAL
    backend while handling cross-platform concerns like coordinate validation,
    failsafe checks, and operation logging.

    Attributes:
        _osal: Platform-specific pointer OSAL implementation (injected via __init__).

    Example:
        >>> # Typically accessed via ControllerManager:
        >>> from pyautogui2.controllers.manager import ControllerManager
        >>> manager = ControllerManager()
        >>> pointer = manager.pointer
        >>> pointer.move_to(100, 200)
        >>> pointer.click()

    Note:
        All abstract methods defined here must be implemented by concrete
        subclasses (e.g., PointerController in controllers/pointer.py).
        Decorators are automatically applied via __init_subclass__ unless
        explicitly removed in __abstractmethod_remove_decorators__.
    """

    __abstractmethod_remove_decorators__ = {
        "mouse_info": DECORATORS_TO_REMOVE,
        "get_position": DECORATORS_TO_REMOVE,
        "on_screen": DECORATORS_TO_REMOVE,
    }

    __abstractmethod_decorators__ = {
        "move_to": ["log_screenshot"],
        "move_rel": ["log_screenshot"],
        "button_down": ["log_screenshot"],
        "button_up": ["log_screenshot"],
        "click": ["log_screenshot"],
        "left_click": ["log_screenshot"],
        "right_click": ["log_screenshot"],
        "middle_click": ["log_screenshot"],
        "double_click": ["log_screenshot"],
        "triple_click": ["log_screenshot"],
        "drag_to": ["log_screenshot"],
        "drag_rel": ["log_screenshot"],
        "hscroll": ["log_screenshot"],
        "vscroll": ["log_screenshot"],
        "scroll": ["log_screenshot"],
    }


    # --------------------------------------------------
    # Info functions
    # --------------------------------------------------
    @abstractmethod
    def mouse_info(self) -> None:
        """Launch the MouseInfo utility application for coordinate inspection.

        Opens a GUI tool that displays real-time mouse coordinates, pixel colors,
        and other information useful for planning GUI automation tasks. This is
        a debugging/development utility, not meant for programmatic use.

        Blocks:
            This method blocks execution until the MouseInfo window is closed.

        Example:
            >>> pointer.mouse_info()  # Opens window, blocks until closed

        Note:
            Requires the `mouseinfo` package to be installed. The appearance and
            features vary by platform but typically include:
            - Current mouse coordinates
            - RGB color under cursor
            - Screenshot preview
        """
        pass

    @abstractmethod
    def get_position(self, **kwargs: Any) -> Point:
        """Get the current absolute position of the mouse cursor.

        Returns:
            A tuple (x, y) representing the cursor's position in screen
            coordinates, where (0, 0) is the top-left corner of the primary
            monitor.

        Example:
            >>> x, y = pointer.get_position()
            >>> print(f"Cursor at ({x}, {y})")
            Cursor at (1024, 768)

        Note:
            On multi-monitor setups, coordinates may extend beyond the primary
            screen dimensions. The screen controller can provide total desktop
            size via get_virtual_size().
        """
        pass

    @abstractmethod
    def on_screen(self,
                  x: Optional[ArgCoordX] = None,
                  y: Optional[ArgCoordY] = None,
                  **kwargs: Any) -> bool:
        """Check if a point (or the current cursor position) is within screen bounds.

        Args:
            x: X coordinate to test. If None, uses current cursor X position.
            y: Y coordinate to test. If None, uses current cursor Y position.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            True if the point is within the primary screen bounds, False otherwise.

        Example:
            >>> # Check if cursor is on screen
            >>> pointer.on_screen()
            True
            >>>
            >>> # Check if specific point is valid
            >>> pointer.on_screen(x=1920, y=1080)
            False  # Assuming 1920x1080 screen (0-1919, 0-1079)

        Note:
            On multi-monitor setups, this checks only the primary screen by default.
            For virtual desktop bounds checking, compare against get_size_max().
        """
        pass


    # --------------------------------------------------
    # Move functions
    # --------------------------------------------------
    @abstractmethod
    def move_to(self,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                duration: float = 0.0, tween: Optional[str] = None,
                **kwargs: Any) -> None:
        """Move the mouse cursor to an absolute screen position.

        Args:
            x: Target X coordinate. If None, uses current X position.
            y: Target Y coordinate. If None, uses current Y position.
            duration: Time in seconds to complete the movement. If 0.0 (default),
                the cursor jumps instantly. Values > 0.0 create smooth animated
                movement.
            tween: Easing function name for animated movement (e.g., 'linear',
                'easeInQuad'). See pytweening documentation for available options.
                Ignored if duration is 0.0. Default is 'linear'.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.move_to(500, 300)  # Instant jump
            >>> pointer.move_to(500, 300, duration=1.0, tween='easeInOutQuad')  # Smooth 1-second animation

        Note:
            Coordinates are validated against screen bounds by the controller
            before being passed to the OSAL. Percentage strings are resolved
            relative to the primary screen dimensions.
        """
        pass

    @abstractmethod
    def move_rel(self,
                 offset_x: Optional[int] = None, offset_y: Optional[int] = None,
                 duration: float = 0.0, tween: Optional[str] = None,
                 **kwargs: Any) -> None:
        """Move the mouse cursor relative to its current position.

        Args:
            offset_x: Horizontal offset in pixels. Positive values move right,
                negative values move left. If None, no horizontal movement.
            offset_y: Vertical offset in pixels. Positive values move down,
                negative values move up. If None, no vertical movement.
            duration: Time in seconds to complete the movement. See move_to().
            tween: Easing function name. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.move_rel(offset_x=100)  # Move 100px right
            >>> pointer.move_rel(offset_y=-50, duration=0.5)  # Move 50px up smoothly

        Note:
            The final position is calculated as (current_x + offset_x, current_y + offset_y)
            and validated against screen bounds before execution.
        """
        pass


    # --------------------------------------------------
    # Button functions
    # --------------------------------------------------
    @abstractmethod
    def button_down(self,
                    x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                    button: Optional[ButtonName] = None,
                    **kwargs: Any) -> None:
        """Press and hold a mouse button without releasing it.

        Args:
            x: X coordinate to move to before pressing. If None, presses at
                current position.
            y: Y coordinate to move to before pressing. If None, presses at
                current position.
            button: Button to press ('left', 'right', 'middle'). If None,
                uses the primary button (accounting for left-handed mode).
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.button_down(button='left')  # Start drag operation
            >>> pointer.move_to(500, 500)
            >>> pointer.button_up()  # Complete drag

        Note:
            Must be paired with button_up() to complete the operation. Unpaired
            button_down() calls may leave the button stuck in a pressed state.
        """
        pass

    @abstractmethod
    def button_up(self,
                  x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                  button: Optional[ButtonName] = None,
                  **kwargs: Any) -> None:
        """Release a previously pressed mouse button.

        Args:
            x: X coordinate to move to before releasing. If None, releases at
                current position.
            y: Y coordinate to move to before releasing. If None, releases at
                current position.
            button: Button to release. Must match the button used in button_down().
                If None, releases the primary button.
            **kwargs: Keyword arguments (internal usage).

        Example:
            See button_down() for usage example.

        Note:
            Calling button_up() without a prior button_down() is typically a no-op
            but may produce unexpected behavior on some platforms.
        """
        pass


    # --------------------------------------------------
    # Click functions
    # --------------------------------------------------
    @abstractmethod
    def click(self,
              x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
              button: Optional[ButtonName] = None,
              clicks: int = 1, interval: float = 0.0,
              duration: float = 0.0, tween: Optional[str] = None,
              **kwargs: Any) -> None:
        """Perform one or more complete click operations (down + up pairs).

        Args:
            x: X coordinate for the click. If None, clicks at current position.
            y: Y coordinate for the click. If None, clicks at current position.
            button: Button to click ('left', 'right', 'middle'). If None,
                uses the primary button.
            clicks: Number of consecutive clicks (e.g., 2 for double-click).
                Must be >= 1.
            interval: Delay in seconds between consecutive clicks. Only relevant
                when clicks > 1.
            duration: Time to animate cursor movement before clicking. See move_to().
            tween: Easing function for cursor animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Raises:
            PyAutoGUIException: If clicks < 1.

        Example:
            >>> pointer.click()  # Single left-click at current position
            >>> pointer.click(x=100, y=200, clicks=2, interval=0.1)  # Double-click
            >>> pointer.click(button='right')  # Right-click (context menu)

        Note:
            Each click is a complete button_down + button_up sequence. For
            drag operations, use button_down/button_up directly.
        """
        pass

    @abstractmethod
    def left_click(self,
                   x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                   interval: float = 0.0,
                   duration: float = 0.0, tween: Optional[str] = None,
                   **kwargs: Any) -> None:
        """Convenience method for a single left-button click.

        Equivalent to click(x, y, button='left', clicks=1, ...).

        Args:
            x: X coordinate for the click.
            y: Y coordinate for the click.
            interval: Unused (kept for API consistency).
            duration: Time to animate cursor movement.
            tween: Easing function for cursor animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.left_click(x=100, y=200)
        """
        pass

    @abstractmethod
    def right_click(self,
                    x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                    interval: float = 0.0,
                    duration: float = 0.0, tween: Optional[str] = None,
                    **kwargs: Any) -> None:
        """Convenience method for a single right-button click (context menu).

        Equivalent to click(x, y, button='right', clicks=1, ...).

        Args:
            x: X coordinate for the click.
            y: Y coordinate for the click.
            interval: Unused (kept for API consistency).
            duration: Time to animate cursor movement.
            tween: Easing function for cursor animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.right_click()  # Open context menu at cursor
        """
        pass

    @abstractmethod
    def middle_click(self,
                     x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                     interval: float = 0.0,
                     duration: float = 0.0, tween: Optional[str] = None,
                     **kwargs: Any) -> None:
        """Convenience method for a single middle-button click.

        Equivalent to click(x, y, button='middle', clicks=1, ...).

        Args:
            x: X coordinate for the click.
            y: Y coordinate for the click.
            interval: Unused (kept for API consistency).
            duration: Time to animate cursor movement.
            tween: Easing function for cursor animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.middle_click()  # Often opens link in new tab
        """
        pass

    @abstractmethod
    def double_click(self,
                     x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                     interval: float = 0.0,
                     button: Optional[ButtonName] = None,
                     duration: float = 0.0, tween: Optional[str] = None,
                     **kwargs: Any) -> None:
        """Convenience method for a double left-click.

        Equivalent to click(x, y, button='left', clicks=2, interval=interval, ...).

        Args:
            x: X coordinate for the double-click.
            y: Y coordinate for the double-click.
            interval: Delay in seconds between the two clicks (default 0.0).
            button: Button to click ('left', 'right', 'middle'). If None,
                uses the primary button.
            duration: Time to animate cursor movement before first click.
            tween: Easing function for cursor animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.double_click(x=100, y=200)  # Open file/folder
        """
        pass

    @abstractmethod
    def triple_click(self,
                     x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                     interval: float = 0.0,
                     button: Optional[ButtonName] = None,
                     duration: float = 0.0, tween: Optional[str] = None,
                     **kwargs: Any) -> None:
        """Convenience method for a triple left-click.

        Equivalent to click(x, y, button='left', clicks=3, interval=interval, ...).

        Args:
            x: X coordinate for the triple-click.
            y: Y coordinate for the triple-click.
            interval: Delay in seconds between clicks (default 0.0).
            button: Button to click ('left', 'right', 'middle'). If None,
                uses the primary button.
            duration: Time to animate cursor movement before first click.
            tween: Easing function for cursor animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.triple_click()  # Select entire paragraph in text editor
        """
        pass


    # --------------------------------------------------
    # Drag functions
    # --------------------------------------------------
    @abstractmethod
    def drag_to(self,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                button: Optional[ButtonName] = None,
                duration: float = 0.0, tween: Optional[str] = None,
                **kwargs: Any) -> None:
        """Drag from current position to target position while holding a button.

        This is equivalent to:
        1. button_down(button) at current position
        2. move_to(x, y, duration, tween)
        3. button_up(button) at target position

        Args:
            x: Target X coordinate.
            y: Target Y coordinate.
            button: Button to hold during drag. If None, uses primary button.
            duration: Time to complete the drag movement (default 0.0 = instant).
            tween: Easing function for drag animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.move_to(100, 100)
            >>> pointer.drag_to(x=500, y=500, duration=1.0)  # Smooth drag

        Note:
            Unlike button_down/button_up pairs, drag_to ensures the button
            is released even if an error occurs during movement.
        """
        pass

    @abstractmethod
    def drag_rel(self,
                 offset_x: Optional[int] = None, offset_y: Optional[int] = None,
                 button: Optional[ButtonName] = None,
                 duration: float = 0.0, tween: Optional[str] = None,
                 **kwargs: Any) -> None:
        """Drag relative to current position while holding a button.

        Equivalent to drag_to() but with relative offsets instead of absolute
        coordinates.

        Args:
            offset_x: Horizontal drag distance in pixels.
            offset_y: Vertical drag distance in pixels.
            button: Button to hold during drag. If None, uses primary button.
            duration: Time to complete the drag movement.
            tween: Easing function for drag animation. See move_to().
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.drag_rel(offset_x=200, offset_y=100, duration=0.5)
        """
        pass


    # --------------------------------------------------
    # Scroll functions
    # --------------------------------------------------
    @abstractmethod
    def hscroll(self,
                clicks: int,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                **kwargs: Any) -> None:
        """Scroll the mouse wheel horizontally.

        Args:
            clicks: Number of "clicks" to scroll. Positive values scroll right,
                negative values scroll left. Not all platforms/applications
                support horizontal scrolling.
                The actual scroll distance per click is platform/application-dependent.
            x: X coordinate to position cursor before scrolling. If None,
                scrolls at current position.
            y: Y coordinate to position cursor before scrolling. If None,
                scrolls at current position.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.hscroll(clicks=5)  # Scroll right 5 notches
            >>> pointer.hscroll(clicks=-3, x=500, y=500)  # Scroll left at specific position

        Note:
            Horizontal scroll support varies by platform. May be a no-op on
            systems without horizontal scroll wheel support.
        """
        pass

    @abstractmethod
    def vscroll(self,
                clicks: int,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                **kwargs: Any) -> None:
        """Scroll the mouse wheel vertically.

        Args:
            clicks: Number of "clicks" to scroll. Positive values scroll up
                (toward the user), negative values scroll down (away from user).
                The actual scroll distance per click is platform/application-dependent.
            x: X coordinate to position cursor before scrolling. If None,
                scrolls at current position.
            y: Y coordinate to position cursor before scrolling. If None,
                scrolls at current position.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.vscroll(clicks=5)  # Scroll up 5 notches
            >>> pointer.vscroll(clicks=-3, x=500, y=500)  # Scroll down at specific position

        Note:
            The scroll direction convention (positive = up) matches most platforms
            but may be inverted in some applications or with "natural scrolling" enabled.
        """
        pass

    @abstractmethod
    def scroll(self,
               clicks: int,
               x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
               **kwargs: Any) -> None:
        """Scroll the mouse wheel.

        Args:
            clicks: Number of "clicks" to scroll.
                The actual scroll distance per click is platform/application-dependent.
            x: X coordinate to position cursor before scrolling. If None,
                scrolls at current position.
            y: Y coordinate to position cursor before scrolling. If None,
                scrolls at current position.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> pointer.scroll(clicks=5)  # Scroll up 5 notches
            >>> pointer.scroll(clicks=-3, x=500, y=500)  # Scroll down at specific position

        Note:
            The default scroll direction convention is often vertically.
        """
        pass


class AbstractKeyboardController(AbstractController):
    """Abstract base class for keyboard input control.

    This controller manages all keyboard-related operations including:
    - Individual key press/release events
    - Text entry (type strings)
    - Hotkey combinations (Ctrl+C, Alt+Tab, etc.)
    - Keyboard layout detection and management

    The controller coordinates with the OSAL backend to translate high-level
    operations (like "press Ctrl+C") into platform-specific key events.

    Attributes:
        _osal: Platform-specific keyboard OSAL implementation (injected via __init__).

    Example:
        >>> from pyautogui2.controllers.manager import ControllerManager
        >>> manager = ControllerManager()
        >>> keyboard = manager.keyboard
        >>> keyboard.write("Hello, world!")
        >>> keyboard.hotkey('ctrl', 'c')

    Note:
        Key names are normalized across platforms (e.g., 'ctrl' works on all OSes,
        even though MacOS uses 'command' for most shortcuts). See the keyboard
        OSAL documentation for platform-specific key name mappings.
    """

    __abstractmethod_remove_decorators__ = {
        "get_layout": DECORATORS_TO_REMOVE,
        "is_valid_key": DECORATORS_TO_REMOVE,
    }

    __abstractmethod_decorators__ = {
        "key_down": ["log_screenshot"],
        "key_up": ["log_screenshot"],
        "press_key": ["log_screenshot"],
        "write": ["log_screenshot"],
        "hold": ["log_screenshot"],
        "hotkey": ["log_screenshot"],
        "codepoint": ["log_screenshot"],
    }


    # --------------------------------------------------
    # Layout functions
    # --------------------------------------------------
    @abstractmethod
    def get_layout(self, **kwargs: Any) -> str:
        """Get the current keyboard layout identifier.

        Returns:
            A platform-specific layout identifier string, such as:
            - "us", "fr", "de" on Linux (from setxkbmap or xkblayout-state)
            - "com.apple.keylayout.US" on MacOS
            - "00000409" (LCID) on Windows

        Example:
            >>> layout = keyboard.get_layout()
            >>> print(f"Current layout: {layout}")
            Current layout: us

        Note:
            The format and available layouts vary by platform. Implementations
            should cache the result if layout detection is expensive.
        """
        pass


    # --------------------------------------------------
    # Key press/release functions
    # --------------------------------------------------
    @abstractmethod
    def key_down(self, key: str, **kwargs: Any) -> None:
        """Press and hold a key without releasing it.

        Args:
            key: Key name to press (e.g., 'a', 'shift', 'ctrl', 'enter').
                Must be a valid key name recognized by the platform OSAL.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> keyboard.key_down('shift')
            >>> keyboard.press('a')  # Types 'A' (shifted)
            >>> keyboard.key_up('shift')

        Raises:
            PyAutoGUIException: If the key name is not recognized.

        Note:
            Must be paired with key_up() to avoid leaving the key stuck.
            Use press() for complete key press cycles, or hotkey() for
            modifier combinations.
        """
        pass

    @abstractmethod
    def key_up(self, key: str, **kwargs: Any) -> None:
        """Release a previously pressed key.

        Args:
            key: Key name to release. Should match a prior key_down() call.
            **kwargs: Keyword arguments (internal usage).

        Example:
            See key_down() for usage.

        Note:
            Calling key_up() without a matching key_down() is typically safe
            but may be ignored by the OS.
        """
        pass

    @abstractmethod
    def press_key(self, key: str, presses: int = 1, interval: float = 0.0, **kwargs: Any) -> None:
        """Perform one or more complete key press operations (down + up).

        Args:
            key: Key name to press (e.g., 'enter', 'escape', 'f1').
            presses: Number of times to press the key (default 1).
            interval: Delay in seconds between consecutive presses.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> keyboard.press('enter')  # Single press
            >>> keyboard.press('down', presses=5, interval=0.1)  # Navigate list

        Example with unmapped character:
            >>> press_key('é')  # On US QWERTY without 'é' key
            # Automatically types 'é' via codepoint mechanism

        Note:
            For modifier combinations, use hotkey() instead. This method
            presses keys sequentially, not simultaneously.
        """
        pass

    @abstractmethod
    def write(self, text: str, interval: float = 0.0, **kwargs: Any) -> None:
        r"""Write a string of text by simulating individual key presses.

        Args:
            text: The string to write. Can include special characters, newlines,
                and unicode. Each character is mapped to the appropriate key
                sequence for the current keyboard layout.
            interval: Delay in seconds between individual key presses (default 0.0).
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> keyboard.write("Hello, world!")
            >>> keyboard.write("Line 1\nLine 2", interval=0.05)  # Slower typing

        Note:
            This method attempts to match the input text exactly, including:
            - Capitalization (via automatic Shift)
            - Special characters (via layout-specific key sequences)
            - Unicode characters (if supported by the platform/layout)

            For non-latin scripts or complex input, some platforms may fall
            back to clipboard-based text injection (see paste()).
        """
        pass

    @abstractmethod
    def is_valid_key(self, key: str, **kwargs) -> bool:
        """Check if a string represents a valid key name for the current platform.

        Args:
            key: The key name to validate (e.g., 'enter', 'ctrl', 'a', 'f1').
            **kwargs: Keyword arguments (internal usage).

        Returns:
            True if the key name is recognized by the keyboard OSAL, False otherwise.

        Example:
            >>> keyboard.is_valid_key('enter')
            True
            >>> keyboard.is_valid_key('ctrl')
            True
            >>> keyboard.is_valid_key('invalid_key_xyz')
            False

        Note:
            Valid key names vary by platform and keyboard layout. Common keys
            (alphanumeric, modifiers, function keys) are usually cross-platform,
            but special keys may differ (e.g., 'command' vs 'win').
        """
        pass

    @abstractmethod
    def hold(self, *keys, interval: float = 0.0, **kwargs) -> AbstractContextManager[None]:
        """Context manager to hold a key pressed for the duration of a block.

        Args:
            keys: Key names to hold (typically a modifier like 'ctrl', 'shift', 'alt').
                Accepts either individual arguments, a list, or a "+" separated string.
            interval: Delay in seconds between key presses (default 0.0).
            **kwargs: Keyword arguments (internal usage).

        Yields:
            None (control flow only).

        Example:
            >>> with keyboard.hold('ctrl'):
            ...     keyboard.press('c')  # Ctrl+C
            ...     keyboard.press('v')  # Ctrl+V

        Usage patterns:
            >>> with hold('ctrl', 'shift'):    # Multiple args
            >>> with hold(['ctrl', 'shift']):  # List
            >>> with hold('ctrl+shift'):       # String with separators

        Note:
            - Automatically releases the key when the block exits, even if an
            exception occurs. Equivalent to try/finally with key_down/key_up.
            - The reverse release order ensures proper modifier key handling
            (e.g., Shift released before Ctrl in a Ctrl+Shift sequence).
        """
        pass

    @abstractmethod
    def hotkey(self, *keys: str, interval: float = 0.0, **kwargs: Any) -> None:
        """Perform a hotkey combination by pressing keys in sequence, then releasing in reverse.

        Args:
            *keys: Key names to press in order (e.g., 'ctrl', 'shift', 'c').
                The first keys are treated as modifiers, held down while the
                last key is pressed.
            interval: Delay in seconds between key down events (default 0.0).
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> keyboard.hotkey('ctrl', 'c')  # Copy
            >>> keyboard.hotkey('ctrl', 'shift', 't')  # Reopen closed tab
            >>> keyboard.hotkey('alt', 'f4')  # Close window (Windows/Linux)

        Note:
            Keys are pressed in the order given and released in reverse order:
            1. key_down('ctrl')
            2. key_down('shift')
            3. key_down('c')
            4. key_up('c')
            5. key_up('shift')
            6. key_up('ctrl')

            This ensures modifiers are active for the final key press.
        """
        pass

    @abstractmethod
    def codepoint(self, codepoint: int | str, **kwargs: Any) -> None:
        """Type a Unicode codepoint value.

        Directly injects a character without relying on keyboard layout mapping.
        Useful for typing special characters, emojis, or symbols that may not
        have dedicated keys on the current layout.

        Args:
            codepoint: Integer Unicode codepoint (e.g., 0x263A for '☺') or
                a string (e.g., 'U+263A' for '☺') to extract the codepoint from.
            **kwargs: Keyword arguments (internal usage).

        Example:
            >>> # Type a smiley emoji
            >>> keyboard.codepoint(0x1F642)  # 🙂
            >>> keyboard.codepoint('U+263A')  # ☺

        Note:
            Platform support varies.
            Not all applications handle Unicode input correctly.
        """
        pass


class AbstractScreenController(AbstractController):
    """Abstract base class for screen capture and image recognition.

    This controller manages all screen-related operations including:
    - Screenshot capture (full screen, specific regions, or windows)
    - Image search and localization on screen
    - Pixel color sampling
    - Screen dimension queries

    The controller coordinates with the screen OSAL for platform-specific
    capture mechanisms and provides high-level image processing utilities.

    Attributes:
        _osal: Platform-specific screen OSAL implementation (injected via __init__).

    Example:
        >>> from pyautogui2.controllers.manager import ControllerManager
        >>> manager = ControllerManager()
        >>> screen = manager.screen
        >>> screenshot = screen.screenshot()
        >>> screenshot.save('screenshot.png')
        >>> location = screen.locate_on_screen('button.png')

    Note:
        Image recognition features (locate*, pixel*) require the pillow and
        opencv-python libraries. Screenshot capture works without dependencies
        on most platforms via native APIs.
    """

    __abstractmethod_remove_decorators__ = {
        "locate": DECORATORS_TO_REMOVE,
        "locate_all": DECORATORS_TO_REMOVE,
        "locate_all_on_screen": DECORATORS_TO_REMOVE,
        "locate_center_on_screen": DECORATORS_TO_REMOVE,
        "locate_on_screen": DECORATORS_TO_REMOVE,
        "locate_on_window": DECORATORS_TO_REMOVE,
        "center": DECORATORS_TO_REMOVE,
        "pixel": DECORATORS_TO_REMOVE,
        "pixel_matches_color": DECORATORS_TO_REMOVE,
        "screenshot": DECORATORS_TO_REMOVE,
        "get_size_max": DECORATORS_TO_REMOVE,
        "get_size": DECORATORS_TO_REMOVE,
        "window": DECORATORS_TO_REMOVE,
        "get_active_window": DECORATORS_TO_REMOVE,
        "get_active_window_title": DECORATORS_TO_REMOVE,
        "get_windows_at": DECORATORS_TO_REMOVE,
        "get_windows_with_title": DECORATORS_TO_REMOVE,
        "get_all_windows": DECORATORS_TO_REMOVE,
        "get_all_titles": DECORATORS_TO_REMOVE,
    }


    @abstractmethod
    def locate(self,
               needle_image: Union[str, "Image.Image"],
               haystack_image: Union[str, "Image.Image"],
               **kwargs: Any) -> Optional[Box]:
        """Find an image within another image (off-screen template matching).

        Searches for a template image within a larger "haystack" image without
        capturing the screen. Useful for pre-processing or testing image
        recognition logic.

        Args:
            needle_image: Path to template image file or PIL Image object to find.
            haystack_image: Path to source image file or PIL Image object to search in.
            **kwargs: Options for template matching (confidence, grayscale, etc.).

        Returns:
            A Box-like object (left, top, width, height) of the first match,
            or None if not found.

        Example:
            >>> # Find button in a saved screenshot
            >>> location = screen.locate('button.png', 'screenshot.png')
            >>> if location:
            ...     print(f"Found at ({location.left}, {location.top})")

        Note:
            This is the off-screen variant of locate_on_screen(). It does not
            interact with the display but operates purely on image data.
        """
        pass

    @abstractmethod
    def locate_all(self,
                   needle_image: Union[str, "Image.Image"],
                   haystack_image: Union[str, "Image.Image"],
                   **kwargs: Any) -> Iterable[Box]:
        """Find all occurrences of an image within another image (off-screen).

        Args:
            needle_image: Path to template image file or PIL Image object to find.
            haystack_image: Path to source image file or PIL Image object to search in.
            **kwargs: Options for template matching (confidence, grayscale, etc.).

        Yields:
            Box-like objects for each match found, or empty iterator if no matches.

        Example:
            >>> # Find all icons in a UI screenshot
            >>> for location in screen.locate_all('icon.png', 'ui.png'):
            ...     print(f"Icon at ({location.left}, {location.top})")

        Note:
            Off-screen variant of locate_all_on_screen(). See locate() for details.
        """
        pass

    @abstractmethod
    def locate_all_on_screen(self,
                             image: Union[str, "Image.Image"],
                             **kwargs: Any) -> Iterable[Box]:
        """Find all occurrences of a template image on the screen.

        Args:
            image: Path to template image file or PIL Image object to find.
            **kwargs: See locate_on_screen() for supported options.

        Yields:
            Box-like objects representing each found occurrence, or empty
            iterator if no matches found.

        Example:
            >>> # Find all instances of an icon
            >>> for location in screen.locate_all_on_screen('icon.png'):
            ...     print(f"Found at ({location.left}, {location.top})")

        Note:
            This method may return overlapping matches if the template appears
            multiple times with slight shifts. Consider using confidence
            threshold to filter weak matches.
        """
        pass

    @abstractmethod
    def locate_center_on_screen(self,
                                image: Union[str, "Image.Image"],
                                **kwargs: Any) -> Optional[Point]:
        """Find the first occurrence of a template image and return its center point.

        Args:
            image: Path to template image file or PIL Image object to find.
            **kwargs: See locate_on_screen() for supported options.

        Returns:
            A Point-like object (or tuple) with attributes (x, y) representing
            the center of the found image, or None if not found.

        Example:
            >>> center = screen.locate_center_on_screen('button.png')
            >>> if center:
            ...     pointer.click(center.x, center.y)

        Note:
            Convenience wrapper around locate_on_screen. Equivalent to:
            location = locate_on_screen(image_path, **kwargs)
            center = (location.left + location.width // 2,
                     location.top + location.height // 2)
        """
        pass

    @abstractmethod
    def locate_on_screen(self,
                         image: Union[str, "Image.Image"],
                         min_search_time: int = 0,
                         **kwargs: Any) -> Optional[Box]:
        """Find the first occurrence of a template image on the screen.

        Args:
            image: Path to template image file or PIL Image object to find.
            min_search_time: Minimum time to search image on screen.
            **kwargs: Optional arguments for locate behavior:
                - confidence: float 0.0-1.0, minimum match confidence (default 0.9)
                - region: Tuple[int, int, int, int], search area (default full screen)
                - grayscale: bool, convert to grayscale before matching (faster)

        Returns:
            A Box-like object with attributes (left, top, width, height) representing
            the bounding box of the found image, or None if not found.

        Example:
            >>> location = screen.locate_on_screen('button.png')
            >>> if location:
            ...     print(f"Found at ({location.left}, {location.top})")
            ...     # Click the center of the button
            ...     center_x = location.left + location.width // 2
            ...     center_y = location.top + location.height // 2
            ...     pointer.click(center_x, center_y)

        Raises:
            FileNotFoundError: If image path does not exist.
            ImportError: If required image processing libraries are not installed.

        Note:
            Requires opencv-python or pyscreeze. This is a convenience wrapper
            around locate_all_on_screen that returns only the first match.
        """
        pass

    @abstractmethod
    def locate_on_window(self,
                         image: Union[str, "Image.Image"],
                         title: str,
                         **kwargs: Any) -> Optional[Box]:
        """Find a template image within a specific window and return screen coordinates.

        Activates the target window, captures its content area, and searches for
        the template image. Returns coordinates in absolute screen space, making
        it directly usable with pointer methods.

        Args:
            image: Path to the template image file or PIL Image object to find.
            title: Full or partial window title to identify the target window.
                Must match exactly one window.
            **kwargs: Options for template matching:
                - confidence: Matching threshold (0.0-1.0)
                - grayscale: Convert to grayscale before matching (bool)

        Returns:
            A Box-like object (left, top, width, height) with coordinates in
            absolute screen space, or None if the image is not found.

        Raises:
            PyAutoGUIException: If no window matches the title, or if multiple
                windows match (ambiguous).

        Example:
            >>> # Find and click a button in Firefox
            >>> location = screen.locate_on_window('refresh.png', 'Firefox')
            >>> if location:
            ...     center_x = location.left + location.width // 2
            ...     center_y = location.top + location.height // 2
            ...     pointer.click(center_x, center_y)  # Direct screen coords

        Note:
            - The window is automatically activated (brought to front) before capture
            - Title matching is case-sensitive and must be unique
            - For partial title matching with multiple results, use
            get_windows_with_title() and iterate manually
            - Coordinates are ready to use with pointer methods without conversion
        """
        pass

    @abstractmethod
    def center(self, region: Box, **kwargs: Any) -> Point:
        """Calculate the center point of a rectangular region.

        Args:
            region: A Box-like object (left, top, width, height) or tuple
                defining the rectangular area.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            A Point-like object (x, y) representing the center coordinates
            of the region.

        Example:
            >>> # Get center of a found image
            >>> location = screen.locate_on_screen('button.png')
            >>> if location:
            ...     center = screen.center(location)
            ...     pointer.click(center.x, center.y)
            >>>
            >>> # Calculate center of a custom region
            >>> center = screen.center((100, 100, 200, 150))
            >>> print(f"Center at ({center.x}, {center.y})")
            Center at (200, 175)

        Note:
            The calculation is: (left + width // 2, top + height // 2).
            This is a utility method often used in combination with locate*
            functions to click on found images.
        """
        pass

    @abstractmethod
    def pixel(self, x: int, y: int, **kwargs: Any) -> tuple[int, int, int]:
        """Get the RGB color of a single pixel at the specified coordinates.

        Args:
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            A tuple (red, green, blue) with values in range 0-255.

        Example:
            >>> color = screen.pixel(100, 200)
            >>> print(f"RGB: {color}")
            RGB: (255, 128, 0)

        Note:
            This is typically implemented by capturing a 1x1 screenshot and
            extracting the pixel value. For checking multiple pixels, it's
            more efficient to capture a region once and use PIL directly.
        """
        pass

    @abstractmethod
    def pixel_matches_color(self,
                            x: int, y: int,
                            expected_color: tuple[int, int, int],
                            tolerance: int = 0,
                            **kwargs: Any) -> bool:
        """Check if a pixel's color matches an expected RGB value within tolerance.

        Args:
            x: X coordinate of the pixel.
            y: Y coordinate of the pixel.
            expected_color: Tuple (red, green, blue) with values 0-255.
            tolerance: Maximum allowed difference per channel (default 0 = exact match).
                For example, tolerance=10 allows each RGB component to differ
                by up to 10 from the expected value.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            True if the pixel color matches within tolerance, False otherwise.

        Example:
            >>> # Check for exact white pixel
            >>> is_white = screen.pixel_matches_color(100, 200, (255, 255, 255))
            >>>
            >>> # Check for approximately red pixel
            >>> is_red = screen.pixel_matches_color(
            ...     100, 200, (255, 0, 0), tolerance=20
            ... )

        Note:
            Tolerance is applied per-channel using Manhattan distance:
            match = (abs(actual_r - expected_r) <= tolerance and
                     abs(actual_g - expected_g) <= tolerance and
                     abs(actual_b - expected_b) <= tolerance)
        """
        pass

    @abstractmethod
    def screenshot(
        self,
        image_path: Optional[str] = None,
        region: Optional[Box] = None,
        **kwargs: Any
    ) -> "Image.Image":
        """Capture a screenshot of the screen or a specific region.

        Args:
            image_path: Optional file path to save the screenshot (e.g., 'screenshot.png').
                If None, returns a PIL Image object without saving.
            region: Optional tuple (left, top, width, height) defining the
                capture area in screen coordinates. If None, captures the entire
                primary screen.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            A PIL Image object representing the captured screenshot.

        Example:
            >>> # Capture full screen
            >>> img = screen.screenshot()
            >>>
            >>> # Capture and save
            >>> screen.screenshot('full.png')
            >>>
            >>> # Capture specific region
            >>> region_img = screen.screenshot(region=(100, 100, 400, 300))

        Note:
            Requires the pillow library. On Linux/X11, may also use scrot or
            gnome-screenshot as fallback backends.
        """
        pass

    @abstractmethod
    def get_size_max(self, **kwargs: Any) -> Size:
        """Get the dimensions of the entire virtual desktop area.

        On multi-monitor setups, this includes all monitors arranged in their
        configured layout. The virtual desktop may include negative coordinates
        if monitors are positioned to the left/above the primary screen.

        Returns:
            A tuple (width, height) in pixels representing the bounding box
            of all monitors combined.

        Example:
            >>> # Setup: Primary 1920x1080, secondary 1920x1080 to the right
            >>> virtual_width, virtual_height = screen.get_size_max()
            >>> print(f"Virtual desktop: {virtual_width}x{virtual_height}")
            Virtual desktop: 3840x1080

        Note:
            The virtual size is used by the pointer controller to validate
            coordinates across the entire multi-monitor setup.
        """
        pass

    @abstractmethod
    def get_size(self, **kwargs: Any) -> Size:
        """Get the dimensions of the primary screen.

        Returns:
            A tuple (width, height) in pixels representing the primary monitor's
            resolution.

        Example:
            >>> width, height = screen.get_size()
            >>> print(f"Primary screen: {width}x{height}")
            Primary screen: 1920x1080

        Note:
            On multi-monitor setups, this returns only the primary monitor.
            Use get_size_max() for the total desktop area spanning all monitors.
        """
        pass

    @abstractmethod
    def window(self, handle: Any) -> Optional[Any]:
        """Get a Window object representing a specific window by handle.

        Args:
            handle: Platform-specific window handle/ID, or None.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            A Window object with methods like activate(), minimize(), close(), etc.,
            or None if no matching window found.

        Note:
            Requires platform-specific window management libraries (e.g., pygetwindow).
            Window objects provide high-level control over window state and geometry.
        """
        pass

    @abstractmethod
    def get_active_window(self, **kwargs: Any) -> Optional[Any]:
        """Get a Window object representing the currently focused window.

        Returns:
            A Window object for the active window, or None if unable to determine
            (e.g., desktop has focus, or platform does not support detection).

        Example:
            >>> win = screen.get_active_window()
            >>> if win:
            ...     print(f"Active window: {win.title}")
            ...     print(f"Position: ({win.left}, {win.top})")

        Note:
            "Active" typically means the window with keyboard focus. This may
            differ from the topmost visible window in some window managers.
        """
        pass

    @abstractmethod
    def get_active_window_title(self, **kwargs: Any) -> str:
        """Get the title of the currently focused window.

        Returns:
            String containing the window title, or None if no window has focus
            or the title cannot be determined.

        Example:
            >>> title = screen.get_active_window_title()
            >>> print(f"Active: {title}")
            Active: Mozilla Firefox

        Note:
            Convenience method equivalent to:
            win = get_active_window()
            return win.title if win else None
        """
        pass

    @abstractmethod
    def get_windows_at(self, x: int, y: int, **kwargs: Any) -> list:
        """Get all Window objects at a specific screen coordinate.

        Args:
            x: X coordinate in screen coordinates.
            y: Y coordinate in screen coordinates.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            List of Window objects at the specified point, ordered from topmost
            to bottommost. May be empty if only the desktop is at that location.

        Example:
            >>> # Check what windows are under the cursor
            >>> x, y = pointer.get_position()
            >>> windows = screen.get_windows_at(x, y)
            >>> for win in windows:
            ...     print(f"Window: {win.title}")

        Note:
            The order of windows depends on the Z-order (stacking order) managed
            by the window manager. Not all platforms support accurate Z-order queries.
        """
        pass

    @abstractmethod
    def get_windows_with_title(self, title: str, **kwargs: Any) -> list:
        """Get all Window objects whose titles contain a specific substring.

        Args:
            title: Substring to search for (case-insensitive by default).
            **kwargs: Keyword arguments (internal usage).

        Returns:
            List of matching Window objects, or empty list if none found.

        Example:
            >>> # Find all Chrome windows
            >>> chrome_windows = screen.get_windows_with_title('Chrome')
            >>> for win in chrome_windows:
            ...     print(f"Chrome window: {win.title}")

        Note:
            Search is typically case-insensitive and matches partial titles.
            For exact matching, check platform-specific kwargs or filter results.
        """
        pass

    @abstractmethod
    def get_all_windows(self, **kwargs: Any) -> list:
        """Get Window objects for all visible windows on the desktop.

        Returns:
            List of all Window objects currently visible (not minimized to taskbar),
            or empty list if enumeration fails.

        Example:
            >>> all_windows = screen.get_all_windows()
            >>> print(f"Found {len(all_windows)} windows")
            >>> for win in all_windows:
            ...     print(f"  - {win.title} ({win.width}x{win.height})")

        Note:
            May include system windows, taskbars, and other non-application windows
            depending on the platform and OSAL implementation. Consider filtering
            by title or class name if needed.
        """
        pass

    @abstractmethod
    def get_all_titles(self, **kwargs: Any) -> list:
        """Get the titles of all visible windows on the desktop.

        Returns:
            List of window title strings, or empty list if enumeration fails.

        Example:
            >>> titles = screen.get_all_titles()
            >>> for title in titles:
            ...     print(f"Window: {title}")

        Note:
            Convenience method equivalent to:
            [win.title for win in get_all_windows()]

            Some windows may have empty titles (system windows, splash screens).
        """
        pass


class AbstractDialogsController(AbstractController):
    """Abstract base class for modal dialog boxes.

    This controller manages platform-native dialog boxes for user interaction:
    - alert(): Display a message with an OK button
    - confirm(): Ask a yes/no question
    - prompt(): Request text input from the user
    - password(): Request password input (masked text)

    The controller delegates to the dialogs OSAL for platform-specific
    implementations (tkinter, PyMsgBox, zenity, AppleScript, etc.).

    Attributes:
        _osal: Platform-specific dialogs OSAL implementation (injected via __init__).

    Example:
        >>> from pyautogui2.controllers.manager import ControllerManager
        >>> manager = ControllerManager()
        >>> dialogs = manager.dialogs
        >>>
        >>> dialogs.alert("Operation complete!", title="Success")
        >>> choice = dialogs.confirm("Save changes?", buttons=("Save", "Discard"))
        >>> name = dialogs.prompt("Enter your name:")

    Note:
        All dialog methods block execution until the user responds or the
        dialog times out. The timeout parameter (if supported by the platform)
        allows automatic dismissal after a specified duration.
    """

    __abstractmethod_remove_decorators__ = {
        "alert": DECORATORS_TO_REMOVE,
        "confirm": DECORATORS_TO_REMOVE,
        "prompt": DECORATORS_TO_REMOVE,
        "password": DECORATORS_TO_REMOVE,
    }


    @abstractmethod
    def alert(self,
              text: str = '', title: str = '', button: str = 'OK',
              root: Optional[Any] = None, timeout: Optional[float] = None, **kwargs: Any) -> str:
        """Display a simple alert dialog with a message and single button.

        Args:
            text: The message to display in the dialog body (default empty string).
            title: The dialog window title (default empty string).
            button: The button label (default 'OK').
            root: Optional tkinter root window for dialog parenting (platform-specific).
            timeout: Optional timeout in seconds. If specified and supported by
                the platform, the dialog auto-dismisses after this duration.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            The button label that was clicked (typically the value of `button` parameter).

        Example:
            >>> dialogs.alert("Task completed successfully!", title="Success")
            'OK'
            >>>
            >>> # With custom button
            >>> dialogs.alert("Error occurred", button="Dismiss")
            'Dismiss'

        Note:
            Blocks until the user clicks the button or the dialog times out.
            On timeout, the return value is platform-dependent (may be None
            or the button label).
        """
        pass

    @abstractmethod
    def confirm(self,
                text: str = '', title: str = '', buttons: tuple[str, ...] = ('OK', 'Cancel'),
                root: Optional[Any] = None, timeout: Optional[float] = None, **kwargs: Any) -> Optional[str]:
        """Display a confirmation dialog with multiple choice buttons.

        Args:
            text: The question or message to display.
            title: The dialog window title.
            buttons: Tuple of button labels (default ('OK', 'Cancel')).
                Common patterns:
                - ('Yes', 'No')
                - ('Save', 'Discard', 'Cancel')
                - ('Retry', 'Abort')
            root: Optional tkinter root window for dialog parenting.
            timeout: Optional timeout in seconds.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            The label of the button that was clicked, or None if the dialog
            was closed without clicking a button (e.g., via X button or timeout).

        Example:
            >>> choice = dialogs.confirm(
            ...     "Save changes before closing?",
            ...     buttons=("Save", "Don't Save", "Cancel")
            ... )
            >>> if choice == "Save":
            ...     save_file()
            >>> elif choice == "Don't Save":
            ...     pass  # Discard changes
            >>> else:  # Cancel or None
            ...     return  # Abort close operation

        Note:
            The first button is typically the default (activated by Enter key).
            Platform conventions vary for button order and styling.
        """
        pass

    @abstractmethod
    def prompt(self,
               text: str = '', title: str = '', default: str = '',
               root: Optional[Any] = None, timeout: Optional[float] = None, **kwargs: Any) -> Optional[str]:
        """Display a text input dialog requesting user input.

        Args:
            text: The prompt message or label for the input field.
            title: The dialog window title.
            default: Default text pre-filled in the input field (default empty string).
            root: Optional tkinter root window for dialog parenting.
            timeout: Optional timeout in seconds.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            The user's input as a string, or None if the dialog was cancelled
            or timed out.

        Example:
            >>> name = dialogs.prompt("Enter your name:", default="User")
            >>> if name:
            ...     print(f"Hello, {name}!")
            ... else:
            ...     print("Input cancelled")

        Note:
            Empty string input is valid and distinct from None (cancellation).
            To distinguish between empty input and cancellation:
            - None: user clicked Cancel or closed dialog
            - "": user clicked OK with empty field
        """
        pass

    @abstractmethod
    def password(self,
                 text: str = '', title: str = '', default: str = '', mask: str = '*',
                 root: Optional[Any] = None, timeout: Optional[float] = None, **kwargs: Any) -> Optional[str]:
        """Display a password input dialog with masked text entry.

        Args:
            text: The prompt message or label for the password field.
            title: The dialog window title.
            default: Default password pre-filled (rarely used for security reasons).
            mask: Character to display instead of actual input (default '*').
                Common values: '*', '•', '' (some platforms support empty string
                for invisible text).
            root: Optional tkinter root window for dialog parenting.
            timeout: Optional timeout in seconds.
            **kwargs: Keyword arguments (internal usage).

        Returns:
            The user's password input as a string, or None if cancelled.

        Example:
            >>> password = dialogs.password("Enter password:")
            >>> if password:
            ...     authenticate(password)
            ... else:
            ...     print("Authentication cancelled")

        Security Note:
            The password is returned as plaintext and stored in memory. For
            production applications, use dedicated authentication libraries
            that handle secure password input and storage.

        Note:
            Masking is visual only; the actual input is not encrypted until
            returned to the caller. The dialog does not enforce password
            strength requirements.
        """
        pass

