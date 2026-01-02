"""GnomePointerPart - Desktop part for all Linux pointers."""
import subprocess

from typing import Optional

from .....utils.types import ButtonName
from ....abstract_cls import AbstractPointer


class GnomePointerPart(AbstractPointer):
    """GNOME desktop pointer configuration handler.

    Provides GNOME-specific pointer behavior, primarily detecting the user's
    left-handed mouse configuration. Queries GNOME settings via gsettings
    to determine which physical button should be treated as PRIMARY.

    Implementation Notes:
        - Caches primary button detection for performance.
        - Checks both touchpad and mouse settings via D-Bus.
        - Fallback chain: touchpad -> mouse -> LEFT (default).
        - Uses gsettings command-line tool for configuration queries.
    """

    _cache_primary_button: Optional[ButtonName] = None

    def _get_gsetting(self, schema: str, key: str) -> str:
        """Query a GNOME setting value via gsettings command.

        Executes the gsettings CLI tool to retrieve configuration values from
        GNOME's dconf database. Used internally to detect left-handed mode.

        Args:
            schema (str): GSettings schema name (e.g., "org.gnome.desktop.peripherals.mouse").
            key (str): Setting key within the schema (e.g., "left-handed").

        Returns:
            str: Raw setting value as string (e.g., "true", "false").

        Implementation Notes:
            - Runs subprocess: gsettings get <schema> <key>.
            - Returns stripped string output.
            - No type conversion performed (caller must interpret).

        Example:
            >>> self._get_gsetting("org.gnome.desktop.peripherals.mouse", "left-handed")
            'true'
        """
        try:
            return subprocess.check_output(
                ["gsettings", "get", schema, key],
                text=True
            ).strip().strip("'")
        except subprocess.CalledProcessError:
            return ""

    def get_primary_button(self) -> ButtonName:
        """Implementation Notes:
        - Checks touchpad settings first (org.gnome.desktop.peripherals.touchpad).
        - Falls back to mouse settings (org.gnome.desktop.peripherals.mouse).
        - Maps touchpad identifiers to button names via touchpad_bt_mapping.
        - Caches result in self._cache_primary_button.
        - Default is ButtonName.LEFT if no left-handed mode detected.
        """
        if self._cache_primary_button is not None:
            return self._cache_primary_button

        res = ButtonName.LEFT    # default => ButtonName.LEFT button is primary

        touchpad = self._get_gsetting("org.gnome.desktop.peripherals.touchpad", "left-handed")
        touchpad_bt_mapping = {
            "left": ButtonName.LEFT,
            "right": ButtonName.RIGHT,
        }

        if touchpad in touchpad_bt_mapping:
            res = touchpad_bt_mapping[touchpad]
        else:
            # fallback on mouse
            mouse_left_handed = self._get_gsetting("org.gnome.desktop.peripherals.mouse", "left-handed")
            if mouse_left_handed == "true":
                res = ButtonName.RIGHT   # left-handed mode => ButtonName.RIGHT button is primary

        self._cache_primary_button = res
        return res
