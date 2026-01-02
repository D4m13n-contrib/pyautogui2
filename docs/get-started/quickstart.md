# Quickstart

You're 5 minutes away from automating your first task. Let's go.

---

## Setup

Every interaction goes through a single `PyAutoGUI` instance:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
```

That's it. No configuration needed to get started.  
`pag` gives you access to four controllers: `pointer`, `keyboard`, `screen`, and `dialogs`.

---

## Pointer — Move & Click

```python
# Move the mouse to absolute coordinates (x, y)
pag.pointer.move_to(500, 300)

# Left-click at the current position
pag.pointer.click()

# Or combine: move and click in one call
pag.pointer.click(500, 300)

# Right-click, double-click
pag.pointer.click(500, 300, button='right')
pag.pointer.double_click(500, 300)
```

Want smooth, human-like movement? Add a duration:

```python
pag.pointer.move_to(500, 300, duration=0.5)  # glides over 500ms
```

📖 [Full Pointer Guide →](../guides/pointer.md)

---

## Keyboard — Type & Shortcut

```python
# Type a string (handles special characters automatically)
pag.keyboard.write("Hello, world!")

# Press a single key
pag.keyboard.press("enter")

# Keyboard shortcut
pag.keyboard.hotkey("ctrl", "c")  # Copy
pag.keyboard.hotkey("ctrl", "v")  # Paste
```

📖 [Full Keyboard Guide →](../guides/keyboard.md)

---

## Screen — Capture & Locate

```python
# Take a screenshot
screenshot = pag.screen.screenshot()
screenshot.save("screen.png")

# Read the color of a pixel at the current mouse position
pos = pag.pointer.get_position()
color = pag.screen.pixel(pos.x, pos.y)
print(f"Pixel at {pos}: RGB{color}")  # e.g. Pixel at Point(742, 451): RGB(30, 30, 30)

# Find an image on screen and click it
location = pag.screen.locate_on_screen("button.png")
if location:
    pag.pointer.click(location.x, location.y)
```

📖 [Full Screen Guide →](../guides/screen.md)

---

## Dialogs — Alerts & Prompts

```python
# Simple alert
pag.dialogs.alert("Task complete!")

# Ask for confirmation
if pag.dialogs.confirm("Do you want to continue?") == "OK":
    pag.keyboard.write("Let's go!")

# Ask for user input
name = pag.dialogs.prompt("What's your name?")
pag.keyboard.write(f"Hello, {name}!")
```

📖 [Full Dialogs Guide →](../guides/dialogs.md)

---

## Putting It Together

Here's a small script that combines several controllers — just to show how naturally they compose:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# Where is the mouse right now?
pos = pag.pointer.get_position()
color = pag.screen.pixel(pos.x, pos.y)
print(f"Cursor is at {pos}, pixel color: RGB{color}")

# Move, type, done
pag.pointer.click(500, 300)
pag.keyboard.write("Automated with PyAutoGUI2")
pag.keyboard.press("enter")
```

---

## What's Next?

You've covered the basics. Here's where to go depending on what you want to do:

| I want to… | Go here |
|---|---|
| Control the mouse precisely | [Pointer Guide](../guides/pointer.md) |
| Type text or use shortcuts | [Keyboard Guide](../guides/keyboard.md) |
| Capture or search the screen | [Screen Guide](../guides/screen.md) |
| Show popups and prompts | [Dialogs Guide](../guides/dialogs.md) |
| Understand how it all works | [Architecture Overview](../architecture/overview.md) |
