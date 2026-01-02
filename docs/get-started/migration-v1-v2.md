# Migration from PyAutoGUI v1

Already have code written with PyAutoGUI v1? This guide covers what changed,
what still works, and what you'll need to update.

---

## TL;DR

| | PyAutoGUI v1 | PyAutoGUI2 |
|---|---|---|
| Import | `import pyautogui` | `from pyautogui2 import PyAutoGUI` and `pag = PyAutoGUI()` |
| Usage | `pyautogui.click(x, y)` | `pag.pointer.click(x, y)` |
| Settings | `pyautogui.PAUSE = 0.5` | `pag.PAUSE = 0.5` |
| Module name | `pyautogui` | `pyautogui2` |

**The short version:** the flat API still works for a quick migration,
but the new OOP API is cleaner and is where future development happens.

---

## Compatibility layer

PyAutoGUI2 ships with a compatibility layer that maps most v1 functions
to their v2 equivalents. This means your existing code may work with
minimal changes — just swap the import:

```python
# Before
import pyautogui
pyautogui.click(100, 200)
pyautogui.write("hello")

# After (flat API, still works)
import pyautogui2
pyautogui2.click(100, 200)
pyautogui2.write("hello")
```

This is useful to get up and running quickly, but the **recommended**
approach is to migrate to the OOP API:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
pag.pointer.click(100, 200)
pag.keyboard.write("hello")
```

---

## What changed

### Settings — `PAUSE` and `FAILSAFE`

These still exist, but they're now **instance properties** instead of module-level globals:

```python
# Before
import pyautogui
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

# After
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
pag.PAUSE = 0.5      # pause between actions
pag.FAILSAFE = True  # move to corner to emergency-stop
```

The behavior is identical — only where you set them has changed.

---

### Function & argument renames

Most renames follow a simple pattern: `camelCase` → `snake_case`.

#### Pointer

| v1 | v2 | Notes |
|---|---|---|
| `moveTo(x, y)` | `pag.pointer.move_to(x, y)` | |
| `moveRel(dx, dy)` / `move(dx, dy)` | `pag.pointer.move_rel(offset_x, offset_y)` | Args renamed |
| `click(x, y)` | `pag.pointer.click(x, y)` | |
| `leftClick(x, y)` | `pag.pointer.left_click(x, y)` | |
| `rightClick(x, y)` | `pag.pointer.right_click(x, y)` | |
| `middleClick(x, y)` | `pag.pointer.middle_click(x, y)` | |
| `doubleClick(x, y)` | `pag.pointer.double_click(x, y)` | |
| `tripleClick(x, y)` | `pag.pointer.triple_click(x, y)` | |
| `dragTo(x, y)` | `pag.pointer.drag_to(x, y)` | |
| `dragRel(dx, dy)` / `drag(dx, dy)` | `pag.pointer.drag_rel(offset_x, offset_y)` | Args renamed |
| `scroll(n)` | `pag.pointer.scroll(n)` | |
| `hscroll(n)` | `pag.pointer.hscroll(n)` | |
| `vscroll(n)` | `pag.pointer.vscroll(n)` | |
| `mouseDown()` | `pag.pointer.button_down()` | |
| `mouseUp()` | `pag.pointer.button_up()` | |
| `position()` | `pag.pointer.get_position()` | |
| `onScreen(x, y)` | `pag.pointer.on_screen(x, y)` | |

#### Keyboard

| v1 | v2 | Notes |
|---|---|---|
| `typewrite(text)` / `write(text)` | `pag.keyboard.write(text)` | |
| `press(key)` | `pag.keyboard.press_key(key)` | |
| `keyDown(key)` | `pag.keyboard.key_down(key)` | |
| `keyUp(key)` | `pag.keyboard.key_up(key)` | |
| `hotkey(*keys)` / `shortcut(*keys)` | `pag.keyboard.hotkey(*keys)` | |
| `hold(key)` | `pag.keyboard.hold(key)` | |
| `isValidKey(key)` | `pag.keyboard.is_valid_key(key)` | |
| *(not available)* | `pag.keyboard.codepoint(cp)` | New in v2 |

#### Screen

| v1 | v2 | Notes |
|---|---|---|
| `screenshot()` | `pag.screen.screenshot()` | |
| `size()` / `resolution()` | `pag.screen.get_size()` | |
| *(not available)* | `pag.screen.get_size_max()` | New in v2 |
| `pixel(x, y)` | `pag.screen.pixel(x, y)` | |
| `pixelMatchesColor(x, y, c)` | `pag.screen.pixel_matches_color(x, y, c)` | |
| `locate(img)` | `pag.screen.locate(img)` | |
| `locateOnScreen(img)` | `pag.screen.locate_on_screen(img)` | |
| `locateAllOnScreen(img)` | `pag.screen.locate_all_on_screen(img)` | |
| `locateCenterOnScreen(img)` | `pag.screen.locate_center_on_screen(img)` | |
| `center(box)` | `pag.screen.center(box)` | |
| `getActiveWindow()` | `pag.screen.get_active_window()` | |
| `getActiveWindowTitle()` | `pag.screen.get_active_window_title()` | |
| `getAllWindows()` | `pag.screen.get_all_windows()` | |
| `getAllTitles()` | `pag.screen.get_all_titles()` | |

#### Dialogs

| v1 | v2 | Notes |
|---|---|---|
| `alert(text)` | `pag.dialogs.alert(text)` | |
| `confirm(text)` | `pag.dialogs.confirm(text)` | |
| `prompt(text)` | `pag.dialogs.prompt(text)` | |
| `password(text)` | `pag.dialogs.password(text)` | |

---

### Removed features

#### `run()` — the mini scripting language

PyAutoGUI v1 had an undocumented `run()` function that parsed a string
as a sequence of commands. It is **not supported** in v2 and will raise
`NotImplementedError` if called.

```python
# v1 only — will NOT work in v2
pyautogui.run("ccg-20,+0c")  # ❌ NotImplementedError
```

There is no direct replacement — use the standard API instead:

```python
pag.pointer.click()
pag.pointer.click()
pag.pointer.move_rel(-20, 0)
pag.pointer.click()
```

---

## What's new in v2

A few things worth knowing if you're moving beyond the compatibility layer:

- **`codepoint()`** — type any Unicode character directly by codepoint,
  without relying on keyboard layout:
  ```python
  pag.keyboard.codepoint(0x1F642)  # 🙂
  pag.keyboard.codepoint("U+263A") # ☺
  ```

- **OOP structure** — controllers are proper objects. You can pass them
  around, inspect them, and extend them:
  ```python
  kb = pag.keyboard
  kb.write("hello")
  kb.hotkey("ctrl", "s")
  ```

---

## Migration checklist

Not sure where to start? Go through this list:

- [ ] Replace `import pyautogui as pag` with `from pyautogui2 import PyAutoGUI` and `pag = PyAutoGUI()`
- [ ] Replace `pyautogui.PAUSE = x` with `pag.PAUSE = x`
- [ ] Replace `pyautogui.FAILSAFE = x` with `pag.FAILSAFE = x`
- [ ] Update function calls using the tables above (camelCase → snake_case, add controller prefix)
- [ ] Update argument names where needed (`xOffset` → `offset_x`, `mouseDownUp` → `mouse_down_up`)
- [ ] Remove any usage of `run()` and rewrite as explicit API calls
- [ ] (Optional) Stop using the flat API and switch fully to `pag.pointer / pag.keyboard / ...`
