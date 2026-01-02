# Keyboard Control Guide

Complete guide to controlling the keyboard with PyAutoGUI2.

---

## Overview

PyAutoGUI2 provides the following functions for keyboard control:

| Function | Purpose | Example |
|----------|---------|---------|
| `write()` | Type text strings | `keyboard.write("Hello")` |
| `press_key()` | Press and release a single key | `keyboard.press_key("enter")` |
| `key_down()` | Press and hold a single key | `keyboard.key_down("ctrl")` |
| `key_up()` | Release a held key | `keyboard.key_up("ctrl")` |
| `hold()` | Hold one or more keys (context manager) | `keyboard.hold("ctrl", "shift")` |
| `hotkey()` | Press a key combination atomically | `keyboard.hotkey("ctrl", "c")` |
| `codepoint()` | Type a Unicode character by codepoint | `keyboard.codepoint(0x00E9)` |

**Key principle:** PyAutoGUI2 handles **keyboard layout mapping automatically**. You write what you want to type, and it works on any keyboard layout (QWERTY, AZERTY, QWERTZ, etc.).

---

## Basic Usage

### Typing Text

Use `write()` to type a string of text:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# Type a simple message
pag.keyboard.write("Hello, World!")

# Type with a delay between each character (in seconds)
pag.keyboard.write("Slow typing...", interval=0.1)

# Type special characters — layout is handled automatically
pag.keyboard.write("Price: $19.99")
pag.keyboard.write("[]{}@")  # AltGr combinations handled automatically
```

**How it works internally:**

For each character, `write()` calls `press_key()`, which:
1. Checks if the character is mapped to a physical key on your current keyboard layout → presses it directly
2. If not mapped (e.g. typing `"é"` on a QWERTY keyboard) → automatically falls back to `codepoint()` using the character's Unicode value
3. Same fallback applies to dead keys, to ensure they are always typed as the intended character

This is entirely transparent — you never need to handle this yourself.

> **Note (Linux only):** When the fallback to `codepoint()` is triggered, the input method uses
> `Ctrl+Shift+U+<codepoint>` internally. On some setups, this sequence may briefly flash on screen
> before the character appears. This is a visual artefact only and does not affect the output.

---

### Pressing Keys

Use `press_key()` to press and release a single named key:

```python
pag.keyboard.press_key("enter")
pag.keyboard.press_key("esc")
pag.keyboard.press_key("tab")
pag.keyboard.press_key("f5")
pag.keyboard.press_key("ctrl")  # Press and immediately release
```

For lower-level control, use `key_down()` and `key_up()` separately:

```python
pag.keyboard.key_down("shift")
pag.keyboard.press_key("a")  # Types "A"
pag.keyboard.key_up("shift")
```

> ⚠️ **Warning:** If an exception occurs between `key_down()` and `key_up()`, the key stays
> pressed. Prefer `hold()` whenever possible — it always releases the key, even on error.

Refer to the [Key Names Reference](#key-names-reference) for all valid key names.

---

### Holding Keys

Use `hold()` as a context manager to safely hold one or more keys:

```python
# Hold a single modifier
with pag.keyboard.hold("ctrl"):
    pag.keyboard.press_key("c")  # Ctrl+C

# Hold multiple modifiers simultaneously
with pag.keyboard.hold("ctrl", "shift"):
    pag.keyboard.press_key("i")  # Ctrl+Shift+I
```

The held keys are **always released** when the `with` block exits, even if an exception is raised.

---

### Key Combinations (Hotkeys)

Use `hotkey()` to press a key combination in a single call:

```python
pag.keyboard.hotkey("ctrl", "c")       # Copy
pag.keyboard.hotkey("ctrl", "v")       # Paste
pag.keyboard.hotkey("ctrl", "shift", "t")  # Reopen closed tab
pag.keyboard.hotkey("alt", "f4")       # Close window
```

Internally, `hotkey("ctrl", "c")` is equivalent to:

```python
with pag.keyboard.hold("ctrl", "c"):
    pass
```

Keys are pressed in order and released in reverse order, which matches the expected behaviour
for modifier combinations.

---

### Unicode Characters

Use `codepoint()` to type a character directly by its Unicode value, bypassing keyboard layout
mapping entirely:

```python
# Using an integer codepoint
pag.keyboard.codepoint(0x00E9)   # é
pag.keyboard.codepoint(0x1F642)  # 🙂

# Using a Unicode string notation
pag.keyboard.codepoint("U+00E9")   # é
pag.keyboard.codepoint("U+1F642")  # 🙂
```

In most cases you do not need to call `codepoint()` directly — `write()` falls back to it
automatically when a character is not available on your keyboard layout. Use `codepoint()`
explicitly when you want to type a specific Unicode character regardless of what `write()` would do.

---

## Key Names Reference

PyAutoGUI2 uses canonical key names as strings. Key names are **case-insensitive**.

### Modifier Keys

| Key name | Description |
|----------|-------------|
| `"ctrl"` | Control |
| `"shift"` | Shift |
| `"alt"` | Alt / Option (MacOS) |
| `"meta"` | Windows key / Command (MacOS) / Super (Linux) |
| `"altgr"` | AltGr (Right Alt) |

### Navigation Keys

| Key name | Description |
|----------|-------------|
| `"up"`, `"down"`, `"left"`, `"right"` | Arrow keys |
| `"home"`, `"end"` | Line start/end |
| `"pageup"`, `"pagedown"` | Page navigation |
| `"tab"` | Tab |

### Action Keys

| Key name | Description |
|----------|-------------|
| `"enter"` | Enter / Return |
| `"esc"` | Escape |
| `"backspace"` | Backspace |
| `"delete"` | Delete |
| `"insert"` | Insert |
| `"space"` | Space bar |
| `"capslock"` | Caps Lock |
| `"numlock"` | Num Lock |
| `"scrolllock"` | Scroll Lock |
| `"printscreen"` | Print Screen |
| `"pause"` | Pause / Break |

### Function Keys

`"f1"` through `"f24"`

### Numpad Keys

| Key name | Description |
|----------|-------------|
| `"num0"` – `"num9"` | Numpad digits |
| `"numdecimal"` | Numpad `.` |
| `"numadd"`, `"numsub"`, `"nummul"`, `"numdiv"` | Numpad operators |
| `"numenter"` | Numpad Enter |

### Single Characters

Any printable character can be passed directly as a string:

```python
pag.keyboard.press_key("a")
pag.keyboard.press_key("A")  # Equivalent to Shift+a
pag.keyboard.press_key("!")
```

---

## Pause Control

By default, a short pause is inserted after each PyAutoGUI2 call (configured globally via
`PAUSE`). You can override this per call using the `_pause` argument:

```python
# Use the global PAUSE value (default behaviour)
pag.keyboard.press_key("enter")

# Disable the pause for this specific call
pag.keyboard.press_key("enter", _pause=False)

# Override with a custom pause duration (in seconds) for this call only
pag.keyboard.press_key("enter", _pause=0.5)
```

This applies to all keyboard functions: `write()`, `press_key()`, `key_down()`, `key_up()`,
`hold()`, `hotkey()`, and `codepoint()`.

> See [Settings Guide](settings.md) for global configuration of `PAUSE`.

---

## Common Pitfalls

### 1. Using `key_down()` without `key_up()`

```python
# ❌ Dangerous — Ctrl stays pressed if an exception occurs
pag.keyboard.key_down("ctrl")
pag.keyboard.press_key("c")
pag.keyboard.key_up("ctrl")

# ✅ Safe — key is always released
with pag.keyboard.hold("ctrl"):
    pag.keyboard.press_key("c")
```

### 2. Caps Lock interference

`write()` types characters as-is and does not check the Caps Lock state. If Caps Lock is active,
lowercase letters will be sent as uppercase.

```python
# ❌ Types "HELLO" if Caps Lock is ON
pag.keyboard.write("hello")

# Toggle Caps Lock off before typing if needed
pag.keyboard.press_key("capslock")
pag.keyboard.write("hello")  # ✅ Now types "hello"
```

### 3. Unsupported keyboard layouts

PyAutoGUI2 supports the most common layouts (QWERTY, AZERTY, QWERTZ, and others). If your layout
is not supported, `write()` will still work for characters that have a Unicode fallback via
`codepoint()`, but named key mapping for `press_key()` may be incomplete.

> See [Platform Installation Guides](../platforms/index.md) for the list of supported layouts
> per platform and instructions for adding layout support.

---

## Related Documentation

- [Pointer Control](pointer.md) — mouse movement, clicks, and scrolling
- [Screen Capture](screen.md) — screenshots and image location
- [Settings Guide](settings.md) — `PAUSE`, and global configuration
- [Platform Installation Guides](../platforms/index.md) — supported layouts per platform
```
