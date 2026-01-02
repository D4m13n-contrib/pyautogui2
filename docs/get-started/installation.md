# Installation Guide

> 📦 **PyPI release coming soon.** In the meantime, install directly from the GitHub repository (see below).

---

## Requirements

- **Python:** 3.10 or higher
- **OS:** Windows 10/11 — MacOS 10.13+ — Linux (X11 or Wayland)

---

## Installation

### From GitHub (current)

```bash
pip install git+https://github.com/D4m13n-contrib/pyautogui2.git
```

### From PyPI

**Not yet available**

```bash
pip install pyautogui2
```

---

## Platform-Specific Setup

PyAutoGUI2 requires additional system dependencies depending on your OS.  
**Follow your platform guide before using the library:**

| Platform | Guide |
|---|---|
| 🐧 Linux | [Linux Installation](../platforms/linux/installation.md) |
| 🪟 Windows | [Windows Installation](../platforms/windows/installation.md) |
| 🍎 MacOS | [MacOS Installation](../platforms/macos/installation.md) |

---

## Verify Your Installation

Run the following snippet to confirm everything is working:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
print(f"My cursor is at {pag.pointer.get_position()} on a screen of size {pag.screen.get_size()}")
```

Expected output (values depend on your setup):

```
My cursor is at Point(742, 451) on a screen of size Size(width=1920, height=1080)
```

---

## Next Steps

- [Quickstart](quickstart.md) — your first automation script
- [Pointer Guide](../guides/pointer.md) — mouse control
- [Keyboard Guide](../guides/keyboard.md) — typing and hotkeys
- [Screen Guide](../guides/screen.md) — screenshots and image search
