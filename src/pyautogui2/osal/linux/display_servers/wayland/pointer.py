"""WaylandPointerPart - Display server part for all Linux pointers."""
import time

from typing import Any, Optional

from .....utils.exceptions import PyAutoGUIException
from .....utils.lazy_import import lazy_import
from .....utils.types import ButtonName
from ....abstract_cls import AbstractPointer
from ._common import ensure_device_not_exists


class WaylandPointerPart(AbstractPointer):
    """Wayland display server pointer implementation using uinput kernel interface.

    Provides low-level pointer control via Linux uinput subsystem, which creates
    a virtual input device. Required on Wayland due to security restrictions that
    prevent direct pointer injection via display server protocols.

    Implementation Notes:
        - Uses python-uinput to create virtual mouse device.
        - Requires write access to /dev/uinput (typically root or input group).
        - Emits absolute position events (ABS_X/ABS_Y) not relative motion.
        - Button mapping respects desktop environment's left-handed configuration.
        - Position queries delegated to compositor-specific Parts (e.g., GNOME Shell).

    Dependencies:
        - python-uinput library.
        - /dev/uinput kernel interface access.
        - uinput kernel module loaded.

    Limitations:
        - Requires elevated permissions or group membership.
        - No built-in position query (compositor must provide).
    """

    _uinput = lazy_import("uinput")

    BUTTON_NAME_MAPPING = {
        ButtonName.LEFT:      None,      # set in setup_postinit()
        ButtonName.MIDDLE:    None,      # set in setup_postinit()
        ButtonName.RIGHT:     None,      # set in setup_postinit()
        ButtonName.PRIMARY:   None,      # set in setup_postinit()
        ButtonName.SECONDARY: None,      # set in setup_postinit()
    }

    _device_name = "pyautogui-virtual-pointer"

    def __init__(self, *args, **kwargs):
        """Initialize Wayland pointer without creating uinput device.

        Defers uinput device creation until setup_postinit() when screen
        dimensions are available (required for ABS_X/ABS_Y range setup).
        """
        super().__init__(*args, **kwargs)
        self._device: Optional[Any] = None
        self._first_move_done: bool = False

    def setup_postinit(self, *args, **kwargs):
        """Create virtual uinput mouse device with screen dimensions.

        Instantiates a virtual input device via /dev/uinput with capabilities
        for buttons, scroll wheels, and absolute positioning. Screen dimensions
        define the ABS_X/ABS_Y coordinate ranges.

        Args:
            *args: Ignored (compatibility with other implementations).
            **kwargs: Ignored (compatibility with other implementations).

        Implementation Notes:
            - Creates uinput.Device with BTN_LEFT/RIGHT/MIDDLE and scroll support.
            - Sets ABS_X range to (0, width) and ABS_Y to (0, height).
            - Updates BUTTON_NAME_MAPPING based on desktop's primary button.
            - Device persists until Python process exits.

        Raises:
            PermissionError: If no write access to /dev/uinput.
            OSError: If uinput kernel module not loaded.
        """
        super().setup_postinit(*args, **kwargs)

        screen_size_max = kwargs.get("screen_size_max")
        if screen_size_max is None:
            controller_manager = kwargs.get("controller_manager")
            if controller_manager is not None:
                screen_size_max = controller_manager.screen.get_size_max()
        if screen_size_max is None:
            raise ValueError("screen_size_max value is required")
        w, h = screen_size_max

        self.BUTTON_NAME_MAPPING[ButtonName.LEFT] = self._uinput.BTN_LEFT
        self.BUTTON_NAME_MAPPING[ButtonName.MIDDLE] = self._uinput.BTN_MIDDLE
        self.BUTTON_NAME_MAPPING[ButtonName.RIGHT] = self._uinput.BTN_RIGHT

        if self.get_primary_button() == ButtonName.LEFT:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
        else:
            self.BUTTON_NAME_MAPPING[ButtonName.PRIMARY] = self.BUTTON_NAME_MAPPING[ButtonName.RIGHT]
            self.BUTTON_NAME_MAPPING[ButtonName.SECONDARY] = self.BUTTON_NAME_MAPPING[ButtonName.LEFT]

        ensure_device_not_exists(self._device_name)

        self._device = self._uinput.Device([
            self._uinput.BTN_LEFT,
            self._uinput.BTN_RIGHT,
            self._uinput.BTN_MIDDLE,
            self._uinput.REL_WHEEL,
            self._uinput.REL_HWHEEL,
            self._uinput.ABS_X + (0, w - 1, 0, 0),
            self._uinput.ABS_Y + (0, h - 1, 0, 0),
        ], name=self._device_name)

        time.sleep(0.1)     # Let's give the OS some time to create the device

        self._first_move_done = False

    def teardown_postinit(self, *args: Any, **kwargs: Any) -> None:
        """Close the UInput virtual device if it was created."""
        super().teardown_postinit(*args, **kwargs)
        if self._device is not None:
            self._device.destroy()
            self._device = None

    def move_to(self, x: int, y: int, **_kwargs: Any) -> None:
        """Implementation Notes:
            - If it the first move, emits ABS_X/ABS_Y events with fake position (-1,-1)
                to force moving even on the initial device position (0,0).
            - Emits ABS_X and ABS_Y events via uinput device.
            - Uses syn=False on ABS_X to batch both axes in one SYN event.
            - Compositor handles actual cursor rendering.

        Raises:
            PyAutoGUIException: If x or y is None.
        """
        if x is None or y is None:
            raise PyAutoGUIException(f"Error: x/y values (x:{x}, y:{y}) are required' ")

        assert(self._device is not None), "Error: device is None"

        if not self._first_move_done:
            self._device.emit(self._uinput.ABS_X, -1, syn=False)
            self._device.emit(self._uinput.ABS_Y, -1, syn=False)
            self._first_move_done = True

        self._device.emit(self._uinput.ABS_X, x, syn=False)
        self._device.emit(self._uinput.ABS_Y, y)

    @AbstractPointer.button_decorator
    def button_down(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses BUTTON_NAME_MAPPING to resolve button to uinput constant.
        - Emits device.emit(BTN_xxx, 1) for press.
        - Respects desktop environment's left-handed configuration.
        - Decorated with @AbstractPointer.button_decorator.
        """
        assert(self._device is not None), "Error: device is None"
        self._device.emit(self.BUTTON_NAME_MAPPING[button], 1)

    @AbstractPointer.button_decorator
    def button_up(self, button: ButtonName = ButtonName.PRIMARY, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Uses BUTTON_NAME_MAPPING to resolve button to uinput constant.
        - Emits device.emit(BTN_xxx, 0) for release.
        - Respects desktop environment's left-handed configuration.
        - Decorated with @AbstractPointer.button_decorator.
        """
        assert(self._device is not None), "Error: device is None"
        self._device.emit(self.BUTTON_NAME_MAPPING[button], 0)

    def scroll(self, dx: Optional[int] = None, dy: Optional[int] = None, **_kwargs: Any) -> None:
        """Implementation Notes:
        - Vertical scrolling uses REL_WHEEL.
        - Horizontal scrolling uses REL_HWHEEL.
        - Both directions can be scrolled simultaneously.
        - Scroll amount is in wheel "clicks" (typically 120 units = 1 line).
        """
        assert(self._device is not None), "Error: device is None"
        if dy is not None and dy != 0:
            self._device.emit(self._uinput.REL_WHEEL, dy)
        if dx is not None and dx != 0:
            self._device.emit(self._uinput.REL_HWHEEL, dx)
