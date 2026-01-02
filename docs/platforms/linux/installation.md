# Linux Platform Guide

---

## Overview

PyAutoGUI2 on Linux supports both **X11** and **Wayland** display servers, and integrates with
the most common desktop environments (GNOME, KDE, XFCE, and others).

**Supported versions:** Any modern Linux distribution with Python 3.10+

> Not sure which display server you are running?
> ```bash
> echo $XDG_SESSION_TYPE  # outputs "x11" or "wayland"
> ```

---

## System Requirements

- **OS:** Any modern Linux distribution (Ubuntu 22.04+, Fedora 38+, Arch, etc.)
- **Python:** 3.10+
- **Display server:** X11 or Wayland
- **Desktop environment:** GNOME, KDE, XFCE, or any DE that supports the dependencies below

---

## Installation

**Not yet available**

```bash
pip install pyautogui2
```

Depending on your display server and desktop environment, additional dependencies may be required.
See the sections below.

---

## Dependencies by Component

### X11

If you are running X11, install the following system-level dependency:

```bash
pip install python-xlib
```

This is required for mouse and keyboard control under X11. No further setup is needed.

See [X11 — Specifics and Limitations](x11.md) for more details.

---

### Wayland

Wayland does not expose a unified input API. PyAutoGUI2 uses **UInput** (Linux kernel input
subsystem) for mouse and keyboard simulation.

> **Compositor communication:** On Wayland, PyAutoGUI2 needs to query the compositor to retrieve
> three pieces of information: **pointer position**, **screen size**, and **keyboard layout**.
> This is read-only — the compositor is never used to simulate input or interact with the system.
> Behavior may therefore vary depending on which compositor you are running.
> See [Wayland — Compositor Support](wayland.md#compositor-support) for details.

See [Wayland — Specifics and Limitations](wayland.md#setup) for more details.

---

### GNOME

No additional dependency is required for basic GNOME support.

---

### KDE Plasma

No additional dependency is required.

---

### Other desktop environments

PyAutoGUI2 should work on any desktop environment that supports X11 or UInput (Wayland). If
you encounter issues with an unsupported DE, please open an issue on
[GitHub](https://github.com/D4m13n-contrib/pyautogui2/issues).

---

## Verification

After installation, verify your setup:

```bash
pyautogui2-verify
```

See [Installation Guide — Verification](../../get-started/installation.md#verification) for
details.

---

## Known Limitations

### 1. Wayland compositor support

Not all Wayland compositors are supported. Since PyAutoGUI2 must query the compositor to
retrieve pointer position, screen size, and keyboard layout, unsupported compositors will
cause initialization to fail. See [Wayland — Compositor Support](wayland.md#compositor-support)
for the full compatibility matrix.

---

### 2. Root and headless environments

Running PyAutoGUI2 as `root` or in a headless environment (no display server, e.g. a plain SSH
session) is not supported and will raise an exception on initialization.

If you need automation in a CI environment, use a virtual display:

```bash
# Install Xvfb
sudo apt install xvfb

# Run your script with a virtual display
xvfb-run python your_script.py
```

---

### 3. Snap and Flatpak sandboxing

If your Python environment is installed via Snap or Flatpak, it may be sandboxed and unable to
access `/dev/uinput`. Use a standard system Python or a virtual environment created outside
the sandbox.

---

## Troubleshooting

### "Permission denied: /dev/uinput"

UInput permissions are not correctly configured. Follow the [UInput setup](#wayland) steps
above, then log out and back in.

---

### Mouse or keyboard has no effect on X11

Verify that `python-xlib` is installed and that your display server is actually X11:

```bash
echo $XDG_SESSION_TYPE  # should output "x11"
python -c "import Xlib; print('python-xlib OK')"
```

---

### GNOME Shell extension not working (Wayland)

The extension may not be installed or enabled. See
[Wayland — GNOME Shell Extension](wayland.md#gnome-shell).

---

## See Also

- [Installation Guide](../../get-started/installation.md) — complete setup instructions
- [Quick Start](../../get-started/quickstart.md) — first steps with PyAutoGUI2
- [X11 — Specifics and Limitations](x11.md)
- [Wayland — Specifics and Limitations](wayland.md)
- [Platform Support](../index.md) — platform comparison and feature matrix
