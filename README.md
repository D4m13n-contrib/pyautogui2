# PyAutoGUI2

[![CI](https://github.com/D4m13n-contrib/pyautogui2/workflows/CI/badge.svg)](https://github.com/D4m13n-contrib/pyautogui2/actions)
[![Coverage](https://codecov.io/github/D4m13n-contrib/pyautogui2/branch/main/graph/badge.svg?token=VUFQC3FIY2)](https://codecov.io/github/D4m13n-contrib/pyautogui2)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

**PyAutoGUI2** is a modern, cross-platform GUI automation library for Python — a complete rewrite of [PyAutoGUI](https://github.com/asweigart/pyautogui) with a clean object-oriented architecture, strict typing, and native Wayland support.

---

## ✨ Features

- 🖱️ **Mouse control** — move, click, drag, scroll
- ⌨️ **Keyboard control** — type text, press keys, hotkeys
- 📸 **Screen capture** — screenshots, image location, pixel reading
- 🪟 **Window management** — find, focus, resize windows
- 🐧 **Linux** — X11 (Xlib) and Wayland (UInput + compositor)
- 🪟 **Windows** — native Win32 API
- 🍎 **MacOS** — native Quartz/Cocoa
- 🎯 **Fully typed** — mypy strict, IDE-friendly

---

## 📦 Installation

**Not yet available**

```bash
pip install pyautogui2
```

> **Linux + Wayland (GNOME)?** An additional setup step is required.  
> See the [Linux installation guide](docs/platforms/linux/installation.md).

---

## 🚀 Quick Start

```python
from pyautogui2 import PyAutoGUI

pag = PyAutoGUI()

# Screen
size = pag.screen.get_size()
screenshot = pag.screen.screenshot()

# Mouse
pag.pointer.move_to(100, 100, duration=0.5)
pag.pointer.click()

# Keyboard
pag.keyboard.write("Hello, World!", interval=0.05)
pag.keyboard.hotkey("ctrl", "s")
```

---

## 📚 Documentation

| | |
|---|---|
| 📖 [Full Documentation](docs/index.md) | Full documentation |
| 🚀 [Quick Start](docs/get-started/quickstart.md) | Get up and running in 5 minutes |
| ⚙️ [API Reference](docs/api/) | Full API documentation |
| 🐧 [Linux Guide](docs/platforms/linux/installation.md) | X11 & Wayland setup |
| 🪟 [Windows Guide](docs/platforms/windows/installation.md) | Windows setup |
| 🍎 [MacOS Guide](docs/platforms/macos/installation.md) | MacOS setup |
| 🔄 [Migration from v1](docs/get-started/migration-v1-v2.md) | Upgrading from PyAutoGUI 0.9.x |
| 🏗️ [Architecture](docs/osal/) | Internals for contributors |

---

## 🤝 Contributing

Contributions are welcome. Please read the [contributing guide](docs/support/contributing.md) before opening a pull request.

```bash
git clone https://github.com/D4m13n-contrib/pyautogui2.git
cd pyautogui2
pip install -e ".[dev]"
pytest
```

---

## 📜 License

BSD-3-Clause — see [LICENSE.txt](LICENSE.txt).  
Original PyAutoGUI by [Al Sweigart](https://github.com/asweigart/pyautogui).
