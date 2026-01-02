"""PyAutoGUI types."""

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class ButtonName(Enum):
    """Pointer button name enumeration."""
    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"
    PRIMARY = "primary"
    SECONDARY = "secondary"


class Point(NamedTuple):
    """Represents a point on the screen.

    Attributes:
        x: X coordinate (horizontal position)
        y: Y coordinate (vertical position)
    """
    x: int
    y: int


class Size(NamedTuple):
    """Represents screen dimensions.

    Attributes:
        width: Width in pixels
        height: Height in pixels
    """
    width: int
    height: int


class Box(NamedTuple):
    """Represents a rectangular region on the screen.

    Attributes:
        left: X coordinate of the left edge
        top: Y coordinate of the top edge
        width: Width of the box in pixels
        height: Height of the box in pixels

    Example:
        >>> box = Box(left=100, top=50, width=200, height=100)
        >>> box.center
        Point(x=200, y=100)
        >>> box.right
        300
        >>> box.bottom
        150
    """
    left: int
    top: int
    width: int
    height: int

    @property
    def center(self) -> Point:
        """Calculate the center point of this box.

        Returns:
            Point with coordinates of the center (x, y)
        """
        return Point(
            x=self.left + self.width // 2,
            y=self.top + self.height // 2
        )

    @property
    def right(self) -> int:
        """Right edge X coordinate (left + width)."""
        return self.left + self.width

    @property
    def bottom(self) -> int:
        """Bottom edge Y coordinate (top + height)."""
        return self.top + self.height



ArgCoordX = int | float | None | tuple[int, int] | str
ArgCoordY = int | float | None


Coord = int | float | None

@dataclass
class Coords:
    """Coodinates dataclass defines 'x' and 'y' positions."""
    x: Coord
    y: Coord

CoordsRect = tuple[Coord, Coord, int, int]
CoordsNormalized = tuple[int, int]
