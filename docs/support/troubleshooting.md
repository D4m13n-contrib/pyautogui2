# Troubleshooting

This guide helps you diagnose and fix the most common issues with PyAutoGUI2.

- **Installation issues** → [Section 1](#1-installation-issues)
- **Runtime issues** → [Section 2](#2-runtime-issues)
- **FailSafe / PAUSE behaviour** → [Section 3](#3-global-behavior)

> **Platform-specific issues** (Linux permissions, Wayland setup, MacOS accessibility, etc.)
> are covered in the [Platform Guides](../platforms/index.md).

---

## 1. Installation Issues

### ImportError / ModuleNotFoundError

**Symptom:**
```python
ImportError: No module named 'pyautogui2'
```

**Cause:** PyAutoGUI2 is not installed in the active Python environment.

**Fix:**

**Not yet available**

```bash
pip install pyautogui2
```

If you use multiple Python versions or virtual environments, make sure you're installing into the right one:
```bash
python -m pip install pyautogui2   # use the exact Python you run scripts with
```

---

### Missing system dependencies (Linux)

**Symptom:** Installation succeeds but importing raises an error about a missing native library (`python3-xlib`, `python3-uinput`, etc.).

**Fix:** Install the required system packages. The exact list depends on your display server and desktop environment.

> See [Linux Installation](../platforms/linux/installation.md) for the full dependency list.

---

### Permission errors (Linux / MacOS)

**Symptom:** Import succeeds but the first API call raises a `PermissionError` or similar.

**Cause:**
- **Linux:** Your user may not have access to `/dev/uinput` or the GNOME Shell extension may not be enabled.
- **MacOS:** Accessibility permissions have not been granted to your terminal or application.

**Fix:** Grant the required permissions before running your script.

> See [Linux Installation](../platforms/linux/installation.md) or [MacOS Installation](../platforms/macos/installation.md) for step-by-step instructions.

---

## 2. Runtime Issues

### 2.1 Pointer

#### Mouse doesn't move

**Symptom:** Calling `pag.pointer.move_to()` or `pag.pointer.click()` has no visible effect.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| The target application captures input exclusively (e.g. a game) | Switch the application to windowed mode |
| On Linux/Wayland: missing compositor support | Check [Platform Guides](../platforms/index.md) for your compositor |
| On MacOS: accessibility not granted | Grant access in *System Settings → Privacy → Accessibility* |
| On Windows: UAC prompt is in the foreground | Dismiss the UAC prompt first; PyAutoGUI2 cannot interact with elevated windows |

---

#### Click has no effect

**Symptom:** The mouse moves correctly but the click does not register in the target application.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| Application requires focus before accepting input | Call `move_to()` first, wait briefly, then click |
| `duration` too short, click lands before the window is ready | Add a short `time.sleep()` before the click |
| Wrong button used | Check you are passing the correct `button` argument (`"left"`, `"right"`, `"middle"`) |

---

#### Wrong coordinates (multi-monitor)

**Symptom:** Clicks land in the wrong location on a multi-monitor setup or high-DPI display.

**Cause:** Coordinates are always expressed in the global screen space (origin at top-left of the primary monitor). Secondary monitors have offsets.

**Fix:**
```python
# Check the size and position of each display
displays = pag.screen.get_displays()
for d in displays:
    print(d)  # Shows position and resolution of each display
```

> See [Platform Guides](../platforms/index.md) for known DPI scaling issues per OS.

---

### 2.2 Keyboard

#### Keys not typed / nothing appears

**Symptom:** `pag.keyboard.write()` or `pag.keyboard.press_key()` runs without error but no text appears.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| No window has keyboard focus | Click the target field first with `pag.pointer.click()` |
| Application ignores synthetic input (e.g. password field, game) | Use the application's own API or a dedicated automation tool |
| On Linux/Wayland: missing permissions or extension not active | Check [Platform Guides](../platforms/index.md) |

---

#### Wrong characters typed

**Symptom:** `pag.keyboard.write("hello")` types unexpected characters (e.g. `"hewwq"` on AZERTY).

**Cause:** PyAutoGUI2 maps key names to scancodes based on your **active keyboard layout**. If the layout detected at runtime does not match the physical layout in use, characters will be wrong.

**Fix:** Verify your system keyboard layout matches what PyAutoGUI2 detects.

> - For usage details, see [Keyboard Guide → write()](../guides/keyboard.md).
> - For layout mapping per OS, see [Platform Guides](../platforms/index.md).

---

#### Hotkey has no effect

**Symptom:** `pag.keyboard.hotkey("ctrl", "c")` does nothing.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| Target window does not have focus | Click the window first |
| Key names are wrong | Check valid key names in [Keyboard Guide](../guides/keyboard.md) |
| Another application intercepts the shortcut globally | Disable conflicting global shortcuts temporarily |

---

### 2.3 Screen

#### Screenshot returns a black image

**Symptom:** `pag.screen.screenshot()` returns an all-black `PIL.Image`.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| On Linux/Wayland: compositor does not support screen capture | Check [Platform Guides](../platforms/index.md) for your compositor |
| On Windows: hardware-accelerated or DRM-protected content | This is a system-level restriction — no workaround |
| Running in a headless environment (CI, SSH) | Use a virtual display (e.g. `Xvfb` on Linux) |

---

#### `locate_on_screen()` always returns `None`

**Symptom:** The image is visually present on screen but `locate_on_screen()` returns `None`.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| `confidence` threshold too high | Lower it: `confidence=0.8` instead of `0.95` |
| Display scaling changes pixel size | Capture the template at the same scale as the screen |
| Template image has compression artefacts | Re-capture the template with `pag.screen.screenshot()` |
| Template was captured on a different DPI / OS | Recapture on the target machine |

```python
# Quick debug: check what the screen actually looks like
screenshot = pag.screen.screenshot()
screenshot.save("debug_screenshot.png")  # Inspect this file manually
```

---

#### `pixel()` returns wrong color

**Symptom:** `pag.screen.pixel(x, y)` returns an unexpected RGB value.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| Display color profile / HDR alters values | Disable HDR or color profiles for testing |
| Coordinates are off (DPI scaling) | Verify coordinates with `pag.pointer.get_position()` while hovering the pixel |
| The pixel changed between the call and your expectation | Capture a screenshot first, then read from it |

```python
# Read pixel from a captured screenshot instead of live screen
screenshot = pag.screen.screenshot()
r, g, b = screenshot.getpixel((x, y))
```

---

### 2.4 Dialogs

#### Dialog doesn't appear

**Symptom:** `pag.dialogs.alert()` or similar returns immediately without showing anything.

**Possible causes and fixes:**

| Cause | Fix |
|---|---|
| Running in a headless environment | Dialogs require a graphical display — not usable in CI/headless |
| On Linux: `tkinter` is not installed | Install it: `sudo apt install python3-tk` (Debian/Ubuntu) |

---

#### Dialog appears behind other windows

**Symptom:** The dialog opens but is hidden behind the current foreground window.

**Cause:** Window stacking order is managed by the OS; PyAutoGUI2 cannot force a dialog to the front on all platforms.

**Fix:** Minimise other windows before calling the dialog, or check `platforms/index.md` for platform-specific workarounds.

---

## 3. Global Behavior

### 3.1 FailSafe

**Symptom:** Your script raises `FailSafeException` unexpectedly.

```
pyautogui2.utils.exceptions.FailSafeException: PyAutoGUI2 fail-safe triggered.
```

**Cause:** The mouse reached a corner of the screen (top-left, top-right, bottom-left, or bottom-right). This is intentional — it lets you interrupt a runaway script by moving the mouse to a corner.

**Fix (recommended):** Add pauses between actions so you can interrupt cleanly:

```python
import time

pag.pointer.move_to(500, 300)
time.sleep(0.5)
pag.pointer.click()
```

**Fix (disable — use with caution):** You can disable the failsafe, but you lose the ability to interrupt a runaway script:

```python
pag.FAILSAFE = False  # ⚠️ Not recommended for long-running scripts
```

> See [Settings Guide](../guides/settings.md) for full configuration details.

---

### 3.2 PAUSE

**Symptom:** Your script runs too fast and actions are missed by the target application.

**Cause:** By default, there is no automatic pause between PyAutoGUI2 calls. Some applications need time to react.

**Fix (per call):** Use `time.sleep()` between calls:

```python
pag.pointer.click(500, 300)
time.sleep(0.3)
pag.keyboard.write("hello")
```

**Fix (global):** Set `PAUSE` to insert an automatic delay after every PyAutoGUI2 call:

```python
pag.PAUSE = 0.2  # 200ms after every call
```

> See [Settings Guide](../guides/settings.md) for full configuration details.

---

## 4. Still Stuck?

If none of the above solves your issue:

1. **Check the platform guide** for your OS — many issues are platform-specific:
   [Platform Guides](../platforms/index.md)

2. **Run the verification tool** to confirm your installation is healthy:
   ```bash
   pyautogui2-verify
   ```

3. **Open an issue** on GitHub with:
   - Your OS, Python version, and PyAutoGUI2 version
   - The full traceback
   - A minimal reproducible script
