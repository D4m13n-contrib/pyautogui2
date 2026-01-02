"""GnomeShellScreenPart - Wayland part for all Linux screens.
"""
import json

from .......utils.types import Size
from ......abstract_cls import AbstractScreen


class GnomeShellScreenPart(AbstractScreen):
    """GNOME Shell on Wayland screen implementation.

    Provides GNOME Shell-specific implementations for screen dimension queries
    using D-Bus communication with the custom GNOME Shell extension
    'gnome-wayland@pyautogui.org'. All other screen operations are inherited
    from LinuxScreenPart.

    The extension must be installed and enabled for this backend to function.
    Installation is handled by the installer script in this directory.

    Implementation Notes:
        - Communicates with GNOME Shell via D-Bus (org.gnome.Shell.PyAutoGUI)
        - Removes default decorators from size methods for direct D-Bus queries
        - Lazy loads backend to avoid D-Bus connection overhead
        - Supports multi-monitor setups through GetOutputs() D-Bus method

    Attributes:
        __abstractmethod_remove_decorators__: Configuration to bypass default
            decorators on size-related methods for direct D-Bus queries.

    See Also:
        - _backend.py: GnomeShellBackend D-Bus interface
        - installer.py: Extension installation script
        - gnome-wayland@pyautogui.org/: GNOME Shell extension source
    """

    def __init__(self, *args, **kwargs):
        """Initialize the GNOME Shell screen backend.

        Note:
            The actual D-Bus backend is lazy-loaded on first use to avoid
            connection overhead during initialization.
        """
        super().__init__(*args, **kwargs)
        self._backend = None

    @property
    def backend(self):
        """Lazy-load and return the GNOME Shell D-Bus backend.

        Returns:
            GnomeShellBackend: D-Bus interface for communicating with the
                GNOME Shell extension.

        Note:
            The backend is instantiated only once and cached for subsequent calls.
        """
        if self._backend is None:
            from ._backend import GnomeShellBackend
            self._backend = GnomeShellBackend()
        return self._backend

    def _get_all_monitors(self):
        """Retrieve all monitor configurations from GNOME Shell.

        Queries the GNOME Shell extension via D-Bus to get detailed information
        about all connected monitors/outputs.

        Returns:
            list[dict]: List of monitor configurations, each containing:
                - x (int): Horizontal position in virtual screen space
                - y (int): Vertical position in virtual screen space
                - width (int): Monitor width in pixels
                - height (int): Monitor height in pixels
                - (potentially other monitor properties)

        Implementation Notes:
            - Calls GetOutputs() D-Bus method via the backend
            - Returns parsed JSON response as Python list
            - Used internally by get_size_max() for multi-monitor calculations

        Example Response:
            [
                {"x": 0, "y": 0, "width": 1920, "height": 1080},
                {"x": 1920, "y": 0, "width": 1920, "height": 1080}
            ]
        """
        outputs_json = self.backend.get_screen_outputs()
        return json.loads(outputs_json)

    def get_size(self) -> Size:
        """Get the size of the primary GNOME Shell screen.

        Queries the GNOME Shell extension via D-Bus to retrieve the dimensions
        of the primary monitor.

        Returns:
            Size: Named tuple (width, height) in pixels of the primary screen.

        Implementation Notes:
            - Calls GetPrimaryScreenSize() D-Bus method
            - Returns dimensions of the monitor marked as primary in GNOME settings
            - Works on Wayland where direct screen queries are restricted
        """
        all_monitors = self._get_all_monitors()
        if not all_monitors:
            return Size(0, 0)
        return Size(all_monitors[0]["width"], all_monitors[0]["height"])

    def get_size_max(self) -> Size:
        """Get the maximum screen size across all GNOME Shell monitors.

        Queries all monitor outputs via D-Bus and calculates the bounding box
        that encompasses all screens. Useful for multi-monitor setups.

        Returns:
            Size: Named tuple (width, height) representing the maximum extent
                of the virtual desktop in pixels.

        Implementation Notes:
            - Calls GetOutputs() D-Bus method to get all monitor configurations
            - Parses JSON response containing position and size of each output
            - Calculates max(x + width) and max(y + height) across all outputs
            - Returns the dimensions of the combined virtual screen space

        Example:
            Two monitors: [1920x1080 at (0,0)] and [1920x1080 at (1920,0)]
            Returns: Size(width=3840, height=1080)
        """
        all_monitors = self._get_all_monitors()
        if not all_monitors:
            return Size(0, 0)
        screen_width_max = max(m["x"] + m["width"] for m in all_monitors)
        screen_height_max = max(m["y"] + m["height"] for m in all_monitors)
        return Size(int(screen_width_max), int(screen_height_max))
