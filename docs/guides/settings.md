# Settings Guide

PyAutoGUI2 exposes a set of global settings that control timing, safety, and logging behaviour.
This guide explains each setting, how to configure it, and when to use it.

---

## How Settings Work

Settings are defined in `pyautogui2/settings.py` with their default values.
When PyAutoGUI2 is first used, these values are read by internal managers
(such as `PauseManager`) to initialize their state.

There are two valid ways to configure settings:

### 1. Edit `settings.py` — static configuration

Modify the default values directly in `settings.py` before any PyAutoGUI2 instance is created.
This is suitable for project-wide defaults.

```python
# pyautogui2/settings.py
PAUSE_CONTROLLER_DURATION: float = 0.5   # increase default pause
FAILSAFE: bool = False                   # disable failsafe globally
```

> ⚠️ Modifying `settings.py` values **after** instantiation has no effect — internal
> managers have already read and cached these values.

### 2. Use instance properties — runtime configuration

The recommended way to change settings at runtime is through the `PyAutoGUI` instance:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

pag.PAUSE = 0.5      # update pause duration at runtime
pag.FAILSAFE = False # disable failsafe at runtime
```

These properties delegate to the internal managers and take effect immediately.

---

## Reference

### `PAUSE` / `PAUSE_CONTROLLER_DURATION`

```python
PAUSE_CONTROLLER_DURATION: float = 0.1  # seconds
```

Duration of the automatic pause inserted **after each controller-level call**
(`click()`, `write()`, `move_to()`, etc.).

This gives the target application time to process each action before the next one fires.

**Runtime:**
```python
pag.PAUSE = 0.0   # disable pauses entirely
pag.PAUSE = 0.5   # slow down for unreliable UIs
```

**Per-call override:**

Any call can override the global pause for that specific invocation:

```python
pag.pointer.click(100, 200, _pause=False)  # no pause after this call
pag.pointer.click(100, 200, _pause=0.5)   # 0.5s pause after this call only
```

> `_pause=False` disables the pause. `_pause=<float>` overrides the duration.
> This applies to all controller methods across pointer, keyboard, and screen.

---

### `PAUSE_OSAL_DURATION`

```python
PAUSE_OSAL_DURATION: float = 0.0  # seconds
```

Duration of the pause inserted after **each low-level OSAL operation**
(`key_down()`, `key_up()`, `move_raw()`, etc.).

By default this is `0.0` (no pause). Increase it only if you experience missed
inputs on slow or virtualized systems.

```python
# In settings.py — before instantiation only
PAUSE_OSAL_DURATION: float = 0.02
```

> This setting is **not** exposed as a `pag.` property. Configure it in `settings.py`
> before instantiation if needed.

---

### `FAILSAFE`

```python
FAILSAFE: bool = True
```

When enabled, moving the mouse to the **top-left corner of the screen** `(0, 0)`
raises a `FailSafeException`, immediately stopping the script.

This is a safety mechanism to regain control when automation runs away.

```python
pag.FAILSAFE = False  # disable (not recommended for long-running scripts)
pag.FAILSAFE = True   # re-enable
```

> ⚠️ Disabling `FAILSAFE` is discouraged. If your script enters an uncontrolled
> loop, you will have no easy way to interrupt it.

---

### `LOG_SCREENSHOTS`

```python
LOG_SCREENSHOTS: bool = False
```

When enabled, PyAutoGUI2 automatically captures and saves a screenshot after
each decorated action (clicks, key presses, etc.).

Useful for debugging automation scripts or building audit trails.

```python
# In settings.py
LOG_SCREENSHOTS = True
LOG_SCREENSHOTS_FOLDER = "debug_screenshots"
LOG_SCREENSHOTS_LIMIT = 50
```

---

### `LOG_SCREENSHOTS_FOLDER`

```python
LOG_SCREENSHOTS_FOLDER: str = "log_screenshots_output"
```

Directory where screenshots are saved when `LOG_SCREENSHOTS` is enabled.
Relative to the working directory of the script.

---

### `LOG_SCREENSHOTS_LIMIT`

```python
LOG_SCREENSHOTS_LIMIT: int = 10
```

Maximum number of screenshots to keep on disk. When the limit is reached,
the oldest files are deleted automatically (FIFO).

Set to `None` to disable the limit (unbounded growth — use with caution on
long-running scripts).

---

### `DARWIN_CATCH_UP_TIME`

```python
DARWIN_CATCH_UP_TIME: float = 0.01  # seconds
```

MacOS-specific timing constant. Adds a small delay after mouse moves and
key events to give the system interface time to catch up.

> This value may need adjustment on slower or faster MacOS systems.
> It affects `move_to()`, `drag_to()`, and key event duration on MacOS only.
> See [Platform Guide](../platforms/index.md) for MacOS-specific details.

---

### `PAUSE_DEBUG`

```python
PAUSE_DEBUG: bool = False
```

When enabled, prints timing information to stdout for each pause applied
by `PauseManager`. Intended for debugging pause behaviour — not for
production use.

```python
# In settings.py
PAUSE_DEBUG = True
```

Output example:
```
[PauseManager] controller pause: 0.1s after click()
[PauseManager] controller pause: 0.1s after write()
```

---

## Summary Table

| Setting | Default | Runtime (`pag.`) | Use case |
|---|---|---|---|
| `PAUSE_CONTROLLER_DURATION` | `0.1` | `pag.PAUSE` | Pause after each controller call |
| `PAUSE_OSAL_DURATION` | `0.0` | ❌ settings.py only | Pause after each low-level operation |
| `FAILSAFE` | `True` | `pag.FAILSAFE` | Emergency stop on corner move |
| `LOG_SCREENSHOTS` | `False` | ❌ settings.py only | Screenshot audit trail |
| `LOG_SCREENSHOTS_FOLDER` | `"log_screenshots_output"` | ❌ settings.py only | Screenshot output directory |
| `LOG_SCREENSHOTS_LIMIT` | `10` | ❌ settings.py only | Max screenshots on disk |
| `DARWIN_CATCH_UP_TIME` | `0.01` | ❌ settings.py only | MacOS timing adjustment |
| `PAUSE_DEBUG` | `False` | ❌ settings.py only | Debug pause timings |
