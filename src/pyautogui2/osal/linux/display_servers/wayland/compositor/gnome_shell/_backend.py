"""Gnome Shell D-Bus Backend."""
import atexit
import contextlib
import logging
import os
import signal
import time

from typing import Any, Optional

from .......utils.lazy_import import lazy_import
from .......utils.singleton import Singleton


class GnomeShellBackend(metaclass=Singleton):
    """Singleton D-Bus backend for communicating with the GNOME Shell extension.

    This backend provides a Python interface to the custom GNOME Shell extension
    that exposes Wayland-restricted APIs (keyboard layout, pointer position, screen
    configuration) via D-Bus. The extension must be installed and enabled for this
    backend to function.

    Extension Location:
        osal/linux/display_servers/wayland/gnome_shell/extension/

    D-Bus Interface:
        - Bus Name: org.pyautogui.Wayland
        - Object Path: /org/pyautogui/Wayland
        - Bus Type: Session bus

    Implementation Notes:
        - Singleton pattern ensures single D-Bus connection across all components.
        - Lazy initialization of D-Bus proxy on first access.
        - Uses pydbus library for D-Bus communication (lazy imported).
        - Raises RuntimeError with helpful message if extension is not available.

    Attributes:
        BUS_NAME (str): D-Bus service name of the GNOME Shell extension.
        OBJECT_PATH (str): D-Bus object path of the extension interface.

    Raises:
        RuntimeError: If D-Bus connection fails (extension not installed/enabled).
    """

    BUS_NAME = "org.pyautogui.Wayland"
    OBJECT_PATH = "/org/pyautogui/Wayland"

    _pydbus = lazy_import("pydbus")

    def __init__(self):
        """Initialize the backend without establishing D-Bus connection.

        The actual D-Bus proxy connection is deferred until first access
        via the proxy property (lazy initialization pattern).

        Registers atexit cleanup to release the D-Bus name when the process exits.
        """
        self._uuid: Optional[str] = None
        self._bus_handle: Optional[Any] = None
        self._proxy: Optional[Any] = None
        self._name_owner: Optional[Any] = None

        atexit.register(self.cleanup)

    @property
    def _bus(self):
        """Get or create D-Bus session connection."""
        if self._bus_handle is None:
            self._bus_handle = self._pydbus.SessionBus()
        return self._bus_handle

    def cleanup(self):
        """Release D-Bus name on exit."""
        if self._bus_handle is not None and self._uuid is not None:
            try:
                dbus_proxy = self._bus_handle.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
                dbus_proxy.ReleaseName(self._uuid)
            except Exception as e:
                logging.error(f"ReleaseName failed: {e}")

        if self._name_owner is not None:
            with contextlib.suppress(Exception):
                self._name_owner.unown()
            self._name_owner = None

        if self._bus_handle is not None:
            with contextlib.suppress(Exception):
                self._bus_handle.close()
            self._bus_handle = None

        # Force property to recreate on next access
        if hasattr(self, "_proxy"):
            delattr(self, "_proxy")

        self._proxy = None
        self._uuid = None


    def _load_auth_token(self) -> str:
        """Load authentication token from Gnome Shell extension.

        Returns:
            str: The authentication token value read from the file.

        Raises:
            RuntimeError: If the token file is not found or if there is an error reading the file.
        """
        try:
            proxy = self._bus.get(self.BUS_NAME, object_path=self.OBJECT_PATH)
            token_path = proxy.GetAuthTokenPath()
            if not token_path:
                raise RuntimeError("Extension not installed")

            with open(token_path, encoding="utf-8") as f:
                token = f.read().strip()

            if not token:
                raise RuntimeError(f"Token file is empty: {token_path}")

            return token

        except FileNotFoundError as e:
            raise RuntimeError(
                f"Token file not found: {token_path}. "
                "Make sure the Gnome Shell extension is running."
            ) from e
        except PermissionError as e:
            raise RuntimeError(
                f"Cannot read token file: {token_path}. "
                "Check file permissions."
            ) from e
        except Exception as e:
            raise RuntimeError("Failed to load auth token") from e

    def _is_stale_registration(self) -> bool:
        """Check if current bus name registration is from a dead process.

        Returns:
            True if registration is stale (process doesn't exist anymore)
        """
        try:
            dbus_proxy = self._bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")

            owner_id = dbus_proxy.GetNameOwner(self._uuid)
            pid = dbus_proxy.GetConnectionUnixProcessID(owner_id)

            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return False  # Process exists, not stale
            except (ProcessLookupError, PermissionError):
                return True  # Process doesn't exist, it's stale

        except Exception:
            # If we can't determine, assume it's not stale (safe default)
            return False

    def _force_release_via_dbus(self) -> bool:
        """Force release of bus name using D-Bus direct API.

        Returns:
            True if release succeeded
        """
        try:
            dbus_proxy = self._bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")

            with contextlib.suppress(Exception):
                owner_id = dbus_proxy.GetNameOwner(self._uuid)
                pid = dbus_proxy.GetConnectionUnixProcessID(owner_id)

                with contextlib.suppress(ProcessLookupError, PermissionError):
                    os.kill(pid, signal.SIGTERM)

            # Wait for D-Bus
            time.sleep(0.2)

            try:
                dbus_proxy.GetNameOwner(self._uuid)
                return False
            except Exception:
                return True

        except Exception:
            return False

    def _create_proxy(self) -> Any:
        """Create D-Bus proxy connection.

        Returns:
            D-Bus proxy object

        Raises:
            RuntimeError: If connection fails
        """
        if self._proxy is not None:
            return self._proxy

        try:
            if self._uuid is None:
                self._uuid = f"pyautogui.{self._load_auth_token()}"

            if self._name_owner is None:
                try:
                    self._name_owner = self._bus.request_name(self._uuid)
                except RuntimeError as e:
                    # If we're already the owner, that's fine
                    if "already the owner" in str(e):
                        pass
                    else:
                        raise RuntimeError("Request name failed") from e
                self._proxy = self._bus.get(self.BUS_NAME, object_path=self.OBJECT_PATH)

            return self._proxy

        except Exception as e:
            error_msg = str(e).lower()

            # Check if it's a stale registration
            if "name already exists" in error_msg or "already in use" in error_msg:
                if self._is_stale_registration() and self._force_release_via_dbus():
                    # Reset state and retry
                    self._name_owner = None
                    return self._create_proxy()

                raise RuntimeError(
                    f"Could not release stale bus name {self._uuid}. "
                    "Try manually: dbus-send --session --type=method_call "
                    "--dest=org.freedesktop.DBus /org/freedesktop/DBus "
                    f"org.freedesktop.DBus.ReleaseName string:{self._uuid}"
                ) from e

            raise RuntimeError(
                "Could not connect to Wayland Gnome Shell extension via D-Bus. "
                "Make sure the extension is installed and enabled. "
                f"(bus name: {self.BUS_NAME}, uuid: {self._uuid}, error: {e})"
            ) from e

    @property
    def proxy(self) -> Any:
        """Get D-Bus proxy.

        Returns:
            D-Bus proxy object

        Raises:
            RuntimeError: If connection fails
        """
        return self._create_proxy()

    def get_keyboard_layout(self) -> str:
        """Retrieve the current keyboard layout from GNOME Shell.

        Queries the active keyboard layout (e.g., 'us', 'fr', 'de') from
        GNOME Shell's input source manager via the extension.

        Returns:
            str: Current keyboard layout identifier (ISO 639-1 language code
                or X11 layout name, e.g., 'us', 'fr', 'gb', 'dvorak').

        Implementation Notes:
            - Calls GetKeyboardLayout() D-Bus method on the extension.
            - Used by KeyboardController to adapt key mapping to layout.
            - Layout changes in GNOME settings are immediately reflected.

        Example:
            >>> backend.get_keyboard_layout()
            'us'
        """
        result: str = self.proxy.GetKeyboardLayout()
        return result

    def get_pointer_position(self) -> tuple[int, int]:
        """Retrieve the current pointer (mouse cursor) position from GNOME Shell.

        Queries the global cursor coordinates from GNOME Shell's pointer tracker.
        On Wayland, applications cannot directly query pointer position due to
        security restrictions, so this must go through the compositor.

        Returns:
            tuple[int, int]: Current cursor position as (x, y) coordinates in
                pixels, relative to the top-left corner of the virtual screen.

        Implementation Notes:
            - Calls GetPosition() D-Bus method on the extension.
            - Required for Wayland compatibility (no direct pointer queries).
            - Used by PointerController.position() getter.
            - Works across all monitors in multi-monitor setups.

        Example:
            >>> backend.get_pointer_position()
            (1523, 847)
        """
        result: tuple[int, int] = self.proxy.GetPosition()
        return result

    def get_screen_outputs(self) -> str:
        """Retrieve all monitor output configurations from GNOME Shell.

        Queries the list of all connected monitors with their positions and
        dimensions from GNOME Shell's monitor manager. On Wayland, screen
        information is restricted and must be obtained from the compositor.

        Returns:
            str: JSON string containing an array of monitor configurations.
                Each monitor object includes:
                - x (int): Horizontal position in virtual screen space.
                - y (int): Vertical position in virtual screen space.
                - width (int): Monitor width in pixels.
                - height (int): Monitor height in pixels.

        Implementation Notes:
            - Calls GetOutputs() D-Bus method on the extension.
            - Returns raw JSON string (caller must parse with json.loads()).
            - Used by ScreenController.get_size_max() for multi-monitor support.
            - Updates automatically when monitors are connected/disconnected.

        Example:
            >>> backend.get_screen_outputs()
            '[{"x":0,"y":0,"width":1920,"height":1080},
              {"x":1920,"y":0,"width":1920,"height":1080}]'
        """
        result: str = self.proxy.GetOutputs()
        return result
