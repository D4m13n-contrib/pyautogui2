"""PointerController for PyAutoGUI.

See AbstractPointerController for documentation.
"""

import time

from functools import singledispatchmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Union

from more_itertools import mark_ends
from PIL import Image

from ..osal.abstract_cls import AbstractPointer
from ..utils.decorators.failsafe import FailsafeManager
from ..utils.exceptions import ImageNotFoundException, PyAutoGUIException
from ..utils.tweening import TweeningManager
from ..utils.types import (
    ArgCoordX,
    ArgCoordY,
    Box,
    ButtonName,
    Coord,
    Coords,
    CoordsNormalized,
    Point,
)
from .abstract_cls import AbstractPointerController


if TYPE_CHECKING:
    from .screen import ScreenController


class PointerController(AbstractPointerController):
    """Concrete implementation of pointer/mouse controller.

    This implementation adds movement smoothing and duration normalization logic
    on top of OSAL delegation. It handles sub-threshold durations by converting
    them to instant movements for better performance.
    See AbstractPointerController for detailed method documentation.

    Class Attributes:
        MINIMUM_DURATION: Threshold (0.1s) below which movements are instant.
        MINIMUM_SLEEP: Minimum sleep interval (0.05s) for smooth animations.

    Implementation Notes:
        - Durations below MINIMUM_DURATION are rounded to 0.0 for instant moves.
        - Screenshot logging is added to some operations (see __abstractmethod_decorators__).
        - Platform-specific sleep timing may need adjustment (see TODO).
    """

    # In seconds. Any duration less than this is rounded to 0.0 to instantly move
    # the mouse.
    MINIMUM_DURATION: float = 0.1
    # If sleep_amount is less than MINIMUM_DURATION, time.sleep() will be a no-op and the mouse cursor moves there instantly.
    # TODO: This value should vary with the platform. http://stackoverflow.com/q/1133857
    MINIMUM_SLEEP: float = 0.05

    def __init__(self, osal: AbstractPointer, *args, **kwargs):
        """Store OSAL backend reference for pointer operations.

        Args:
            osal: Platform-specific pointer OSAL implementation.
            *args: List arguments (internal usage).
            **kwargs: Keyword arguments (internal usage).

        Raises:
            ValueError: If osal is not an AbstractPointer subclass.

        Implementation Notes:
            - Validates OSAL type at instantiation.
            - _screen_controller initialized to None (set in setup_postinit).
        """
        super().__init__(*args, **kwargs)

        if not isinstance(osal, AbstractPointer):
            raise PyAutoGUIException(f"Error: '{osal}' should be a subclass of AbstractPointer")
        self._osal: AbstractPointer = osal

        self._screen_controller: Optional[ScreenController] = None

    def setup_postinit(self, *args, **kwargs):
        """Complete OSAL initialization and configure failsafe manager.

        Args:
            *args: List arguments.
            **kwargs: Keyword arguments.

        Implementation-Specific Behavior:
            1. Delegates setup to OSAL backend (osal.setup_postinit).
            2. Registers OSAL's get_pos() with FailsafeManager for corner detection.
            3. Stores reference to ScreenController for coordinate normalization.

        Side Effects:
            - FailsafeManager().register_get_position() called globally (affects all pointer ops).
            - self._screen_controller bound (enables image-based coordinate resolution).
        """
        super().setup_postinit(*args, **kwargs)
        self._osal.setup_postinit(*args, **kwargs)

        FailsafeManager().register_get_position(self._osal.get_pos)
        self._screen_controller = kwargs["controller_manager"].screen

    def teardown_postinit(self, *args, **kwargs):
        self._osal.teardown_postinit(*args, **kwargs)
        super().teardown_postinit(*args, **kwargs)


    # --------------------------------------------------
    # Normalization functions
    # --------------------------------------------------
    @singledispatchmethod
    def _normalize_coords(self, bad_type, x: Optional[Coord] = None, y: Optional[Coord] = None) -> CoordsNormalized:
        """Normalize various coordinate input formats to CoordsNormalized tuple.

        This is a singledispatch method that routes different input types to
        specialized handlers. Supports:
        - Separate x/y integers,
        - Coords namedtuple,
        - (x, y) tuple,
        - Image filename (locates on screen).

        Args:
            bad_type: Unhandled type (triggers TypeError in fallback).
            x: X coordinate (used only in int/int dispatch).
            y: Y coordinate (used only in int/int dispatch).

        Returns:
            CoordsNormalized: Tuple of (x: int, y: int) in absolute screen coordinates.

        Raises:
            TypeError: If input type has no registered handler.
            ImageNotFoundException: If image file not found on screen.
            ValueError: If coordinates are None or out of screen bounds.

        Implementation Notes:
            - This base method is the fallback (always raises TypeError).
            - Actual logic in @_.register overloads below.
            - Image-based coordinates use self._screen_controller.locate().

        Example:
            >>> # These all route to different implementations:
            >>> self._normalize_coords(100, 200)          # int/int handler
            >>> self._normalize_coords(Coords(100, 200))  # Coords handler
            >>> self._normalize_coords((100, 200))        # tuple handler
            >>> self._normalize_coords("icon.png")        # image handler
        """
        if bad_type is not None:
            raise TypeError(f"Unsupported type for coords: {type(bad_type)}")

        # Get position only if needed
        if x is None or y is None:
            cx, cy = self.get_position()
            if x is None:
                x = cx
            if y is None:
                y = cy

        return int(x), int(y)

    @_normalize_coords.register
    def _(self, coord_x: int, coord_y: int) -> CoordsNormalized:
        """Handle separate x/y integer coordinates.

        Args:
            coord_x: Absolute X position in pixels.
            coord_y: Absolute Y position in pixels.

        Returns:
            CoordsNormalized: Validated (x, y) tuple.

        Implementation Notes:
            - No bounds checking (allows negative/off-screen for edge cases).
            - Used by public API methods (move_to, click, etc.).
        """
        return self._normalize_coords(None, coord_x, coord_y)

    @_normalize_coords.register
    def _(self, coord_x: float, coord_y: float) -> CoordsNormalized:
        """Handle separate x/y float coordinates.

        Args:
            coord_x: Absolute X position in pixels.
            coord_y: Absolute Y position in pixels.

        Returns:
            CoordsNormalized: Rounded and validated coordinates.

        Implementation Notes:
            - Recursively calls _normalize_coords(None, int, int) for validation.
        """
        return self._normalize_coords(None, round(coord_x), round(coord_y))

    @_normalize_coords.register
    def _(self, coords: Coords, _ = None) -> CoordsNormalized:
        """Handle Coords namedtuple input.

        Args:
            coords: Coords object with .x and .y attributes.
            _: Ignored (exists for dispatch signature compatibility).

        Returns:
            CoordsNormalized: Extracted (coords.x, coords.y).

        Implementation Notes:
            - Recursively calls _normalize_coords(None, int, int) for validation.
        """
        return self._normalize_coords(None, coords.x, coords.y)

    @_normalize_coords.register
    def _(self, coords: tuple, _ = None) -> CoordsNormalized:     # tuple <=> Coords or CoordsRect
        """Handle (x, y) or (x, y, w, h) tuple input.

        Args:
            coords: 2-element tuple (x, y) or 4-element tuple (x, y, w, h).
            _: Ignored (exists for dispatch signature compatibility).

        Returns:
            CoordsNormalized: Unpacked and validated coordinates.

        Raises:
            ValueError: If tuple length != 2 and != 4.

        Implementation Notes:
            - 2-tuple: uses coordinates directly.
            - 4-tuple: extracts center via ScreenController.
            - Recursively calls _normalize_coords(None, int, int).
        """
        if len(coords) == 2:
            pt = Point(*coords)
        elif len(coords) == 4:
            assert(self._screen_controller is not None), "Screen controller not initialized"
            box = Box(*coords)
            pt = self._screen_controller.center(box)
        else:
            raise ValueError(f"Expected 2-tuple (x, y) or 4-tuple (x, y, w, h), got {len(coords)} elements")

        return self._normalize_coords(None, pt.x, pt.y)

    @_normalize_coords.register(str)
    @_normalize_coords.register(Path)
    @_normalize_coords.register(Image.Image)
    def _(self, image_file: Union[str, Path, "Image.Image"], _ = None) -> CoordsNormalized:
        """Locate image on screen and return its center coordinates.

        Args:
            image_file: Path or string path to image file (PNG/JPEG/BMP), or Image object.
            _: Ignored (exists for dispatch signature compatibility).

        Returns:
            CoordsNormalized: Center coordinates of located image region.

        Raises:
            ImageNotFoundException: If image not found on screen.

        Implementation Notes:
            - Delegates to self._screen_controller.locate_center_on_screen().
            - Requires _screen_controller set in setup_postinit.

        Example:
            >>> # Click center of "submit_button.png":
            >>> self.click("submit_button.png")
        """
        assert(self._screen_controller is not None), "Screen controller not initialized"
        if isinstance(image_file, Path):
            image_file = str(image_file)
        location = self._screen_controller.locate_center_on_screen(image_file)
        if location is None:
            raise ImageNotFoundException(f"'{image_file}' not found on screen")
        return self._normalize_coords(None, location.x, location.y)

    def _normalize_button(self, button: Optional[ButtonName | str]) -> ButtonName:
        """Normalize button name to ButtonName enum.

        Args:
            button: Mouse button as ButtonName enum or lowercase string
                    ('left', 'right', 'middle', 'primary', 'secondary').
                    If button is None, consider ButtonName.PRIMARY.

        Returns:
            ButtonName: Validated enum value (ButtonName.LEFT/RIGHT/MIDDLE).

        Raises:
            ValueError: If button string is not 'left'/'right'/'middle'/'primary'/'secondary'.
            TypeError: If button is neither ButtonName nor str.

        Implementation Notes:
            - Case-insensitive string matching.
            - Passes through ButtonName enums unchanged.
            - Used by click/press/release methods.

        Example:
            >>> self._normalize_button('left')        # -> ButtonName.LEFT
            >>> self._normalize_button(ButtonName.RIGHT)  # -> ButtonName.RIGHT
            >>> self._normalize_button('MIDDLE')      # -> ButtonName.MIDDLE
            >>> self._normalize_button('invalid')     # -> ValueError
        """
        if button is None:
            return ButtonName(ButtonName.PRIMARY)
        try:
            if isinstance(button, str):
                button = button.lower()
            return ButtonName(button)
        except ValueError as e:
            raise PyAutoGUIException(f"Invalid button: '{button}'") from e


    # --------------------------------------------------
    # Info functions
    # --------------------------------------------------
    def mouse_info(self) -> None:
        """Implementation Notes:
        - Delegates to self._osal.mouse_info().
        """
        return self._osal.mouse_info()

    def get_position(self, **_kwargs: Any) -> Point:
        """Implementation Notes:
        - Delegates to self._osal.get_pos().
        - Returns current cursor position at time of call.
        - No caching (always queries OS).
        """
        x, y = self._osal.get_pos()
        return Point(int(x), int(y))

    def on_screen(self,
                  x: Optional[ArgCoordX] = None,
                  y: Optional[ArgCoordY] = None,
                  **_kwargs: Any) -> bool:
        """Implementation Notes:
        - Normalizes coordinates via self._normalize_coords().
        - Uses self._screen_controller.get_size().
        - Requires _screen_controller set in setup_postinit.
        """
        x, y = self._normalize_coords(x, y)
        assert(self._screen_controller is not None), "Screen controller not initialized"
        w, h = self._screen_controller.get_size_max()
        result: bool = (0 <= x < w and 0 <= y < h)
        return result


    # --------------------------------------------------
    # Move functions
    # --------------------------------------------------
    def _get_real_target_pos(self,
                             start_pos: Point,
                             target_x: Optional[int] = None, target_y: Optional[int] = None,
                             offset_x: Optional[int] = None, offset_y: Optional[int] = None):
        """Get the real target position (see _move_drag())."""
        offset_x = int(offset_x or 0)
        offset_y = int(offset_y or 0)

        if target_x is None and target_y is None and \
            offset_x == 0 and offset_y == 0:
            return  # Special case for no mouse movement at all.

        x = int(target_x) if target_x is not None else int(start_pos.x)
        y = int(target_y) if target_y is not None else int(start_pos.y)

        x += offset_x
        y += offset_y

        assert(self._screen_controller is not None), "Screen controller not initialized"
        screen_size = self._screen_controller.get_size_max()

        # Make sure x and y are within the screen bounds.
        x = max(0, min(x, screen_size.width - 1))
        y = max(0, min(y, screen_size.height - 1))

        return Point(x, y)

    def _move_compute_step_count(self, duration):
        """Compute step count with duration (see _move_drag())."""
        step_count: int = 0

        if duration > self.MINIMUM_DURATION:
            step_count = int(duration / self.MINIMUM_SLEEP)

        return step_count

    def _move_build_step_points(self, start_pos: Point, target_pos: Point, step_count: int, tween: Optional[str] = None):
        """Build all step points with tweening (see _move_drag())."""
        tween_func = TweeningManager()(tween or 'linear')

        steps: list[Point] = [
            Point(*TweeningManager().get_point_on_line(start_pos.x, start_pos.y,
                                                       target_pos.x, target_pos.y,
                                                       tween_func(n / step_count))
            )
            for n in range(step_count)
        ]

        # Making sure the last position is the target destination.
        steps.append(target_pos)

        return steps

    def _move_drag_all_steps(self, steps: list[Point], sleep_amount: float, button: Optional[ButtonName] = None):
        """Move/Drag at all pre-computed positions (see _move_drag())."""
        for step_pos in steps:
            tween_pos = Point(round(step_pos.x), round(step_pos.y))

            # Do a fail-safe check to see if the user moved the mouse to a fail-safe position, but not if the mouse cursor
            # moved there as a result of this function. (Just because tween_x and tween_y aren't in a fail-safe position
            # doesn't mean the user couldn't have moved the mouse cursor to a fail-safe position.)
            if tween_pos not in FailsafeManager().trigger_points:
                FailsafeManager().check()

            if button is None:
                self._osal.move_to(tween_pos.x, tween_pos.y)
            else:
                self._osal.drag_to(tween_pos.x, tween_pos.y, button)

            if sleep_amount > 0.0:
                time.sleep(sleep_amount)

        # Do a fail-safe check on the last position to be sure the next call not raises it.
        FailsafeManager().check()

    def _move_drag(self,
                   target_x: Optional[int] = None, target_y: Optional[int] = None,
                   offset_x: Optional[int] = None, offset_y: Optional[int] = None,
                   duration: float = 0.0, tween: Optional[str] = None,
                   button: Optional[ButtonName] = None):
        """Internal method implementing mouse movement and drag operations.

        This is the core implementation for all mouse movement (move_to, move_rel)
        and drag operations (drag_to, drag_rel). Handles coordinate computation,
        failsafe checks, button press/release, and tweened animation.

        Args:
            target_x: Absolute X coordinate (mutually exclusive with offset_x).
            target_y: Absolute Y coordinate (mutually exclusive with offset_y).
            offset_x: Relative X offset from current position.
            offset_y: Relative Y offset from current position.
            duration: Movement duration in seconds (0 = instant).
            tween: Easing function for animation (default: linear).
            button: Mouse button to hold during movement (None = move only).

        Implementation Notes:
            Coordinate Resolution:
                - If target_x/y provided: use as absolute coordinates.
                - If offset_x/y provided: compute from current position.
                - Single-value variants (e.g., x only) get current for other axis.

            Movement Logic:
                - duration=0: Instant teleport to target.
                - duration>0: Animated movement with tween function.
                - Applies tween(progress) for each intermediate step.

            Button Handling:
                - button=None: Pure movement (no buttons pressed).
                - button specified: Press before move, release after.
                - Used for drag operations.

            Failsafe:
                - Can raise FailSafeException.
                - Check fail-safe on target position at the end of moving

            OSAL Delegation:
                - Delegates to self._osal.move_to() for actual movement.
                - Animation loop managed here, not in OSAL.

            Performance:
                - Caches current position to avoid redundant OSAL calls.
                - Computes step count based on duration and distance.
                - Uses time.sleep() for animation timing.
        """
        if duration < 0.0:
            raise PyAutoGUIException("duration must be non-negative")

        if tween is not None and tween not in TweeningManager().tweens:
            raise PyAutoGUIException(f"Unknown tweening name '{tween}'")

        start_pos = self.get_position()

        real_target_pos = self._get_real_target_pos(start_pos, target_x, target_y, offset_x, offset_y)
        if real_target_pos is None:
            # Nothing to move
            return

        step_count = self._move_compute_step_count(duration)

        steps = self._move_build_step_points(start_pos, real_target_pos, step_count, tween)

        if len(steps) == 1 and steps[0] == start_pos:
            # Pointer already at the target position => nothing to move
            return

        sleep_amount = duration / len(steps) if len(steps) > 1 else self.MINIMUM_SLEEP

        self._move_drag_all_steps(steps, sleep_amount, button)

        # Check target position is reached
        last_pos = self.get_position()
        if last_pos != real_target_pos:
            raise PyAutoGUIException(
                f"Error: failed to move from {start_pos} to {real_target_pos}, reached {last_pos}."
            )

    def move_to(self,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                duration: float = 0.0, tween: Optional[str] = None,
                **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes coordinates via self._normalize_coords().
        """
        x, y = self._normalize_coords(x, y)
        self._move_drag(target_x=x, target_y=y, duration=duration, tween=tween)

    def move_rel(self,
                 offset_x: Optional[int | tuple | list] = None, offset_y: Optional[int] = None,
                 duration: float = 0.0, tween: Optional[str] = None,
                 **_kwargs: Any) -> None:
        """Implementation Notes:
        - Relative to position at time of call (not queued).
        """
        if isinstance(offset_x, (tuple, list)):
            off_x, off_y = offset_x[0], offset_x[1]
        else:
            off_x, off_y = offset_x, offset_y
        self._move_drag(offset_x=off_x, offset_y=off_y, duration=duration, tween=tween)


    # --------------------------------------------------
    # Button functions
    # --------------------------------------------------
    def button_down(self,
                    x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                    button: Optional[ButtonName] = None,
                    **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes button name via self._normalize_button().
        - Delegates to self._osal.button_down().
        """
        button = self._normalize_button(button)
        x, y = self._normalize_coords(x, y)

        self._move_drag(target_x=x, target_y=y)
        self._osal.button_down(button)

    def button_up(self,
                  x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                  button: Optional[ButtonName] = None,
                  **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes button name via self._normalize_button().
        - Delegates to self._osal.button_up().
        """
        button = self._normalize_button(button)
        x, y = self._normalize_coords(x, y)

        self._move_drag(target_x=x, target_y=y)
        self._osal.button_up(button)


    # --------------------------------------------------
    # Click functions
    # --------------------------------------------------
    def click(self,
              x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
              button: Optional[ButtonName] = None,
              clicks: int = 1, interval: float = 0.0,
              duration: float = 0.0, tween: Optional[str] = None,
              **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes button name via self._normalize_button().
        - Delegates to self._osal.button_down() + self._osal.button_up().
        - interval applies between clicks, not before first click.
        """
        if clicks < 1:
            raise PyAutoGUIException(f"clicks value must be >= 1 ({clicks})")

        if interval < 0.0:
            raise PyAutoGUIException(f"interval must be non-negative ({interval})")

        button = self._normalize_button(button)
        x, y = self._normalize_coords(x, y)

        for _, is_last, _ in mark_ends(range(clicks)):
            # Move the pointer to the x, y coordinate before each clicks
            # to grant position between each clicks
            self._move_drag(target_x=x, target_y=y, duration=duration, tween=tween)

            self._osal.button_down(button)
            self._osal.button_up(button)

            if not is_last and interval > 0.0:
                time.sleep(interval)

    def left_click(self,
                   x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                   interval: float = 0.0,
                   duration: float = 0.0, tween: Optional[str] = None,
                   **_kwargs: Any) -> None:
        self.click(x, y, ButtonName.LEFT, 1, interval, duration, tween, _log_screenshot=False, _pause=False)

    def right_click(self,
                    x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                    interval: float = 0.0,
                    duration: float = 0.0, tween: Optional[str] = None,
                    **_kwargs: Any) -> None:
        self.click(x, y, ButtonName.RIGHT, 1, interval, duration, tween, _log_screenshot=False, _pause=False)

    def middle_click(self,
                     x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                     interval: float = 0.0,
                     duration: float = 0.0, tween: Optional[str] = None,
                     **_kwargs: Any) -> None:
        self.click(x, y, ButtonName.MIDDLE, 1, interval, duration, tween, _log_screenshot=False, _pause=False)

    def double_click(self,
                     x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                     interval: float = 0.0,
                     button: Optional[ButtonName] = None,
                     duration: float = 0.0, tween: Optional[str] = None,
                     **_kwargs: Any) -> None:
        """Implementation Notes:
        - Enforce interval to be > 0.0 to avoid OS considering only one click.
        """
        interval = interval if interval > 0.0 else 0.1
        self.click(x, y, button, 2, interval, duration, tween, _log_screenshot=False, _pause=False)

    def triple_click(self,
                     x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                     interval: float = 0.0,
                     button: Optional[ButtonName] = None,
                     duration: float = 0.0, tween: Optional[str] = None,
                     **_kwargs: Any) -> None:
        """Implementation Notes:
        - Enforce interval to be > 0.0 to avoid OS considering only one click.
        """
        interval = interval if interval > 0.0 else 0.1
        self.click(x, y, button, 3, interval, duration, tween, _log_screenshot=False, _pause=False)


    # --------------------------------------------------
    # Drag functions
    # --------------------------------------------------
    def drag_to(self,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                button: Optional[ButtonName] = None,
                duration: float = 0.0, tween: Optional[str] = None,
                **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes coordinates via self._normalize_coords().
        - Normalizes button via self._normalize_button().
        """
        x, y = self._normalize_coords(x, y)
        button = self._normalize_button(button)

        self._osal.button_down(button)
        # Use try/finally to ensure button_up() always call after button_down()
        try:
            self._move_drag(target_x=x, target_y=y, duration=duration, tween=tween, button=button)
        finally:
            self._osal.button_up(button)

    def drag_rel(self,
                 offset_x: Optional[int | tuple | list] = None, offset_y: Optional[int] = None,
                 button: Optional[ButtonName] = None,
                 duration: float = 0.0, tween: Optional[str] = None,
                 **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes button via self._normalize_button().
        """
        if isinstance(offset_x, (tuple, list)):
            off_x, off_y = offset_x[0], offset_x[1]
        else:
            off_x, off_y = offset_x, offset_y
        button = self._normalize_button(button)

        self._osal.button_down(button)
        # Use try/finally to ensure button_up() always call after button_down()
        try:
            self._move_drag(offset_x=off_x, offset_y=off_y, duration=duration, tween=tween, button=button)
        finally:
            self._osal.button_up(button)


    # --------------------------------------------------
    # Scroll functions
    # --------------------------------------------------
    def hscroll(self,
                clicks: int,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes coordinates via self._normalize_coords().
        """
        if clicks == 0:
            return
        x, y = self._normalize_coords(x, y)
        self._move_drag(target_x=x, target_y=y)
        self._osal.scroll(dx=int(clicks))

    def vscroll(self,
                clicks: int,
                x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
                **_kwargs: Any) -> None:
        """Implementation Notes:
        - Normalizes coordinates via self._normalize_coords().
        """
        if clicks == 0:
            return
        x, y = self._normalize_coords(x, y)
        self._move_drag(target_x=x, target_y=y)
        self._osal.scroll(dy=int(clicks))

    def scroll(self,
               clicks: int,
               x: Optional[ArgCoordX] = None, y: Optional[ArgCoordY] = None,
               **_kwargs: Any) -> None:
        """Implementation Notes:
        - Delegates to self.vscroll().
        """
        self.vscroll(clicks=clicks, x=x, y=y, _log_screenshot=False, _pause=False)
