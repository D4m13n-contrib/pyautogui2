# Types Reference

Core data types used throughout PyAutoGUI2.

---

## Overview

PyAutoGUI2 uses strongly-typed data structures to represent screen coordinates, regions, and dimensions. These types are immutable `NamedTuple` objects that provide:

- **Type safety** with full mypy support
- **Immutability** to prevent accidental modifications
- **Named fields** for better code readability
- **Tuple unpacking** for backward compatibility

**Key types:**
- **`Point`** — Single coordinate `(x, y)`
- **`Size`** — Dimensions `(width, height)`
- **`Box`** — Rectangular region `(left, top, width, height)`
- **`ButtonName`** — Mouse button enumeration

---

## Quick Reference

| Type | Fields | Usage |
|------|--------|-------|
| `Point` | `x`, `y` | Cursor position, click coordinates |
| `Size` | `width`, `height` | Screen resolution, window size |
| `Box` | `left`, `top`, `width`, `height` | Screenshots, image location, windows |
| `ButtonName` | `LEFT`, `MIDDLE`, `RIGHT`, `PRIMARY`, `SECONDARY` | Mouse button specification |

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

cursor = pag.pointer.get_position()              # Point(x=500, y=300)
resolution = pag.screen.get_size()               # Size(width=1920, height=1080)
region = pag.screen.locate_on_screen("btn.png")  # Box(left=100, top=50, width=80, height=30)
```

---

## Point

Represents a single coordinate on the screen.

```python
class Point(NamedTuple):
    x: int  # Horizontal position (left to right)
    y: int  # Vertical position (top to bottom)
```

```python
from pyautogui2.utils.types import Point

point = Point(x=100, y=200)

print(point.x)   # 100
print(point.y)   # 200

x, y = point     # Tuple unpacking
```

**Common sources:**

| Method | Returns |
|--------|---------|
| `pointer.get_position()` | Current cursor position |
| `box.center` | Center of a `Box` region |

---

## Size

Represents dimensions (width × height).

```python
class Size(NamedTuple):
    width: int
    height: int
```

```python
from pyautogui2.utils.types import Size

size = Size(width=1920, height=1080)

print(size.width)   # 1920
print(size.height)  # 1080

aspect = size.width / size.height  # 1.777... (16:9)
```

**Common sources:**

| Method | Returns |
|--------|---------|
| `screen.get_size()` | Full screen resolution |

---

## Box

Represents a rectangular region on the screen, defined by its top-left corner, width, and height.

```python
class Box(NamedTuple):
    left: int    # X coordinate of the top-left corner
    top: int     # Y coordinate of the top-left corner
    width: int   # Horizontal extent
    height: int  # Vertical extent
```

```python
from pyautogui2.utils.types import Box

box = Box(left=100, top=50, width=200, height=100)

print(box.left, box.top)      # 100 50
print(box.width, box.height)  # 200 100

center = box.center           # Point(x=200, y=100)
pag.pointer.click(center)     # Click the center of the region
```

**Common sources:**

| Method | Returns |
|--------|---------|
| `screen.locate_on_screen()` | Bounding box of a found image |
| `screen.locate_all_on_screen()` | Iterator of bounding boxes |

---

## ButtonName

Enum for specifying mouse buttons.

```python
class ButtonName(Enum):
    LEFT      = "left"
    MIDDLE    = "middle"
    RIGHT     = "right"
    PRIMARY   = "primary"
    SECONDARY = "secondary"
```

```python
from pyautogui2.utils.types import ButtonName

pag.pointer.click(button=ButtonName.LEFT)
pag.pointer.click(button=ButtonName.RIGHT)
pag.pointer.click(button=ButtonName.MIDDLE)

# String values are also accepted
pag.pointer.click(button="right")

# PRIMARY/SECONDARY adapt to the OS pointer configuration
pag.pointer.click(button=ButtonName.PRIMARY)    # Left on most systems
pag.pointer.click(button=ButtonName.SECONDARY)  # Right on most systems
```

> **Platform note:** `PRIMARY` and `SECONDARY` may be swapped on systems configured for left-handed use. See [Platform Guide](../platforms/index.md) for details.

---

## Internal Types

Additional lower-level types (`Coord`, `Coords`, `ArgCoordX`, `ArgCoordY`, etc.) are used internally by PyAutoGUI2. You do not need them for normal usage — they are documented in the [contributor documentation](../support/contributing.md).

---

## Best Practices

**Use named arguments for clarity**

```python
# ✅ Explicit
point = Point(x=100, y=200)
box = Box(left=100, top=50, width=200, height=100)

# ❌ Harder to read at a glance
point = Point(100, 200)
box = Box(100, 50, 200, 100)
```

**Use `box.center` instead of manual calculation**

```python
box = Box(left=100, top=50, width=200, height=100)

# ✅ Built-in, error-free
pag.pointer.click(box.center)

# ❌ Manual, error-prone
pag.pointer.click(box.left + box.width // 2, box.top + box.height // 2)
```

**Use `ButtonName` enum for IDE support**

```python
# ✅ Autocomplete, refactor-safe
pag.pointer.click(button=ButtonName.RIGHT)

# ✅ String works too, but no IDE support
pag.pointer.click(button="right")
```

---

## Related

- [Pointer Guide](pointer.md) — Uses `Point`, `ButtonName`
- [Screen Guide](screen.md) — Uses `Box`, `Size`, `Point`
- [Quickstart](../get-started/quickstart.md)
