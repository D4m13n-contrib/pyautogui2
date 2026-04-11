"""Operating System Abstraction Layer (OSAL) - Abstract Interfaces.

This module defines the abstract base classes for platform-independent system
interactions. It provides a unified API for common operations across different
operating systems.

Architecture:
    - AbstractOSAL: Base class for all OSAL components
    - AbstractPointer: Mouse/touchpad control and monitoring
    - AbstractKeyboard: Keyboard input simulation and monitoring
    - AbstractScreen: Screen capture, window management, and image recognition
    - AbstractDialogs: Native dialog boxes for user interaction
    - OSAL: Aggregator dataclass combining all OSAL components

Each abstract class defines the interface contract that platform-specific
implementations must fulfill. Concrete implementations handle the low-level
details for each supported platform.

Note:
    These are abstract classes. Do not instantiate them directly.
    Use the appropriate platform-specific implementations instead.
"""
import functools

from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional, Union

from ..utils.abstract_cls import AbstractOSAL
from ..utils.decorators import DEFAULTS as DECORATORS_TO_REMOVE
from ..utils.exceptions import PyAutoGUIException
from ..utils.types import Box, ButtonName, Point, Size


if TYPE_CHECKING:
    from PIL import Image


class AbstractPointer(AbstractOSAL):
    """Platform-specific pointer/mouse operations interface.

    This abstract class defines the contract for low-level mouse/pointer control
    that must be implemented by each platform.

    Implementations handle:
    - Direct pointer movement (absolute coordinates)
    - Button press/release operations
    - Drag operations
    - Scrolling (horizontal and vertical)
    - Primary button detection
    - MouseInfo diagnostic tool

    These methods are called by PointerController, which adds cross-platform
    features like coordinate normalization, tweening, and failsafe checks.

    Attributes:
        BUTTON_NAME_MAPPING: Platform-specific mapping of ButtonName to native codes.
        _button_pressed: Internal state tracking for button press/release pairs.
    """

    __abstractmethod_remove_decorators__ = {
        "mouse_info": DECORATORS_TO_REMOVE,
        "get_primary_button": DECORATORS_TO_REMOVE,
        "get_pos": DECORATORS_TO_REMOVE,
    }

    BUTTON_NAME_MAPPING: dict[ButtonName, Any] = {
        ButtonName.LEFT:      None,
        ButtonName.MIDDLE:    None,
        ButtonName.RIGHT:     None,
        ButtonName.PRIMARY:   None,
        ButtonName.SECONDARY: None,
    }

    _button_pressed: dict[ButtonName, int] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._button_pressed = {}

    @abstractmethod
    def mouse_info(self) -> None:
        """Launch the MouseInfo diagnostic application.

        This application provides real-time mouse coordinate and color information,
        which can be useful when planning GUI automation tasks.

        Note:
            This function blocks until the MouseInfo application is closed.
        """
        pass

    @abstractmethod
    def get_primary_button(self) -> ButtonName:
        """Determine which physical button is configured as the primary button.

        Returns:
            ButtonName.LEFT or ButtonName.RIGHT depending on system configuration.

        Note:
            Used by PointerController to correctly map ButtonName.PRIMARY and
            ButtonName.SECONDARY to physical buttons based on user preferences
            (e.g., left-handed mouse mode).

        Example:
            >>> osal.pointer.get_primary_button()
            ButtonName.LEFT  # Normal mode
            >>> osal.pointer.get_primary_button()
            ButtonName.RIGHT  # Left-handed mode enabled
        """
        pass

    @abstractmethod
    def get_pos(self) -> Point:
        """Get the current pointer position in screen coordinates.

        Returns:
            Point namedtuple with x and y coordinates, where (0, 0) is the
            top-left corner of the primary screen.

        Raises:
            NotImplementedError: If the platform or display server does not
                support querying the pointer position (e.g., Wayland without
                a supported compositor).

        Note:
            Called by PointerController.get_position() without modification.
        """
        pass

    @abstractmethod
    def move_to(self, x: int, y: int, **kwargs: Any) -> None:
        """Move the pointer to absolute screen coordinates.

        Args:
            x: The x-axis coordinate to move to, where 0 is the left edge of the screen.
            y: The y-axis coordinate to move to, where 0 is the top edge of the screen.
            **kwargs: Internal options (e.g., _pause).

        Note:
            Coordinates should be in screen space. Controller handles normalization
            and tweening.
        """
        pass

    @abstractmethod
    def drag_to(self, x: int, y: int, button: ButtonName, **kwargs: Any) -> None:
        """Drag the pointer to absolute screen coordinates while holding a button.

        Args:
            x: The x-axis coordinate to drag to, where 0 is the left edge of the screen.
            y: The y-axis coordinate to drag to, where 0 is the top edge of the screen.
            button: The mouse button to hold during the drag operation.
            **kwargs: Internal options (e.g., _pause).

        Note:
            Implementation should press the button, move to target coordinates,
            then release the button.
        """
        pass

    @staticmethod
    def button_decorator(wrapped_function: Callable) -> Callable:
        """Decorator to prevent redundant button press/release operations.

        Wraps button_down and button_up functions to track button state and
        only execute the underlying platform call when the button state actually
        changes (e.g., pressing an already-pressed button is ignored).

        Args:
            wrapped_function: The button_down or button_up method to wrap.

        Returns:
            Wrapped function with state-tracking logic.

        Raises:
            PyAutoGUIException: If the button is not in BUTTON_NAME_MAPPING,
                or if the wrapped function is neither button_down nor button_up.

        Note:
            This decorator maintains an internal counter (_button_pressed) to
            handle nested press/release calls correctly.
        """
        @functools.wraps(wrapped_function)
        def wrapper(self: AbstractPointer, button: ButtonName, **kwargs: Any) -> None:
            if button not in self.BUTTON_NAME_MAPPING:
                raise PyAutoGUIException(f"Error: '{button}' ({type(button)}) "
                                        f"is not supported ({list(self.BUTTON_NAME_MAPPING.keys())})")

            if wrapped_function.__name__ == "button_down":
                exec_func = self._button_pressed.get(button, 0) == 0
                count = self._button_pressed.get(button, 0) + 1
            elif wrapped_function.__name__ == "button_up":
                count = self._button_pressed.get(button, 0) - 1
                exec_func = count <= 0
            else:       # pragma: no cover
                raise PyAutoGUIException(f"Error: the function '{wrapped_function.__name__}' "
                                        "should be a 'button_down' or a 'button_up' function")

            self._button_pressed[button] = count if count > 0 else 0
            if exec_func:
                return wrapped_function(self, button, **kwargs)     # type: ignore[no-any-return]

        return wrapper

    @abstractmethod
    def button_down(self, button: ButtonName, **kwargs: Any) -> None:
        """Press down a mouse button without releasing it.

        Args:
            button: The mouse button to press. Must be one of the ButtonName enum values.
            **kwargs: Internal options (e.g., _pause).

        Note:
            Must be paired with button_up() to complete a click action.
            The button_decorator ensures this method is only called when the
            button is not already pressed.
        """
        pass

    @abstractmethod
    def button_up(self, button: ButtonName, **kwargs: Any) -> None:
        """Release a previously pressed mouse button.

        Args:
            button: The mouse button to release. Must be one of the ButtonName enum values.
            **kwargs: Internal options (e.g., _pause).

        Note:
            Should match the button used in the corresponding button_down() call.
            The button_decorator ensures this method is only called when the
            button is actually pressed.
        """
        pass

    @abstractmethod
    def scroll(self, dx: Optional[int] = None, dy: Optional[int] = None, **kwargs: Any) -> None:
        """Scroll horizontally and/or vertically by the specified amounts.

        Args:
            dx: Horizontal scroll amount. Positive values scroll right,
                negative values scroll left.
            dy: Vertical scroll amount. Positive values scroll down,
                negative values scroll up.
            **kwargs: Internal options (e.g., _pause).

        Note:
            The actual pixel distance scrolled per unit is platform-dependent.
            Some platforms may use different scroll units (e.g., lines vs. pixels).
        """
        pass


class AbstractKeyboard(AbstractOSAL):
    """Platform-specific keyboard operations interface.

    This abstract class defines the contract for low-level keyboard control
    that must be implemented by each platform.

    Implementations handle:
    - Keyboard layout detection
    - Key mapping validation
    - Key press/release operations
    - Unicode codepoint input via context manager

    These methods are called by KeyboardController, which adds cross-platform
    features like key name normalization, text typing, and hotkey combinations.
    """

    __abstractmethod_remove_decorators__ = {
        "get_layout": DECORATORS_TO_REMOVE,
        "key_is_mapped": DECORATORS_TO_REMOVE,
    }


    @abstractmethod
    def get_layout(self) -> str:
        """Get the current keyboard layout type.

        Returns:
            String identifier for the keyboard layout family (e.g., "QWERTY",
            "AZERTY", "QWERTZ"). The returned value corresponds to a layout
            name from the KEYBOARD_LAYOUTS dictionary in utils/keyboard_layouts.py.

        Note:
            Used by KeyboardController to determine key mapping and support
            layout-specific automation.
        """
        pass

    @abstractmethod
    def key_is_mapped(self, key: str) -> bool:
        """Check if a key name is valid for the current keyboard layout.

        Args:
            key: The key name to validate (e.g., "a", "enter", "shift").

        Returns:
            True if the key is mapped and can be pressed, False otherwise.

        Note:
            Key names should be normalized before calling this method.
            Controller handles case-insensitivity and alias resolution.
        """
        pass

    @abstractmethod
    def key_down(self, key: str, **kwargs: Any) -> None:
        """Press down a keyboard key without releasing it.

        Args:
            key: The key name to press (e.g., "a", "enter", "shift").
            **kwargs: Internal options (e.g., _pause).

        Note:
            Must be paired with key_up() to complete a key press action.
            Used for holding modifier keys (ctrl, shift, alt) during hotkey sequences.
        """
        pass

    @abstractmethod
    def key_up(self, key: str, **kwargs: Any) -> None:
        """Release a previously pressed keyboard key.

        Args:
            key: The key name to release (e.g., "a", "enter", "shift").
            **kwargs: Internal options (e.g., _pause).

        Note:
            Should match the key used in the corresponding key_down() call.
            Releasing a key that was never pressed may have no effect or cause
            platform-specific behavior.
        """
        pass

    class AbstractCodepointCtx(ABC):
        """Context manager for typing Unicode codepoints directly.

        This abstract class defines a context manager interface that allows
        typing arbitrary Unicode characters by their codepoint value, bypassing
        normal keyboard layout limitations.

        Usage:
            with keyboard.codepoint_ctx() as ctx:
                ctx.type_codepoint_value("00E9")  # types 'é' (U+00E9)
                ctx.type_codepoint_value("1F600") # types '😀' (U+1F600)

        Note:
            The mechanism for entering codepoints is platform-specific.
            Implementations handle the native method for their respective platform.
        """

        def __init__(self, keyboard: "AbstractKeyboard"):
            """Initialize the codepoint context.

            Args:
                keyboard: Reference to the parent AbstractKeyboard instance,
                    used to access key_down/key_up methods.
            """
            self._keyboard = keyboard

        @abstractmethod
        def type_codepoint_value(self, hexstr: str) -> None:
            """Type a single Unicode character by its hexadecimal codepoint.

            Args:
                hexstr: Hexadecimal string representing the Unicode codepoint
                    (e.g., "00E9" for 'é', "1F600" for '😀'). Should NOT include
                    the "U+" prefix.

            Note:
                The hexstr should be 4-6 characters long for standard Unicode
                codepoints. Implementation details vary by platform.
            """
            pass

    @abstractmethod
    def codepoint_ctx(self) -> AbstractContextManager["AbstractKeyboard.AbstractCodepointCtx"]:
        """Create a context manager for typing Unicode codepoints.

        Returns:
            An instance of AbstractCodepointCtx (platform-specific subclass)
            that can be used as a context manager.

        Usage:
            with keyboard.codepoint_ctx() as ctx:
                ctx.type_codepoint_value("00E9")  # types 'é'

        Note:
            Platform implementations must return a concrete subclass of
            AbstractCodepointCtx that implements the platform-specific
            codepoint entry mechanism.
        """
        pass


class AbstractScreen(AbstractOSAL):
    """Platform-specific screen and window operations interface.

    This abstract class defines the contract for low-level screen/window control
    that must be implemented by each platform.

    Implementations handle:
    - Image location and matching on screen
    - Pixel color detection and validation
    - Screenshot capture
    - Screen size information
    - Window enumeration and management
    - Active window detection

    These methods are called by ScreenController, which adds cross-platform
    features like region validation, confidence thresholds, and caching.
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
        """Find the first occurrence of an image within another image.

        Args:
            needle_image: Image to find (path or PIL Image).
            haystack_image: Image to search in (path or PIL Image).
            **kwargs: Search options like grayscale, confidence, region.

        Returns:
            Box representing the bounding box (left, top, width, height) of the
            found image, or None if not found.

        Note:
            This performs image matching between two provided images, unlike
            locate_on_screen() which captures the screen automatically.
        """
        pass

    @abstractmethod
    def locate_all(self,
                   needle_image: Union[str, "Image.Image"],
                   haystack_image: Union[str, "Image.Image"],
                   **kwargs: Any) -> Generator[Box, None, None]:
        """Find all occurrences of an image within another image.

        Args:
            needle_image: Image to find (path or PIL Image).
            haystack_image: Image to search in (path or PIL Image).
            **kwargs: Search options like grayscale, confidence, region.

        Returns:
            Generator yielding Box objects for each match found.

        Note:
            This performs image matching between two provided images.
            Results are returned as a generator for memory efficiency.
        """
        pass

    @abstractmethod
    def locate_all_on_screen(self,
                             image: Union[str, "Image.Image"],
                             **kwargs: Any) -> Generator[Box, None, None]:
        """Find all occurrences of an image on the current screen.

        Args:
            image: Image to find (path or PIL Image).
            **kwargs: Search options like grayscale, confidence, region.

        Returns:
            Generator yielding Box objects for each match found.

        Note:
            Captures a screenshot and searches within it. Use this when you
            need to find multiple instances of an image on screen.
        """
        pass

    @abstractmethod
    def locate_center_on_screen(self,
                                image: Union[str, "Image.Image"],
                                **kwargs: Any) -> Optional[Point]:
        """Find an image on screen and return its center point.

        Args:
            image: Image to find (path or PIL Image).
            **kwargs: Search options like grayscale, confidence, region.

        Returns:
            Point (x, y) representing the center coordinates of the found image
            in screen-absolute coordinates, or None if not found.

        Note:
            Convenience method equivalent to center(locate_on_screen(needle)).
            Captures a screenshot, searches for the image, and returns the center
            point of the first match. This is the most common operation for
            click-based automation.
        """
        pass

    @abstractmethod
    def locate_on_screen(self,
                         image: Union[str, "Image.Image"],
                         min_search_time: int = 0,
                         **kwargs: Any) -> Optional[Box]:
        """Find the first occurrence of an image on the current screen.

        Args:
            image: Image to find (path or PIL Image).
            min_search_time: Minimum time to search image on screen.
            **kwargs: Search options like grayscale, confidence, region.

        Returns:
            Box with screen-absolute coordinates of the found image,
            or None if not found.

        Note:
            Captures a screenshot and searches within it. This is the most
            common method for GUI automation based on image recognition.
        """
        pass

    @abstractmethod
    def locate_on_window(self,
                         image: Union[str, "Image.Image"],
                         title: str,
                         **kwargs: Any) -> Optional[Box]:
        """Find an image within a specific window's visible area.

        Args:
            image: Image to find (path or PIL Image).
            title: Window title to search in.
            **kwargs: Search options like grayscale, confidence.

        Returns:
            Box with screen-absolute coordinates of the found image,
            or None if not found.

        Raises:
            Exception: If no window with the given title is found.
            Exception: If multiple windows with the same title exist.

        Note:
            Captures a screenshot of the specified window's region and
            searches within it. Returns screen-absolute coordinates.
        """
        pass

    @abstractmethod
    def center(self, coords: Box) -> Point:
        """Calculate the center point of a bounding box.

        Args:
            coords: Box (left, top, width, height) representing a bounding box.

        Returns:
            Point tuple (x, y) representing the center coordinates, calculated as:
            - x = left + width // 2
            - y = top + height // 2

        Example:
            >>> center(Box(10, 10, 6, 8))
            Point(x=13, y=14)
            >>> center(Box(10, 10, 8, 10))
            Point(x=14, y=15)

        Note:
            Uses integer division for pixel-perfect positioning.
        """
        pass

    @abstractmethod
    def pixel(self, x: int, y: int) -> tuple[int, int, int]:
        """Get the RGB color of a pixel at specific screen coordinates.

        Args:
            x: X coordinate (horizontal position).
            y: Y coordinate (vertical position).

        Returns:
            Tuple (r, g, b) where each component is an integer 0-255.

        Note:
            Captures the pixel color from the actual screen at the given
            absolute coordinates.
        """
        pass

    @abstractmethod
    def pixel_matches_color(self,
                            x: int, y: int,
                            expected_rgb: tuple[int, int, int],
                            tolerance: int = 0) -> bool:
        """Check if a pixel's color matches an expected RGB value within tolerance.

        Args:
            x: X coordinate (horizontal position).
            y: Y coordinate (vertical position).
            expected_rgb: Tuple (r, g, b) with expected color values 0-255.
            tolerance: RGB tolerance value (default: 0). Each RGB component
                can differ by up to this amount.

        Returns:
            True if the pixel color matches within tolerance, False otherwise.

        Note:
            Tolerance allows for slight variations due to anti-aliasing,
            compression artifacts, or rendering differences.
        """
        pass

    @abstractmethod
    def screenshot(self,
                   image_filename: Optional[str] = None,
                   region: Optional[Box] = None) -> "Image.Image":
        """Capture a screenshot of the screen or a specific region.

        Args:
            image_filename: Optional path to save the screenshot.
            region: Optional Box (left, top, width, height) to capture
                only a specific area.

        Returns:
            PIL Image object containing the captured screenshot.

        Note:
            If image_filename is provided, the screenshot is also saved to disk.
            If no region is specified, captures the entire primary screen.
        """
        pass

    @abstractmethod
    def get_size_max(self) -> Size:
        """Get the total virtual screen size across all monitors.

        Returns:
            Size tuple (width, height) representing the bounding box that
            encompasses all monitors combined.

        Note:
            For multi-monitor setups, this is the sum of all screen dimensions.
            For single monitors, this is equivalent to get_size().
        """
        pass

    @abstractmethod
    def get_size(self) -> Size:
        """Get the size of the primary screen.

        Returns:
            Size tuple (width, height) of the primary monitor in pixels.

        Note:
            In multi-monitor setups, returns only the primary screen dimensions.
            Use get_size_max() for the total virtual screen size.
        """
        pass

    @abstractmethod
    def window(self, handle: Any) -> Optional[Any]:
        """Create a window object from a platform-specific window handle.

        Args:
            handle: Platform-specific window handle/identifier.

        Returns:
            Platform-specific window object for manipulating the window
            (moving, resizing, activating, etc.), or None if handle is invalid.

        Note:
            The handle format varies by platform (HWND on Windows, XID on X11, etc.).
            Used to obtain a window object when you already have its identifier.
        """
        pass

    @abstractmethod
    def get_active_window(self) -> Optional[Any]:
        """Get the currently active (focused) window.

        Returns:
            Platform-specific window object representing the active window,
            or None if no window is active.

        Note:
            The active window is the one currently receiving keyboard input.
        """
        pass

    @abstractmethod
    def get_active_window_title(self) -> str:
        """Get the title of the currently active window.

        Returns:
            String containing the active window title, or empty string if
            no window is active.

        Note:
            Convenience method equivalent to get_active_window().title.
        """
        pass

    @abstractmethod
    def get_windows_at(self, x: int, y: int) -> list[Any]:
        """Get all windows at specific screen coordinates.

        Args:
            x: X screen coordinate.
            y: Y screen coordinate.

        Returns:
            List of platform-specific window objects at the given position,
            ordered from top to bottom in Z-order.

        Note:
            Multiple windows may overlap at the same coordinates. The first
            window in the list is the topmost (visible) one.
        """
        pass

    @abstractmethod
    def get_windows_with_title(self, title: str) -> list[Any]:
        """Get all windows whose title contains a search string (case-insensitive).

        Args:
            title: Substring to search for in window titles.

        Returns:
            List of platform-specific window objects with matching titles.

        Note:
            Performs case-insensitive substring matching. For example,
            "chrome" will match "Google Chrome", "Chrome Browser", etc.
        """
        pass

    @abstractmethod
    def get_all_windows(self) -> list[Any]:
        """Get all visible windows on the desktop.

        Returns:
            List of platform-specific window objects for all visible windows.

        Note:
            May exclude minimized windows or system windows depending on
            platform implementation.
        """
        pass

    @abstractmethod
    def get_all_titles(self) -> list[str]:
        """Get the titles of all visible windows.

        Returns:
            List of strings containing window titles.

        Note:
            Convenience method equivalent to [w.title for w in get_all_windows()].
        """
        pass


class AbstractDialogs(AbstractOSAL):
    """Abstract interface for displaying native dialog boxes.

    Provides methods to show various types of modal dialogs for user interaction,
    including alerts, confirmations, text input, and password prompts.

    All methods block execution until the user responds to the dialog.
    """

    __abstractmethod_remove_decorators__ = {
        "alert": DECORATORS_TO_REMOVE,
        "confirm": DECORATORS_TO_REMOVE,
        "prompt": DECORATORS_TO_REMOVE,
        "password": DECORATORS_TO_REMOVE,
    }

    @abstractmethod
    def alert(self,
              text: str,
              title: str = '',
              button: str = 'OK',
              root: Optional[Any] = None,
              timeout: Optional[float] = None) -> str:
        """Display an informational alert dialog with an OK button.

        Args:
            text: Main message text to display.
            title: Dialog window title (optional).
            button: Text for the OK button (optional, default varies by platform).
            root: Platform-specific root window (optional).
            timeout: Maximum time to wait for user response in seconds (optional).

        Returns:
            String containing the button text that was clicked (typically the
            button parameter value).

        Note:
            Blocks until the user clicks OK or closes the dialog.
            Commonly used for simple notifications or warnings.
        """
        pass

    @abstractmethod
    def confirm(self,
                text: str,
                title: str = '',
                buttons: tuple[str, ...] = ('OK', 'Cancel'),
                root: Optional[Any] = None,
                timeout: Optional[float] = None) -> Optional[str]:
        """Display a confirmation dialog with multiple choice buttons.

        Args:
            text: Main message text to display.
            title: Dialog window title (optional).
            buttons: Tuple of button labels (optional, default is platform-specific,
                typically ('OK', 'Cancel')).
            root: Platform-specific root window (optional).
            timeout: Maximum time to wait for user response in seconds (optional).

        Returns:
            String containing the text of the button that was clicked, or None
            if the dialog was closed without clicking a button.

        Note:
            Blocks until the user makes a choice or closes the dialog.
            Use this for yes/no questions or multi-choice confirmations.
        """
        pass

    @abstractmethod
    def prompt(self,
               text: str,
               title: str = '',
               default: str = '',
               root: Optional[Any] = None,
               timeout: Optional[float] = None) -> Optional[str]:
        """Display a text input dialog.

        Args:
            text: Main message/prompt text to display.
            title: Dialog window title (optional).
            default: Default text pre-filled in the input field (optional).
            root: Platform-specific root window (optional).
            timeout: Maximum time to wait for user response in seconds (optional).

        Returns:
            String containing the user's input text, or None if the dialog
            was cancelled or closed without input.

        Note:
            Blocks until the user submits or cancels the dialog.
            The input text is visible (not masked). For sensitive data,
            use password() instead.
        """
        pass

    @abstractmethod
    def password(self,
                 text: str,
                 title: str = '',
                 default: str = '',
                 mask: str = '*',
                 root: Optional[Any] = None,
                 timeout: Optional[float] = None) -> Optional[str]:
        """Display a password input dialog with masked text entry.

        Args:
            text: Main message/prompt text to display.
            title: Dialog window title (optional).
            default: Default text pre-filled in the input field (optional).
            mask: Character used to mask the input (optional, typically '*').
            root: Platform-specific root window (optional).
            timeout: Maximum time to wait for user response in seconds (optional).

        Returns:
            String containing the user's input text, or None if the dialog
            was cancelled or closed without input.

        Note:
            Blocks until the user submits or cancels the dialog.
            The input is masked for security (characters replaced with mask symbol).
            Despite the name, this can be used for any sensitive text input.
        """
        pass


@dataclass
class OSAL:
    """Container aggregating all OSAL component implementations.

    This dataclass groups the four core OSAL components (keyboard, pointer,
    screen, dialogs) into a single cohesive interface. Each attribute holds
    a platform-specific implementation of its respective abstract class.

    Attributes:
        keyboard: AbstractKeyboard implementation for keyboard operations.
        pointer: AbstractPointer implementation for mouse/touchpad control.
        screen: AbstractScreen implementation for screen interactions.
        dialogs: AbstractDialogs implementation for native dialog boxes.

    Note:
        This is a simple aggregator with no additional logic. It serves as
        a convenient container for passing all OSAL components together.
    """
    keyboard: AbstractKeyboard
    pointer:  AbstractPointer
    screen:   AbstractScreen
    dialogs:  AbstractDialogs
