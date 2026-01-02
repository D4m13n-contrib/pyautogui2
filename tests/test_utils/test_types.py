import pytest

from pyautogui2.utils.types import Box, Point


class TestTypesBox:
    def test_box_init(self):
        region = (10, 20, 30, 40)

        box1 = Box(left=region[0], top=region[1],
                   width=region[2], height=region[3])
        box2 = Box(region[0], region[1], region[2], region[3])
        box3 = Box(*region)

        assert box1 == box2
        assert box1 == box3

    def test_box_namedtuple_behavior(self):
        box = Box(left=10, top=20, width=30, height=40)

        # Unpacking
        left, top, width, height = box
        assert (left, top, width, height) == (10, 20, 30, 40)

        # Hashable
        box_set = {box}
        assert box in box_set

        # Immutable
        with pytest.raises(AttributeError):
            box.left = 999

        # Can't add attributes
        with pytest.raises(AttributeError):
            box.custom = "test"

    def test_box_properties(self):
        box = Box(left=100, top=50, width=200, height=100)

        assert box.center == Point(x=200, y=100)

        assert box.right == 300
        assert box.bottom == 150
