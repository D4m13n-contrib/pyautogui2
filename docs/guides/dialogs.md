# Dialogs

Display native dialog boxes to interact with the user during automation.

---

## Overview

PyAutoGUI2 provides four dialog types for user interaction:

| Method | Purpose | Returns |
|---|---|---|
| `alert()` | Display a message with a single button | `str` (button label) |
| `confirm()` | Ask a question with multiple buttons | `str` or `None` |
| `prompt()` | Request text input | `str` or `None` |
| `password()` | Request masked text input | `str` or `None` |

All dialogs are **blocking** — execution pauses until the user responds or the dialog times out.

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
```

---

## Basic Usage

### alert()

Display a message with a single confirmation button.

```python
pag.dialogs.alert("Operation complete!")

# With custom title and button label
pag.dialogs.alert("File saved.", title="Success", button="Got it")
```

**Returns:** the label of the button clicked (e.g. `"OK"`).

---

### confirm()

Ask a question with multiple buttons. Default buttons are `OK` and `Cancel`.

```python
result = pag.dialogs.confirm("Do you want to continue?")

if result == "OK":
    pass  # user confirmed
elif result is None:
    pass  # dialog was dismissed (timeout or closed)

# Custom buttons
result = pag.dialogs.confirm(
    "Save changes before closing?",
    title="Unsaved Changes",
    buttons=("Save", "Discard", "Cancel"),
)
```

**Returns:** the label of the button clicked, or `None` if dismissed.

---

### prompt()

Request a single line of text input from the user.

```python
name = pag.dialogs.prompt("Enter your name:")

if name is not None:
    pag.keyboard.write(f"Hello, {name}!")

# With a pre-filled default value
path = pag.dialogs.prompt("Output directory:", default="/tmp/output")
```

**Returns:** the entered string, or `None` if the user cancelled.

---

### password()

Request text input with masked characters. Identical to `prompt()` except input is hidden.

```python
secret = pag.dialogs.password("Enter your password:")

# Custom mask character
secret = pag.dialogs.password("PIN:", mask="•")
```

**Returns:** the entered string, or `None` if the user cancelled.

---

## Timeout

All four dialogs accept an optional `timeout` parameter (in seconds). If the user does not
respond within the given duration, the dialog closes and returns `None`.

```python
# Auto-dismiss after 10 seconds
result = pag.dialogs.confirm("Continue?", timeout=10.0)

if result is None:
    print("No response — skipping.")
```

---

## Best Practices

**Use `confirm()` before irreversible actions**

```python
if pag.dialogs.confirm("Delete all files?", buttons=("Delete", "Cancel")) == "Delete":
    delete_all()
```

**Always handle `None` returns**

`confirm()`, `prompt()`, and `password()` return `None` when the user cancels or the
dialog times out. Skipping this check is a common source of `AttributeError`.

```python
# ❌ Risky
name = pag.dialogs.prompt("Your name:")
pag.keyboard.write(name.strip())  # crashes if None

# ✅ Safe
name = pag.dialogs.prompt("Your name:")
if name is not None:
    pag.keyboard.write(name.strip())
```

**Keep messages short and actionable**

```python
# ❌ Vague
pag.dialogs.alert("An error has occurred in the system.")

# ✅ Clear
pag.dialogs.alert("Could not write to /tmp/output — check permissions.", title="Write Error")
```

---

## Common Pitfalls

**Dialogs block the entire script**

There is no background execution while a dialog is open. Do not open dialogs inside
time-sensitive loops.

**Window focus**

On some platforms (especially Linux/Wayland), the dialog may appear behind other windows.
If your script does not seem to pause, check whether the dialog opened off-screen or unfocused.

**`alert()` always returns a string — never `None`**

Unlike the other three methods, `alert()` always returns the button label. No `None` check needed.

---

## Related Documentation

- [Keyboard guide](keyboard.md) — type text after collecting user input
- [Pointer guide](pointer.md) — click UI elements before or after dialogs
