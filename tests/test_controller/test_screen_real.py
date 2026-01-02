"""Real integration tests for ScreenController.
No mocks - requires actual graphical environment.
"""
import pytest

from pyautogui2.utils.types import Box


@pytest.mark.real
class TestScreenRealBasic:

    def test_basic(self, pyautogui_real):
        """Take real screenshot and locate a region within it."""
        screenshot = pyautogui_real.screen.screenshot()
        img_to_find = screenshot.crop((1, 1, 30, 40))
        location = pyautogui_real.screen.locate(img_to_find, screenshot)

        assert isinstance(location, Box)
        assert location.width == 29     # 30 - 1 (PIL convention)
        assert location.height == 39    # 40 - 1 (PIL convention)

        # Verify the found region actually matches pixel-for-pixel
        found_region = screenshot.crop((
            location.left,
            location.top,
            location.left + location.width,
            location.top + location.height,
        ))
        assert list(found_region.getdata()) == list(img_to_find.getdata())
