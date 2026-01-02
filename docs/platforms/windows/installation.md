# Windows Platform Guide

---

## Overview

PyAutoGUI2 on Windows uses **pure ctypes** to interact with the Win32 API. No external dependencies like `pywin32` are required — everything is handled through direct DLL calls.

**Supported versions:** Windows 10 / 11 (Windows 8.1 may work but is not officially supported)

---

## System Requirements

- **OS:** Windows 10 or Windows 11
- **Python:** 3.10+
- **Architecture:** 32-bit or 64-bit

---

## Installation

### System Dependencies

PyAutoGUI2 on Windows has **no external system dependencies**. The required DLLs (`user32.dll`, `kernel32.dll`) are part of Windows and loaded automatically.

### Python Package

**Not yet available**

```bash
pip install pyautogui2
```

See the [Installation Guide](../../get-started/installation.md) for detailed instructions.

---

## Verification

After installation, verify your setup:

```bash
pyautogui2-verify
```

See [Installation Guide — Verification](../../get-started/installation.md#verification) for details.

---

## Known Limitations

### 1. UAC (User Account Control) prompts

PyAutoGUI2 cannot interact with elevated windows or UAC prompts. This is a Windows security restriction (UIPI — User Interface Privilege Isolation).

**Workaround:** Run your script as administrator — but only if strictly necessary, as this carries security risks.

```powershell
Start-Process python -ArgumentList "your_script.py" -Verb RunAs
```

---

### 2. Fullscreen games and DirectX applications

Mouse and keyboard input may not be captured by applications using exclusive input modes or DirectX overlays.

**Workaround:** Switch the target application to windowed mode.

---

### 3. Virtual machines

Input events may be intercepted by the host OS instead of the VM.

**Workaround:** Ensure the VM window has focus and input capture is enabled in your VM software.

---

## Troubleshooting

### `ImportError: No module named 'ctypes'`

Indicates a broken Python installation. Reinstall Python from [python.org](https://www.python.org/).

---

### `OSError: [WinError 126] The specified module could not be found`

Indicates missing or corrupted Windows system DLLs. Run the System File Checker:

```cmd
sfc /scannow
```

---

### Coordinates are off on a high-DPI display

PyAutoGUI2 enables DPI awareness automatically. If coordinates are still incorrect, verify that the reported screen size matches your actual resolution:

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()
print(pag.screen.get_size())  # Should match your display resolution
```

If the values are wrong, please open a bug report on [GitHub](https://github.com/D4m13n-contrib/pyautogui2/issues).

---

## See Also

- [Installation Guide](../../get-started/installation.md) — complete setup instructions
- [Quick Start](../../get-started/quickstart.md) — first steps with PyAutoGUI2
- [Platform Support](../index.md) — platform comparison and feature matrix
- [Windows SendInput — Microsoft Docs](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
