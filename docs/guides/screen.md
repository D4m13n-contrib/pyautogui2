# Screen Guide

Complete guide to screen interaction with PyAutoGUI2.

---

## Overview

The screen controller provides four categories of operations:

- **Screenshots** — capture the full screen or a specific region
- **Image location** — find UI elements by visual template matching
- **Pixel operations** — read and verify pixel colors
- **Window management** — query and interact with application windows

**Required dependencies:** `Pillow`, `PyScreeze` (installed automatically with PyAutoGUI2).
**Optional:** `OpenCV` — enables the `confidence` parameter for fuzzy image matching.
**Windows/MacOS only:** `PyGetWindow` — required for window management.

---

## Basic Usage

### Taking a Screenshot

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# Full screen
img = pag.screen.screenshot()
img.save("screen.png")  # img is a Pillow Image object

# Specific region: (left, top, width, height)
img = pag.screen.screenshot(region=(100, 200, 800, 600))
```

### Getting the Screen Size

```python
# Primary screen resolution
width, height = pag.screen.get_size()
print(f"Screen: {width}x{height}")

# Total size across all monitors (multi-monitor setups)
width, height = pag.screen.get_size_max()
print(f"All screens combined: {width}x{height}")
```

### Reading a Pixel Color

```python
# Returns an (R, G, B) tuple
r, g, b = pag.screen.pixel(500, 300)
print(f"Pixel at (500, 300): rgb({r}, {g}, {b})")
```

---

## Screenshots

`screenshot()` returns a **Pillow `Image` object**, which you can save, crop, analyze, or pass directly to image location functions.

```python
img = pag.screen.screenshot()

# Save to disk
img.save("capture.png")

# Crop a sub-region from a full screenshot
region = img.crop((100, 100, 400, 400))
region.save("cropped.png")
```

### Capturing a Region

Capturing only the area you need is faster and uses less memory than a full screenshot.

```python
# region=(left, top, width, height)
toolbar = pag.screen.screenshot(region=(0, 0, 1920, 40))
```

---

## Image Location

Image location finds where a reference image appears on screen. This is the primary way to locate UI elements (buttons, icons, text fields) without hardcoding coordinates.

```python
# Returns a Box(left, top, width, height) or None if not found
box = pag.screen.locate("button.png")

if box is not None:
    # Get the center of the matched region
    center = pag.screen.center(box)
    pag.pointer.click(center.x, center.y)
```

> **Note:** `locate()` raises `ImageNotFoundException` if the image is not found and no default is provided. Always check for `None` or handle the exception.

### Finding Multiple Elements

```python
# Returns a generator of all matching Box regions
for box in pag.screen.locate_all("icon.png"):
    center = pag.screen.center(box)
    print(f"Found at: {center}")
```

### Fuzzy Matching with `confidence`

By default, matching is exact (pixel-perfect). If the UI has slight rendering differences (antialiasing, scaling), use `confidence`:

```python
# Requires OpenCV: pip install opencv-python
box = pag.screen.locate("button.png", confidence=0.9)  # 90% similarity threshold
```

> **OpenCV required:** the `confidence` parameter is only available if `opencv-python` is installed. Without it, passing `confidence` raises an error.

### Grayscale matching

Pass `grayscale=True` to convert both the screenshot and the template to grayscale before matching. This can speed up location by roughly 30%, at the cost of ignoring color information.

```python
# Faster search — colour differences are ignored
box = pag.screen.locate_on_screen("button.png", grayscale=True)

# Combine with confidence for fuzzy grayscale matching (requires OpenCV)
box = pag.screen.locate_on_screen("button.png", grayscale=True, confidence=0.8)
```

> **Trade-off:** Two images that differ only by colour will match incorrectly when `grayscale=True`. Use it when the template is visually distinct in shape, not just colour.

### Searching Within a Region

Restrict the search to a portion of the screen to improve performance:

```python
# Only search in the top-left 800x600 area
box = pag.screen.locate("save_icon.png", region=(0, 0, 800, 600))
```

### Searching Within a Screenshot

You can search inside an already-captured image instead of taking a new screenshot:

```python
img = pag.screen.screenshot()
box = pag.screen.locate("checkbox.png", haystack=img)
```

This is useful when you need to perform multiple searches on the same frame without re-capturing the screen each time.

### Performance notes

Image location is significantly slower than other PyAutoGUI2 operations:

| Operation | Typical duration |
|---|---|
| `screenshot()` | ~100 ms |
| `locate_on_screen()` on full screen | 1–2 s |
| `locate_on_screen()` with `region=` | Faster — proportional to region area |
| `locate_on_screen()` with `grayscale=True` | ~30% faster than colour matching |

For time-sensitive scripts, always prefer a `region=` to restrict the search area, and consider `grayscale=True` if colour is not a distinguishing factor.

---

## Pixel Operations

### Reading a Pixel

```python
r, g, b = pag.screen.pixel(100, 200)
```

### Checking a Pixel Color

```python
# Returns True if the pixel matches the given color
if pag.screen.pixel_matches_color(100, 200, (255, 0, 0)):
    print("Red pixel confirmed")

# Allow a tolerance (±10 per channel)
if pag.screen.pixel_matches_color(100, 200, (255, 0, 0), tolerance=10):
    print("Close enough to red")
```

---

## Window Management

> **Linux:** window management is not supported.

### Listing Windows

```python
# Returns a list of window title strings
titles = pag.screen.get_windows_with_title("Notepad")
for title in titles:
    print(title)
```

### Getting the Active Window

```python
window = pag.screen.get_active_window()
if window is not None:
    print(f"Active: {window.title} at {window.left}, {window.top}")
```

### Moving and Resizing a Window

```python
window = pag.screen.get_active_window()

if window is not None:
    window.moveTo(100, 100)        # Move top-left corner
    window.resizeTo(1024, 768)     # Resize
    window.maximize()              # Maximize
    window.minimize()              # Minimize
    window.restore()               # Restore from minimized/maximized
    window.activate()              # Bring to foreground
```

---

## Best Practices

**Save screenshots when debugging image location**

If `locate()` returns `None` unexpectedly, capture and inspect the actual screen state:

```python
img = pag.screen.screenshot()
img.save("debug.png")  # Open this to see what PyAutoGUI2 actually sees
box = pag.screen.locate("button.png", haystack=img)
```

**Prefer region searches for performance**

Full-screen searches are slow on large displays. Narrow the region whenever possible.

```python
# Slower
box = pag.screen.locate("ok_button.png")

# Faster
box = pag.screen.locate("ok_button.png", region=(600, 400, 800, 300))
```

**Use `confidence` only when needed**

Fuzzy matching is slower than exact matching. Start with exact matching, then add `confidence` only if you encounter false negatives due to rendering differences.

**Capture once, search many times**

```python
img = pag.screen.screenshot()

# Multiple searches on the same frame
play_btn = pag.screen.locate("play.png", haystack=img)
pause_btn = pag.screen.locate("pause.png", haystack=img)
stop_btn = pag.screen.locate("stop.png", haystack=img)
```

---

## Common Pitfalls

**`locate()` returns `None` or raises `ImageNotFoundException`**

- The reference image was captured at a different screen resolution or DPI
- The UI element is partially off-screen or obscured
- Sub-pixel rendering differences — try adding `confidence=0.95`
- The element simply isn't visible at the time of the call

**Coordinates are off after a screenshot**

`screenshot(region=...)` returns an image whose internal coordinates start at `(0, 0)`. The `Box` returned by `locate()` uses **screen coordinates**, not region-relative ones — no manual offset needed.

**Window management raises an error on Linux**

This is expected — `PyGetWindow` is not supported on Linux. Use the pointer and keyboard controllers to interact with windows instead.

---

## Related Documentation

- [Pointer guide](pointer.md) — click on located elements
- [Keyboard guide](keyboard.md) — type after focusing a window
- [Settings guide](settings.md) — configure `PAUSE` and global behavior
