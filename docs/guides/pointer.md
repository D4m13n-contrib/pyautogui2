# Pointer Control

Complete guide to controlling the mouse/pointer with PyAutoGUI2.

---

## Overview

`PointerController` provides cross-platform mouse/pointer control:

- **Movement** — instant or animated with easing functions
- **Clicking** — all buttons, single/double/triple, with configurable intervals
- **Dragging** — click-and-drag with optional animation
- **Scrolling** — vertical and horizontal
- **Flexible input** — coordinates, tuples, `Point` objects, or image filenames

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
```

---

## Basic Usage

### Getting the Current Position

```python
pos = pag.pointer.get_position()
print(f"Pointer at x={pos.x}, y={pos.y}")
```

**Returns:** a `Point` object with `.x` and `.y` attributes.

---

### Moving the Pointer

#### Absolute movement

```python
# Instant
pag.pointer.move_to(100, 200)

# Animated (0.5 s, with easing)
pag.pointer.move_to(500, 500, duration=0.5, tween="easeOutQuad")
```

#### Partial movement (preserving one axis)

Pass `None` for either coordinate to keep the current position on that axis:

```python
# Move only horizontally — Y stays where it is
pag.pointer.move_to(500, None)

# Move only vertically — X stays where it is
pag.pointer.move_to(None, 300)
```

This is useful when you want to align the cursor to a fixed column or row without affecting the other axis.

#### Relative movement

```python
# Move 50 px right and 100 px down from current position
pag.pointer.move_rel(50, 100)

# Animated
pag.pointer.move_rel(-50, -100, duration=0.5)
```

---

### Clicking

#### Basic click

```python
pag.pointer.click()                    # left click at current position
pag.pointer.click(100, 200)            # left click at (100, 200)
pag.pointer.click(100, 200, button="right")
```

#### Convenience methods

```python
pag.pointer.left_click(100, 200)
pag.pointer.right_click(100, 200)
pag.pointer.middle_click(100, 200)
pag.pointer.double_click(100, 200)
pag.pointer.triple_click(100, 200)
```

#### Multi-click with interval

```python
# 3 clicks with 0.1 s between each
pag.pointer.click(100, 200, clicks=3, interval=0.1)
```

---

### Scrolling

#### Vertical

```python
pag.pointer.scroll(3)                 # scroll up 3 clicks at current position
pag.pointer.vscroll(-5)               # scroll down 5 clicks
pag.pointer.scroll(3, x=500, y=400)   # scroll at a specific location
```

Positive values scroll up, negative values scroll down.

#### Horizontal

```python
pag.pointer.hscroll(3)    # scroll right 3 clicks
pag.pointer.hscroll(-3)   # scroll left 3 clicks
```

> **Note:** Horizontal scrolling support varies by platform and application.

---

### Dragging

#### Absolute drag

```python
# Drag from current position to (500, 300)
pag.pointer.drag_to(500, 300)

# With animation and a specific button
pag.pointer.drag_to(500, 300, duration=1.0, tween="easeInOutQuad", button="right")
```

#### Relative drag

```python
# Drag 200 px right from current position
pag.pointer.drag_rel(200, 0, duration=0.5)
```

---

## Coordinate Formats

All methods that accept coordinates support several input formats:

#### Two integers

```python
pag.pointer.click(100, 200)
```

#### Tuple or list

```python
pag.pointer.click((100, 200))
pag.pointer.click([100, 200])
```

#### `Point` object

```python
from pyautogui2.utils.types import Point

pos = Point(100, 200)
pag.pointer.click(pos)
```

#### Image filename

Pass an image filename and PyAutoGUI2 will locate it on screen automatically,
then act on its center:

```python
pag.pointer.click("submit_button.png")
pag.pointer.double_click("icon.png")
pag.pointer.drag_to("target.png", duration=0.5)
```

If the image cannot be found on screen, an `ImageNotFoundException` is raised.

```python
from pyautogui2.utils.exceptions import ImageNotFoundException

try:
    pag.pointer.click("submit_button.png")
except ImageNotFoundException:
    print("Image not found on screen.")
```

---

## Smooth Movement (Tweening)

By default, `move_to()` and `drag_to()` move the pointer instantly.
Pass `duration` (in seconds) to animate the movement, and optionally `tween`
to control the easing curve:

```python
pag.pointer.move_to(800, 600, duration=1.0, tween="easeOutQuad")
pag.pointer.drag_to(400, 300, duration=2.0, tween="easeInOutCubic")
```

Available easing functions are listed in the [Tweening Reference](tweening.md).
The default tween is `"linear"`.

---

## Advanced Usage

### Button Press and Release

Use `button_down()` and `button_up()` for fine-grained control:

```python
# Press and release at current position
pag.pointer.button_down()
pag.pointer.button_up()

# Move to coordinates first, then press
pag.pointer.button_down(100, 200)
pag.pointer.button_up(100, 200)

# With a specific button
pag.pointer.button_down(100, 200, button="right")
pag.pointer.button_up(100, 200, button="right")
```

When coordinates (or an image filename) are provided, the pointer moves to that
location before the press or release is applied.

Always pair `button_down()` with `button_up()`. Use `try/finally` to guarantee
the button is released even if an error occurs:

```python
pag.pointer.button_down(100, 200)
try:
    pag.pointer.move_to(500, 400, duration=1.0)
finally:
    pag.pointer.button_up()
```

---

### Relative Movement and Drag

```python
# Nudge the pointer slightly
pag.pointer.move_rel(10, 0)

# Drag diagonally
pag.pointer.drag_rel(100, 100, duration=0.5)
```

---

### Screen Boundary Check

```python
if pag.pointer.on_screen(1000, 800):
    pag.pointer.click(1000, 800)
else:
    print("Coordinates are outside screen bounds.")
```

Called without arguments, `on_screen()` checks the current pointer position:

```python
if pag.pointer.on_screen():
    print("Pointer is on screen.")
```

---

## Best Practices

**Add duration for human-like movement**

```python
# ✅ Natural
pag.pointer.move_to(500, 300, duration=0.3, tween="easeOutQuad")

# ❌ Robotic — may confuse applications that rely on hover events
pag.pointer.move_to(500, 300)
pag.pointer.click()
```

**Check screen bounds before acting on dynamic coordinates**

```python
x, y = compute_target()
if pag.pointer.on_screen(x, y):
    pag.pointer.click(x, y)
```

**Always release pressed buttons**

```python
pag.pointer.button_down()
try:
    do_something()
finally:
    pag.pointer.button_up()
```

**Use convenience methods for readability**

```python
# ✅ Intent is clear
pag.pointer.right_click(100, 200)
pag.pointer.double_click("icon.png")

# ❌ Verbose for no benefit
pag.pointer.click(100, 200, button="right")
```

---

## Common Pitfalls

**Coordinates out of bounds**

```python
# ❌ Will fail or be clamped on smaller screens
pag.pointer.click(9999, 9999)

# ✅ Check first
if pag.pointer.on_screen(9999, 9999):
    pag.pointer.click(9999, 9999)
```

**Acting too fast for the target application**

```python
# ❌ The application may miss intermediate clicks
pag.pointer.click(100, 200)
pag.pointer.click(300, 400)

# ✅ Add small delays or use duration
import time
pag.pointer.click(100, 200)
time.sleep(0.1)
pag.pointer.click(300, 400)
```

**Image not found on screen**

```python
# ❌ Unhandled exception if image is absent
pag.pointer.click("button.png")

# ✅ Handle the exception explicitly
from pyautogui2.utils.exceptions import ImageNotFoundException

try:
    pag.pointer.click("button.png")
except ImageNotFoundException:
    print("Button not found — skipping.")
```

**Wrong button name casing**

```python
# ❌ Invalid — button names are lowercase
pag.pointer.click(100, 200, button="LEFT")

# ✅ Correct
pag.pointer.click(100, 200, button="left")
```

---

## Related Documentation

- [Keyboard Control](keyboard.md) — keyboard input and shortcuts
- [Screen Capture](screen.md) — screenshot and image location
- [Tweening Reference](tweening.md) — complete list of easing functions
- [Types Reference](types.md) — `Point`, `Size`, `Box`, `ButtonName`
- [Settings](settings.md) — `PAUSE`, `FAILSAFE` and global configuration
