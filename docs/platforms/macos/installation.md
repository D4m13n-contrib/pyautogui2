# MacOS Platform Guide

---

## Overview

PyAutoGUI2 on MacOS uses **PyObjC** to interact with Quartz Event Services and AppKit, providing native integration with MacOS's Accessibility API.

**Supported versions:** MacOS 12 (Monterey) or later (MacOS 13+ recommended)

---

## System Requirements

- **OS:** MacOS 12 (Monterey) or later
- **Python:** 3.10+
- **Architecture:** Intel (x86_64) and Apple Silicon (arm64)

---

## Installation

### System Dependencies

PyAutoGUI2 on MacOS requires **PyObjC**, which is installed automatically as a dependency:

**Not yet available**

```bash
pip install pyautogui2
```

No manual system-level installation is required.

See the [Installation Guide](../../get-started/installation.md) for detailed instructions.

---

## Verification

After installation, verify your setup:

```bash
pyautogui2-verify
```

See [Installation Guide — Verification](../../get-started/installation.md#verification) for details.

---

## Accessibility Permissions

MacOS requires explicit permission for any application that simulates input events (mouse, keyboard). Without it, PyAutoGUI2 will silently fail to move the cursor or send keystrokes.

### Granting permission

1. Open **System Settings** → **Privacy & Security** → **Accessibility**
2. Click the **+** button and add your terminal emulator (e.g. Terminal, iTerm2) or your Python executable
3. Ensure the toggle next to the application is **enabled**

> **Running from an IDE?** Grant permission to the IDE itself (e.g. PyCharm, VS Code), not to Python directly.

### Verifying permission

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# If accessibility is not granted, this will have no effect
pag.pointer.move_to(200, 200)
print(pag.pointer.get_position())  # Should print Point(x=200, y=200)
```

If the cursor does not move, accessibility permission has not been granted correctly.

### Revoking and re-granting

If you moved or reinstalled your terminal or IDE, MacOS may silently revoke the permission. Go back to **Privacy & Security → Accessibility**, remove the entry, and re-add it.

---

## Known Limitations

### 1. Screen recording permission (screenshots)

Taking screenshots requires the **Screen Recording** permission in addition to Accessibility.

**Grant it via:** System Settings → Privacy & Security → Screen Recording → add your terminal or IDE.

---

### 2. System Integrity Protection (SIP)

Some system-level windows (login screen, system dialogs) cannot be automated due to SIP. This is a MacOS security restriction and cannot be bypassed without disabling SIP, which is strongly discouraged.

---

### 3. Virtual machines

Input events may be intercepted by the host OS instead of the VM.

**Workaround:** Ensure the VM window has focus and input capture is enabled in your VM software.

---

## Troubleshooting

### Mouse or keyboard has no effect

The most common cause is a missing or revoked Accessibility permission. See [Accessibility Permissions](#accessibility-permissions) above.

---

### `ImportError` related to PyObjC

PyObjC requires a native build that matches your Python architecture. If you see import errors after installation:

```bash
pip uninstall pyobjc
pip install pyautogui2  # reinstalls with correct architecture
```

If you are using a virtual environment with Apple Silicon, ensure you are not mixing arm64 and x86_64 environments.

---

### Screenshots fail or return a blank image

Grant **Screen Recording** permission to your terminal or IDE:

**System Settings → Privacy & Security → Screen Recording**

Then restart your terminal or IDE — MacOS requires a full restart of the application after granting this permission.

---

### Coordinates are off on a Retina display

PyAutoGUI2 works in **logical pixels** on MacOS (not physical pixels). On a Retina display, one logical pixel corresponds to two physical pixels. This is the expected behavior and consistent across the API.

If coordinates are unexpectedly wrong, verify the reported screen size:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
print(pag.screen.get_size())  # Returns logical resolution, e.g. Size(width=1440, height=900) on a 2880×1800 Retina
```

---

## See Also

- [Installation Guide](../../get-started/installation.md) — complete setup instructions
- [Quick Start](../../get-started/quickstart.md) — first steps with PyAutoGUI2
- [Platform Support](../index.md) — platform comparison and feature matrix
- [MacOS Accessibility API — Apple Developer Docs](https://developer.apple.com/documentation/applicationservices/axuielement_h)
