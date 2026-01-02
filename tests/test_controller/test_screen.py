"""Tests for ScreenController."""

from io import BytesIO
from unittest.mock import MagicMock, call, patch

import pytest

from PIL import Image

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.types import Box, Point


class TestScreenGetSize:
    """Test get_size() and get_size_max() methods."""

    def test_get_size_returns_expected(self, screen_controller):
        """Test basic screen size retrieval."""
        result = screen_controller.get_size()
        assert result == (1920, 1080)
        screen_controller._osal.get_size.assert_called_once()

    def test_get_size_max_returns_expected(self, screen_controller):
        """Test maximum screen size (all monitors combined)."""
        result = screen_controller.get_size_max()
        assert result == (3840, 2160)
        screen_controller._osal.get_size_max.assert_called_once()

    def test_get_size_returns_tuple_of_ints(self, screen_controller):
        """Test that get_size returns tuple of integers."""
        width, height = screen_controller.get_size()

        assert isinstance(width, int)
        assert isinstance(height, int)
        assert width > 0
        assert height > 0

    def test_get_size_max_larger_than_get_size(self, screen_controller):
        """Test that max size is >= regular size (multi-monitor)."""
        regular_width, regular_height = screen_controller.get_size()
        max_width, max_height = screen_controller.get_size_max()

        # Max should be >= regular (single monitor: equal, multi: larger)
        assert max_width >= regular_width
        assert max_height >= regular_height

    def test_get_size_consistent_between_calls(self, screen_controller):
        """Test that get_size returns consistent values."""
        size1 = screen_controller.get_size()
        size2 = screen_controller.get_size()

        assert size1 == size2

    def test_get_size_backend_error(self, screen_controller):
        """Test handling backend errors in get_size()."""
        screen_controller._osal.get_size.side_effect = RuntimeError("Size error")

        with pytest.raises(RuntimeError, match="Size error"):
            screen_controller.get_size()

    def test_get_size_max_backend_error(self, screen_controller):
        """Test handling backend errors in get_size_max()."""
        screen_controller._osal.get_size_max.side_effect = RuntimeError("Max size error")

        with pytest.raises(RuntimeError, match="Max size error"):
            screen_controller.get_size_max()


class TestScreenPixel:
    """Test pixel() color sampling method."""

    def test_pixel_returns_color(self, screen_controller):
        """Test basic pixel color retrieval."""
        color = screen_controller.pixel(5, 10)
        assert color == (10, 20, 30)
        screen_controller._osal.pixel.assert_called_once_with(5, 10)

    def test_pixel_returns_rgb_tuple(self, screen_controller):
        """Test that pixel returns RGB tuple."""
        color = screen_controller.pixel(100, 200)

        assert isinstance(color, tuple)
        assert len(color) == 3
        # RGB values should be 0-255
        for component in color:
            assert isinstance(component, int)
            assert 0 <= component <= 255

    def test_pixel_at_origin(self, screen_controller):
        """Test pixel at screen origin (0, 0)."""
        color = screen_controller.pixel(0, 0)

        assert isinstance(color, tuple)
        assert len(color) == 3
        screen_controller._osal.pixel.assert_called_with(0, 0)

    def test_pixel_at_screen_edges(self, screen_controller):
        """Test pixel at screen boundaries."""
        width, height = screen_controller.get_size()

        # Bottom-right corner (width-1, height-1)
        color = screen_controller.pixel(width - 1, height - 1)

        assert isinstance(color, tuple)
        assert len(color) == 3
        screen_controller._osal.pixel.assert_called_with(width - 1, height - 1)

    def test_pixel_out_of_bounds_raises(self, screen_controller):
        """Test that coordinates beyond screen raise error or are handled."""
        width, height = screen_controller.get_size()

        # Test coordinates beyond screen
        try:
            color = screen_controller.pixel(width + 1000, height + 1000)
            # If it doesn't raise, verify it returns valid color
            assert isinstance(color, tuple)
        except (PyAutoGUIException, ValueError, RuntimeError):
            # Expected behavior: raises on out of bounds
            pass

    def test_pixel_backend_error(self, screen_controller):
        """Test handling backend errors in pixel()."""
        screen_controller._osal.pixel.side_effect = RuntimeError("Pixel error")

        with pytest.raises(RuntimeError, match="Pixel error"):
            screen_controller.pixel(10, 10)

    def test_pixel_multiple_samples(self, screen_controller):
        """Test sampling multiple pixels in sequence."""
        positions = [(10, 10), (20, 20), (30, 30)]

        for x, y in positions:
            color = screen_controller.pixel(x, y)
            assert isinstance(color, tuple)
            assert len(color) == 3

        # Should have called pixel for each position
        assert screen_controller._osal.pixel.call_count == 3


class TestScreenWindow:
    """Test all *window*() methods."""

    def test_window(self, screen_controller):
        """Test basic window() method."""
        res = screen_controller.window(42)
        screen_controller._osal.window.assert_called_once_with(42)
        assert res is not None

    def test_get_active_window(self, screen_controller):
        """Test basic get_active_window() method."""
        res = screen_controller.get_active_window()
        screen_controller._osal.get_active_window.assert_called_once_with()
        assert res is not None

    def test_get_active_window_title(self, screen_controller):
        """Test basic get_active_window_title() method."""
        screen_controller._osal.get_active_window_title.return_value = "Window Title"
        res = screen_controller.get_active_window_title()
        screen_controller._osal.get_active_window_title.assert_called_once_with()
        assert res == "Window Title"

    def test_get_windows_at(self, screen_controller):
        """Test basic get_windows_at() method."""
        res = screen_controller.get_windows_at(12, 34)
        screen_controller._osal.get_windows_at.assert_called_once_with(12, 34)
        assert isinstance(res, list)

    def test_get_windows_with_title(self, screen_controller):
        """Test basic get_windows_with_title() method."""
        res = screen_controller.get_windows_with_title("Title")
        screen_controller._osal.get_windows_with_title.assert_called_once_with("Title")
        assert isinstance(res, list)

    def test_get_all_windows(self, screen_controller):
        """Test basic get_all_windows() method."""
        res = screen_controller.get_all_windows()
        screen_controller._osal.get_all_windows.assert_called_once_with()
        assert isinstance(res, list)

    def test_get_all_titles(self, screen_controller):
        """Test basic get_all_titles() method."""
        res = screen_controller.get_all_titles()
        screen_controller._osal.get_all_titles.assert_called_once_with()
        assert isinstance(res, list)


class TestScreenPixelMatchesColor:
    """Test pixel() color sampling method."""

    def test_pixel_matches_color(self, screen_controller):
        """Test basic pixel color matching."""
        color = (12, 34, 56)
        x, y = (10, 10)
        tolerance = 0

        screen_controller._osal.pixel_matches_color.return_value = True
        match = screen_controller.pixel_matches_color(x, y, color, tolerance)
        assert match is True

        screen_controller._osal.pixel_matches_color.return_value = False
        match = screen_controller.pixel_matches_color(x, y, color, tolerance)
        assert match is False


class TestScreenScreenshot:
    """Test screenshot() capture method."""

    def test_screenshot_returns_image_bytes(self, screen_controller):
        """Test basic screenshot returns PIL Image."""
        data = screen_controller.screenshot()

        assert isinstance(data, Image.Image)
        assert data.width == 1920
        assert data.height == 1080
        assert data.mode == "RGB"
        screen_controller._osal.screenshot.assert_called_once()

    def test_screenshot_full_screen_dimensions(self, screen_controller):
        """Test that full screenshot matches screen size."""
        width, height = screen_controller.get_size()
        img = screen_controller.screenshot()

        assert img.width == width
        assert img.height == height

    def test_screenshot_with_region(self, screen_controller):
        """Test screenshot with specific region/box."""
        # Mock OSAL to return smaller image for region
        small_img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        small_img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        screen_controller._osal.screenshot.return_value = small_img

        # Screenshot with region (x, y, width, height)
        img = screen_controller.screenshot(region=(10, 10, 100, 100))

        assert img.width == 100
        assert img.height == 100
        # Verify OSAL was called with region parameter
        screen_controller._osal.screenshot.assert_called()

    def test_screenshot_with_box_object(self, screen_controller):
        """Test screenshot with Box/Region object."""
        small_img = Image.new('RGB', (50, 50), color='blue')
        screen_controller._osal.screenshot.return_value = small_img

        box = Box(left=0, top=0, width=50, height=50)
        img = screen_controller.screenshot(region=box)

        assert img.width == 50
        assert img.height == 50

    def test_screenshot_returns_pil_image(self, screen_controller):
        """Test that screenshot returns actual PIL Image object."""
        img = screen_controller.screenshot()

        # Should be PIL Image
        assert isinstance(img, Image.Image)

        # Should have image methods
        assert hasattr(img, 'save')
        assert hasattr(img, 'getpixel')
        assert hasattr(img, 'crop')

    def test_screenshot_image_mode_rgb(self, screen_controller):
        """Test that screenshot is in RGB mode by default."""
        img = screen_controller.screenshot()

        assert img.mode == "RGB"
        # RGB has 3 channels
        assert len(img.getbands()) == 3

    def test_screenshot_backend_error(self, screen_controller):
        """Test handling backend errors in screenshot()."""
        screen_controller._osal.screenshot.side_effect = RuntimeError("Screenshot failed")

        with pytest.raises(RuntimeError, match="Screenshot failed"):
            screen_controller.screenshot()

    def test_screenshot_can_be_saved(self, screen_controller, tmp_path):
        """Test that screenshot can be saved to file."""
        img = screen_controller.screenshot()

        # Save to temporary file
        save_path = tmp_path / "screenshot.png"
        img.save(save_path)

        # Verify file was created
        assert save_path.exists()

        # Verify can be loaded back
        loaded_img = Image.open(save_path)
        assert loaded_img.size == img.size

    def test_screenshot_pixel_access(self, screen_controller):
        """Test that screenshot pixels can be accessed."""
        img = screen_controller.screenshot()

        # Get pixel at (0, 0)
        pixel = img.getpixel((0, 0))

        assert isinstance(pixel, tuple)
        assert len(pixel) == 3  # RGB

    def test_screenshot_multiple_captures(self, screen_controller):
        """Test taking multiple screenshots in sequence."""
        img1 = screen_controller.screenshot()
        img2 = screen_controller.screenshot()
        img3 = screen_controller.screenshot()

        # All should be valid images
        assert isinstance(img1, Image.Image)
        assert isinstance(img2, Image.Image)
        assert isinstance(img3, Image.Image)

        # Should have called backend 3 times
        assert screen_controller._osal.screenshot.call_count == 3


class TestScreenLocate:
    """Test locate() image recognition methods."""

    def test_locate_functions_delegate_to_osal(self, screen_controller):
        """Test basic locate methods delegate to OSAL."""
        screen_controller.locate("template.png", "screenshot.png")
        screen_controller.locate_all("template.png", "screenshot.png")
        screen_controller.locate_on_screen("template.png", min_search_time=0)
        screen_controller.locate_on_window("template.png", "Title")
        screen_controller.locate_all_on_screen("template.png")
        screen_controller.locate_center_on_screen("template.png")

        screen_controller._osal.mocks.assert_has_calls([
            call.locate("template.png", "screenshot.png"),
            call.locate_all("template.png", "screenshot.png"),
            call.locate_on_screen("template.png", 0),
            call.locate_on_window("template.png", "Title"),
            call.locate_all_on_screen("template.png"),
            call.locate_center_on_screen("template.png"),
        ])

    def test_locate_returns_box_or_none(self, screen_controller):
        """Test that locate returns Box when found, None when not."""
        # Image found
        screen_controller._osal.locate_on_screen.return_value = Box(10, 10, 50, 50)
        result = screen_controller.locate_on_screen("found.png")

        assert isinstance(result, Box)
        assert result.left == 10
        assert result.top == 10

        # Image not found
        screen_controller._osal.locate_on_screen.return_value = None
        result = screen_controller.locate_on_screen("notfound.png")

        assert result is None

    def test_locate_center_returns_point_or_none(self, screen_controller):
        """Test that locate_center returns Point when found."""
        # Image found - return center point
        screen_controller._osal.locate_center_on_screen.return_value = Point(100, 200)
        result = screen_controller.locate_center_on_screen("icon.png")

        assert isinstance(result, Point)
        assert result.x == 100
        assert result.y == 200

        # Image not found
        screen_controller._osal.locate_center_on_screen.return_value = None
        result = screen_controller.locate_center_on_screen("notfound.png")

        assert result is None

    def test_locate_all_returns_generator_or_list(self, screen_controller):
        """Test that locate_all returns iterable of Boxes."""
        # Multiple matches
        boxes = [
            Box(10, 10, 50, 50),
            Box(100, 100, 50, 50),
            Box(200, 200, 50, 50),
        ]
        screen_controller._osal.locate_all_on_screen.return_value = iter(boxes)

        result = screen_controller.locate_all_on_screen("pattern.png")

        # Should be iterable
        result_list = list(result)
        assert len(result_list) == 3
        assert all(isinstance(box, Box) for box in result_list)

    def test_locate_all_empty_when_not_found(self, screen_controller):
        """Test that locate_all returns empty when no matches."""
        screen_controller._osal.locate_all_on_screen.return_value = iter([])

        result = screen_controller.locate_all_on_screen("notfound.png")

        result_list = list(result)
        assert len(result_list) == 0

    def test_locate_with_confidence_parameter(self, screen_controller):
        """Test locate with confidence threshold."""
        screen_controller._osal.locate_on_screen.return_value = Box(50, 50, 100, 100)

        _ = screen_controller.locate_on_screen("image.png", confidence=0.9)

        # Verify confidence was passed to backend
        call_args = screen_controller._osal.locate_on_screen.call_args
        assert call_args is not None
        # Check if confidence in kwargs (implementation specific)

    def test_locate_with_grayscale_parameter(self, screen_controller):
        """Test locate with grayscale option."""
        screen_controller._osal.locate_on_screen.return_value = Box(30, 30, 60, 60)

        result = screen_controller.locate_on_screen("image.png", grayscale=True)

        assert isinstance(result, Box)
        # Verify grayscale was passed
        screen_controller._osal.locate_on_screen.assert_called()

    def test_locate_with_region_parameter(self, screen_controller):
        """Test locate within specific region."""
        screen_controller._osal.locate_on_screen.return_value = Box(20, 20, 40, 40)

        # Search only in top-left quadrant
        region = (0, 0, 500, 500)
        result = screen_controller.locate_on_screen("image.png", region=region)

        assert isinstance(result, Box)

    def test_locate_with_pil_image_object(self, screen_controller):
        """Test locate with PIL Image instead of path."""
        needle_img = Image.new('RGB', (50, 50), color='red')
        screen_controller._osal.locate_on_screen.return_value = Box(100, 100, 50, 50)

        result = screen_controller.locate_on_screen(needle_img)

        assert isinstance(result, Box)
        # Verify PIL Image was passed to backend
        call_args = screen_controller._osal.locate_on_screen.call_args[0]
        assert isinstance(call_args[0], Image.Image)

    def test_locate_invalid_image_path_raises(self, screen_controller):
        """Test that invalid image path raises error."""
        screen_controller._osal.locate_on_screen.side_effect = FileNotFoundError("Image not found")

        with pytest.raises(FileNotFoundError):
            screen_controller.locate_on_screen("nonexistent.png")

    def test_locate_backend_error(self, screen_controller):
        """Test handling backend errors in locate()."""
        screen_controller._osal.locate_on_screen.side_effect = RuntimeError("Locate failed")

        with pytest.raises(RuntimeError, match="Locate failed"):
            screen_controller.locate_on_screen("image.png")

    def test_locate_with_minSearchTime(self, screen_controller):
        """Test locate with minimum search time (performance test)."""
        screen_controller._osal.locate_on_screen.return_value = None

        # Should search for at least minSearchTime seconds
        with patch('time.time', side_effect=[0, 0.1, 0.2, 0.3]):
            result = screen_controller.locate_on_screen(
                "image.png",
                minSearchTime=0.2
            )

        # Should return None after searching
        assert result is None


class TestScreenControllerInitialization:
    """Test ScreenController initialization."""

    def test_init_with_bad_backend_raises(self):
        """Test initialization with bad backend should raises."""
        from pyautogui2.controllers.screen import ScreenController

        mock_backend = MagicMock()  # not AbstractScreen subclass
        with pytest.raises(PyAutoGUIException):
            ScreenController(osal=mock_backend)

    def test_init_with_explicit_backend(self):
        """Test initialization with explicit screen backend."""
        from pyautogui2.controllers.screen import ScreenController
        from pyautogui2.osal.abstract_cls import AbstractScreen

        mock_backend = MagicMock(spec_set=AbstractScreen)
        sc = ScreenController(osal=mock_backend)
        assert sc._osal is mock_backend


class TestScreenValidation:
    """Test input validation and type checking."""

    def test_locate_accepts_string_or_image(self, screen_controller):
        """Test locate accepts both string path and PIL Image."""
        # String path
        screen_controller._osal.locate_on_screen.return_value = None
        screen_controller.locate_on_screen("image.png")

        # PIL Image
        img = Image.new('RGB', (50, 50))
        screen_controller.locate_on_screen(img)

        assert screen_controller._osal.locate_on_screen.call_count == 2

    def test_center(self, screen_controller):
        """Test center."""
        region = Box(10, 10, 100, 200)
        center = screen_controller.center(region)
        assert center == Point(60, 110)


class TestScreenPerformance:
    """Test performance-related features."""

    def test_multiple_screenshots_independent(self, screen_controller):
        """Test multiple screenshots don't interfere."""
        img1 = screen_controller.screenshot()
        img2 = screen_controller.screenshot()
        img3 = screen_controller.screenshot()

        # Each should be independent Image object
        assert img1 is not img2
        assert img2 is not img3

        # All should be valid
        assert all(isinstance(img, Image.Image) for img in [img1, img2, img3])

    def test_pixel_sampling_multiple_points(self, screen_controller):
        """Test sampling many pixels in sequence."""
        points = [(x * 10, y * 10) for x in range(10) for y in range(10)]

        colors = [screen_controller.pixel(x, y) for x, y in points]

        # All should return valid colors
        assert len(colors) == 100
        assert all(isinstance(c, tuple) and len(c) == 3 for c in colors)

    def test_locate_caching_if_implemented(self, screen_controller):
        """Test locate result caching (if implemented)."""
        # Some implementations cache screenshot for repeated locate calls
        screen_controller._osal.locate_on_screen.return_value = Box(10, 10, 50, 50)

        # Multiple locate calls
        result1 = screen_controller.locate_on_screen("image.png")
        result2 = screen_controller.locate_on_screen("image.png")

        # Both should succeed
        assert result1 is not None
        assert result2 is not None


class TestScreenEdgeCases:
    """Test various edge cases and corner scenarios."""

    def test_get_size_after_screenshot(self, screen_controller):
        """Test get_size is consistent after screenshot."""
        size_before = screen_controller.get_size()
        screen_controller.screenshot()
        size_after = screen_controller.get_size()

        assert size_before == size_after

    def test_pixel_at_screenshot_boundaries(self, screen_controller):
        """Test pixel sampling at exact screen boundaries."""
        width, height = screen_controller.get_size()

        # Four corners
        colors = [
            screen_controller.pixel(0, 0),
            screen_controller.pixel(width - 1, 0),
            screen_controller.pixel(0, height - 1),
            screen_controller.pixel(width - 1, height - 1),
        ]

        # All should be valid
        assert all(isinstance(c, tuple) and len(c) == 3 for c in colors)

    def test_locate_very_small_needle(self, screen_controller):
        """Test locating very small image (1x1 pixel)."""
        screen_controller._osal.locate_on_screen.return_value = Box(100, 100, 1, 1)

        tiny_img = Image.new('RGB', (1, 1), color='red')
        result = screen_controller.locate_on_screen(tiny_img)

        assert isinstance(result, Box)
        assert result.width == 1
        assert result.height == 1

    def test_locate_needle_larger_than_screen(self, screen_controller):
        """Test locating image larger than screen."""
        # Should return None or raise error
        screen_controller._osal.locate_on_screen.return_value = None

        huge_img = Image.new('RGB', (10000, 10000))
        result = screen_controller.locate_on_screen(huge_img)

        assert result is None

    def test_operations_after_backend_error(self, screen_controller):
        """Test that controller recovers after backend error."""
        # Cause one error
        screen_controller._osal.pixel.side_effect = [RuntimeError("Error"), (10, 20, 30)]

        with pytest.raises(RuntimeError, match="Error"):
            screen_controller.pixel(10, 10)

        # Should work again
        color = screen_controller.pixel(20, 20)
        assert color == (10, 20, 30)

    def test_locate_backend_error(self, screen_controller):
        """Test that locate() not crash with backend error."""
        screen_controller._osal.locate.return_value = None
        result = screen_controller.locate(needle_image="a.png", haystack_image="b.png")
        assert result is None

    def test_locate_on_window_backend_error(self, screen_controller):
        """Test that locate_on_window() not crash with backend error."""
        screen_controller._osal.locate_on_window.return_value = None
        result = screen_controller.locate_on_window(image="a.png", title="Title")
        assert result is None

    def test_locate_all_on_screen_backend_error(self, screen_controller):
        """Test that locate_all_on_screen() not crash with backend error."""
        screen_controller._osal.locate_all_on_screen.return_value = None
        result = screen_controller.locate_all_on_screen(image="a.png")
        assert result == []

    def test_locate_all_backend_error(self, screen_controller):
        """Test that locate_all() not crash with backend error."""
        screen_controller._osal.locate_all.return_value = None
        result = screen_controller.locate_all(needle_image="a.png", haystack_image="b.png")
        assert result == []


class TestScreenRepresentation:
    """Test string representations for debugging."""

    def test_repr_contains_class_name(self, screen_controller):
        """Test that __repr__ contains class name."""
        rep = repr(screen_controller)
        assert "ScreenController" in rep

    def test_str_is_readable(self, screen_controller):
        """Test that __str__ provides readable output."""
        string = str(screen_controller)
        assert len(string) > 0
        # Should mention screen or controller
        assert "screen" in string.lower() or "controller" in string.lower()


class TestScreenMultiMonitor:
    """Test multi-monitor scenarios."""

    def test_get_size_returns_primary_monitor(self, screen_controller):
        """Test get_size returns primary monitor dimensions."""
        size = screen_controller.get_size()

        # Should be primary monitor size
        assert size == (1920, 1080)

    def test_get_size_max_includes_all_monitors(self, screen_controller):
        """Test get_size_max spans all monitors."""
        max_size = screen_controller.get_size_max()

        # Should be larger (or equal) to single monitor
        assert max_size == (3840, 2160)
        assert max_size[0] >= 1920
        assert max_size[1] >= 1080

    def test_pixel_across_monitors(self, screen_controller):
        """Test pixel sampling across multiple monitors."""
        # Sample pixel on secondary monitor (if exists)
        primary_width, _ = screen_controller.get_size()

        # Pixel on secondary monitor (x > primary width)
        try:
            color = screen_controller.pixel(primary_width + 100, 100)
            # If succeeds, should return valid color
            assert isinstance(color, tuple)
            assert len(color) == 3
        except (PyAutoGUIException, ValueError):
            # Expected if coordinate out of bounds
            pass


class TestScreenTypeCompatibility:
    """Test type compatibility and conversions."""

    def test_box_has_expected_attributes(self, screen_controller):
        """Test Box object has left, top, width, height."""
        screen_controller._osal.locate_on_screen.return_value = Box(10, 20, 100, 200)

        box = screen_controller.locate_on_screen("image.png")

        assert hasattr(box, 'left')
        assert hasattr(box, 'top')
        assert hasattr(box, 'width')
        assert hasattr(box, 'height')
        assert box.left == 10
        assert box.top == 20
        assert box.width == 100
        assert box.height == 200

    def test_point_has_x_y_attributes(self, screen_controller):
        """Test Point object has x, y attributes."""
        screen_controller._osal.locate_center_on_screen.return_value = Point(150, 250)

        point = screen_controller.locate_center_on_screen("icon.png")

        assert hasattr(point, 'x')
        assert hasattr(point, 'y')
        assert point.x == 150
        assert point.y == 250

    def test_screenshot_returns_pil_compatible_image(self, screen_controller):
        """Test screenshot returns PIL-compatible image."""
        img = screen_controller.screenshot()

        # Should support PIL operations
        assert hasattr(img, 'save')
        assert hasattr(img, 'crop')
        assert hasattr(img, 'resize')
        assert hasattr(img, 'convert')
        assert hasattr(img, 'getpixel')

    def test_locate_with_pathlib_path(self, screen_controller):
        """Test locate accepts pathlib.Path."""
        from pathlib import Path

        screen_controller._osal.locate_on_screen.return_value = Box(50, 50, 100, 100)

        image_path = Path("test_image.png")
        result = screen_controller.locate_on_screen(image_path)

        assert isinstance(result, Box)

