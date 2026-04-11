"""KdePointerPart - Desktop part for all Linux pointers."""
import configparser

from pathlib import Path
from typing import Optional

from .....utils.types import ButtonName
from ....abstract_cls import AbstractPointer


class KdePointerPart(AbstractPointer):
    """KDE desktop pointer configuration handler."""

    _cache_primary_button: Optional[ButtonName] = None

    @staticmethod
    def _is_left_handed() -> bool:
        path = Path.home() / ".config" / "kcminputrc"
        if not path.exists():
            return False
        cfg = configparser.RawConfigParser()
        cfg.read(path)
        return any(
            cfg.get(section, "LeftHanded", fallback="false").lower() == "true"
            for section in cfg.sections()
            if section.lower().startswith("libinput")
        )

    def get_primary_button(self) -> ButtonName:
        """Implementation Notes:
        - Reads ``~/.config/kcminputrc`` and checks all Libinput device sections.
        - Returns ``ButtonName.RIGHT`` if any device is configured as left-handed,
          ``ButtonName.LEFT`` otherwise.
        """
        if self._cache_primary_button is None:
            self._cache_primary_button = (
                ButtonName.RIGHT if self._is_left_handed() else ButtonName.LEFT
            )
        return self._cache_primary_button
