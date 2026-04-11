"""KwinBackend - Lightweight pydbus wrapper for KWin DBus interfaces."""

import logging
import re
import subprocess

from typing import Any

from .......utils.exceptions import PyAutoGUIException
from .......utils.types import Size
from .......utils.lazy_import import lazy_import


class KwinBackend:
    """Lightweight DBus client for KWin/KDE system interfaces.

    Unlike GnomeShellBackend, KWin exposes standard system DBus services
    that require no authentication token, no name ownership, and no custom
    extension. This backend is therefore stateless: each query opens a proxy
    on demand without any session lifecycle management.

    DBus services used:
        - ``org.kde.keyboard`` / ``/Layouts`` - active keyboard layout
        - ``org.kde.KScreen`` / ``/`` - connected monitor geometry

    Implementation Notes:
        - Uses ``pydbus`` (same as GnomeShellBackend) via ``lazy_import``.
        - No singleton: instantiate once per compositor part and reuse.
        - Failures raise ``RuntimeError`` with actionable messages.
    """

    _pydbus = lazy_import("pydbus")

    # --- DBus coordinates ---
    _KBD_BUS_NAME      = "org.kde.keyboard"
    _KBD_OBJECT_PATH   = "/Layouts"
    _KSCREEN_BUS_NAME  = "org.kde.KScreen"
    _KSCREEN_OBJECT_PATH = "/"

    # Matches monitor lines: "Virtual-1 connected primary 1280x800+0+0 ..."
    # or without "primary":  "HDMI-1 connected 1920x1080+1280+0 ..."
    _XRANDR_MONITOR_PATTERN = re.compile(
        r"^\S+\s+connected\s+(?:primary\s+)?(\d+)x(\d+)\+(\d+)\+(\d+)",
        re.MULTILINE,
    )
    _XRANDR_CURRENT_PATTERN = re.compile(r"current\s+(\d+)\s+x\s+(\d+)")

    def _session_bus(self) -> Any:
        """Return a pydbus SessionBus instance."""
        return self._pydbus.SessionBus()

    # ------------------------------------------------------------------
    # Keyboard
    # ------------------------------------------------------------------

    def get_keyboard_layout(self) -> str:
        """Return the short name of the currently active keyboard layout.

        Queries ``org.kde.keyboard`` via DBus to retrieve the active layout
        index, then maps it to its short name (e.g. ``"fr"``, ``"us"``).

        Returns:
            str: Short layout name of the active layout.

        Raises:
            RuntimeError: If the DBus service is unavailable or the layout
                list is empty.
        """
        try:
            proxy = self._session_bus().get(self._KBD_BUS_NAME, self._KBD_OBJECT_PATH)
            layouts: list[str] = proxy.getLayoutsList()
            active_index: int = proxy.getLayout()
            if not layouts:
                raise RuntimeError("KDE keyboard DBus returned an empty layout list.")
            return layouts[active_index][0]
        except Exception as e:
            raise RuntimeError(
                "Could not query keyboard layout from KDE DBus service "
                f"(bus: {self._KBD_BUS_NAME}). "
                "Make sure the KDE session is running. "
                f"Original error: {e}"
            ) from e

    # ------------------------------------------------------------------
    # Screen
    # ------------------------------------------------------------------

    def _xrandr_query(self) -> str:
        try:
            return subprocess.check_output(["xrandr", "--query"], text=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            raise PyAutoGUIException("xrandr is not available on this system.") from e

    def get_size(self) -> Size:
        output = self._xrandr_query()
        match = re.search(r"^\S+\s+connected\s+primary\s+(\d+)x(\d+)", output, re.MULTILINE)
        if not match:
            # No primary - fall back to first connected monitor
            match = re.search(r"^\S+\s+connected\s+(\d+)x(\d+)", output, re.MULTILINE)
        if not match:
            raise PyAutoGUIException("Could not determine primary screen size from xrandr.")
        return Size(int(match.group(1)), int(match.group(2)))

    def get_size_max(self) -> Size:
        output = self._xrandr_query()
        match = re.search(r"current\s+(\d+)\s+x\s+(\d+)", output)
        if not match:
            raise PyAutoGUIException("Could not parse xrandr output to determine total screen size.")
        return Size(int(match.group(1)), int(match.group(2)))
