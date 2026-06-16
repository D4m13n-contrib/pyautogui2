# PyAutoGUI2 Documentation

Welcome to the official documentation for **PyAutoGUI2** — a modern, cross-platform desktop automation library for Python.

> 📦 New here? Start with the [Installation Guide](get-started/installation.md) or jump straight to the [Quickstart](get-started/quickstart.md).

---

## Get Started

| Document | Description |
|---|---|
| [Installation](get-started/installation.md) | Install PyAutoGUI2 on Windows, MacOS, or Linux |
| [Quickstart](get-started/quickstart.md) | Your first automation script in minutes |
| [Migration from v1](get-started/migration-v1-v2.md) | Upgrading from the original PyAutoGUI |
| [Legacy API](get-started/legacy-api.md) | Using the compatibility layer |

---

## Guides

Practical, copy-paste examples for common automation tasks.

| Document | Description |
|---|---|
| [Pointer](guides/pointer.md) | Mouse movement, clicks, drag & drop |
| [Keyboard](guides/keyboard.md) | Typing, hotkeys, key combinations |
| [Screen](guides/screen.md) | Screenshots, image search, pixel reading |
| [Dialogs](guides/dialogs.md) | Alert boxes, prompts, confirmations |

---

## API Reference

Full technical reference for contributors and advanced users.

| Document | Description |
|---|---|
| [PointerController](api/pointer.md) | Complete pointer API, limitations, internals |
| [KeyboardController](api/keyboard.md) | Complete keyboard API, limitations, internals |
| [ScreenController](api/screen.md) | Complete screen API, limitations, internals |
| [DialogsController](api/dialogs.md) | Complete dialogs API, limitations, internals |

---

## Platform Guides

Platform-specific installation details, known limitations, and troubleshooting.

| Document | Description |
|---|---|
| [Linux](platforms/linux/installation.md) | Linux setup — X11 and Wayland |
| [Windows](platforms/windows/installation.md) | Windows setup |
| [MacOS](platforms/macos/installation.md) | MacOS setup and permissions |

---

## Contributing

Contributions are welcome! Here's how to get started:

| Topic | Description |
|---|---|
| [Setting up a development environment](contributing/dev-environment.md) | Clone, install dev dependencies, run tests |
| [Architecture overview](contributing/architecture.md) | OSAL pattern, controller design, and key conventions |
| [Adding a new platform backend](contributing/new-platform.md) | Implementing OSAL interfaces for a new OS |
| [Adding Linux desktop/compositor support](contributing/linux-support.md) | Extending the Linux display server or desktop Parts |
| [Code style & conventions](contributing/code-style.md) | Ruff, mypy, typing, docstrings, and testing guidelines |

### Quick start

```bash
# Clone and install in dev mode
git clone https://github.com/D4m13n-contrib/pyautogui2.git
cd pyautogui2
pip install -e ".[dev]"

# Run tests (no hardware required)
python3 -m pytest -m "not real" --cov --cov-branch

# Lint and type-check
ruff check src/ tests/
mypy src/
```

### Guidelines

- **Tests**: Every new feature or fix must include tests. Coverage must remain at 100% (branches included).
- **Type hints**: All public functions must have type annotations. Mypy must pass in strict mode.
- **Docstrings**: Follow Google style. Public API methods require complete documentation.
- **Backward compatibility**: The legacy flat API (`pyautogui2.click()`, etc.) must continue to work.
- **Platform-specific code**: Never hardcode platform logic in controllers — use the OSAL abstraction layer.

---

*For bug reports, feature requests, and questions, open an issue on [GitHub](https://github.com/D4m13n-contrib/pyautogui2/issues).*
