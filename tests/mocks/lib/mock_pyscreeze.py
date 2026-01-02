"""Lightweight Mock of the pyscreeze module used by WindowsScreen tests.
Designed to be simple and safe for Linux test runs.
"""
from typing import Optional
from unittest.mock import MagicMock

from PIL import Image


class MockPyscreeze:
    """Simplified replacement for pyscreeze used in tests."""

    class ImageNotFoundException(Exception):
        """Simulated exception type from pyscreeze."""
        pass

    def __init__(self) -> None:
        # When tests call setup_postinit, this flag should be set True
        self.USE_IMAGE_NOT_FOUND_EXCEPTION = False

        self.locate = MagicMock(return_value=(10, 10, 50, 50))
        self.locateAll = MagicMock(return_value=iter([(10, 10, 50, 50), (20, 20, 30, 30)]))
        self.locateAllOnScreen = MagicMock(return_value=[(10, 10, 50, 50), (20, 20, 30, 30)])
        self.locateCenterOnScreen = MagicMock(return_value=(35, 35))
        self.locateOnScreen = MagicMock(return_value=(10, 10, 50, 50))
        self.locateOnWindow = MagicMock(return_value=(10, 10, 50, 50))
        self.center = MagicMock(side_effect=lambda box: ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2))
        self.pixel = MagicMock(return_value=(123, 45, 67))
        self.pixelMatchesColor = MagicMock(return_value=True)
        self.screenshot = MagicMock(side_effect=self._screenshot_impl)

    def _screenshot_impl(self,
                         _image_path: Optional[str] = None,
                         region: Optional[tuple] = None,
                         **_kwargs) -> "Image":
        """Implementation of screenshot - returns dummy black image.

        Args:
            region: Optional region to capture (Box with x, y, width, height).
                   If None, captures full screen.

        Returns:
            PIL Image object (black dummy image).
        """
        from PIL import Image

        if region:
            return Image.new("RGB", (region[0], region[1]), color="black")
        return Image.new("RGB", (1920, 1080), color="black")

    def reset_mock(self, **kwargs):
        self.locate.reset_mock(**kwargs)
        self.locateAll.reset_mock(**kwargs)
        self.locateAllOnScreen.reset_mock(**kwargs)
        self.locateCenterOnScreen.reset_mock(**kwargs)
        self.locateOnScreen.reset_mock(**kwargs)
        self.locateOnWindow.reset_mock(**kwargs)
        self.center.reset_mock(**kwargs)
        self.pixel.reset_mock(**kwargs)
        self.pixelMatchesColor.reset_mock(**kwargs)
        self.screenshot.reset_mock(**kwargs)
