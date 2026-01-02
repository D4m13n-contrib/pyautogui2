# Platform Support

PyAutoGUI2 runs on **Windows**, **MacOS**, and **Linux**. This page summarizes what is supported on each platform and links to platform-specific installation guides.

---

## Support Matrix

| Platform | Status |
|---|---|
| Windows | ✅ Supported |
| MacOS | ✅ Supported |
| Linux | |
| &nbsp;└── X11 | ✅ Supported |
| &nbsp;└── Wayland | |
| &nbsp;&nbsp;└── GNOME Shell (Mutter) | ✅ Supported |
| &nbsp;&nbsp;└── KDE Plasma (KWin) | 🔲 Planned |
| &nbsp;&nbsp;└── Cinnamon (Muffin) | 🔲 Planned |
| &nbsp;&nbsp;└── MATE (Marco) | 🔲 Planned |
| &nbsp;&nbsp;└── Xfce (Xfwm) | 🔲 Planned |
| &nbsp;&nbsp;└── wlroots (Sway, Hyprland…) | 🔲 Planned |

---

## Windows

- **Supported versions:** Windows 10, Windows 11
- **Dependencies:** none beyond the base package
- **Installation guide:** [Windows installation](windows/installation.md)

---

## MacOS

- **Supported versions:** MacOS 11 (Big Sur) and later
- **Dependencies:** none beyond the base package
- **Permissions required:** Accessibility access must be granted manually — see the installation guide for details
- **Installation guide:** [MacOS installation](macos/installation.md)

---

## Linux

Linux support depends on your **display server** (X11 or Wayland) and, for Wayland, your **compositor**.

### Detecting your configuration

```bash
pyautogui2-detect-platform
```

Example output:

```
OS                  : Linux
OS Identifier       : linux
OS Release          : 6.8.0-106-generic
Python Version      : 3.12.3
Architecture        : x86_64
Display Server      : wayland
Desktop Environment : GNOME
Compositor          : gnome_shell
```

### X11

X11 is the traditional Linux display server. PyAutoGUI2 supports it fully with no compositor-specific requirements.

- **Dependencies:** `python3-xlib`
- **Installation guide:** [Linux / X11](linux/x11.md)

### Wayland

Wayland support requires a **compositor-specific backend**. PyAutoGUI2 currently supports **GNOME Shell (Mutter)** only.

#### How the Wayland backend works

On Wayland, applications cannot access pointer position or keyboard layout information directly — the compositor controls this data. PyAutoGUI2 uses a **GNOME Shell extension** to expose the following information over D-Bus:

- Current cursor position
- Active keyboard layout
- Connected screen sizes and positions

> **Note:** Screen capture is handled independently by [pyscreeze](https://github.com/asweigart/pyscreeze) and does not require the extension.

- **Installation guide:** [Linux / Wayland](linux/wayland.md)

---

## Feature Availability by Platform

| Feature | Windows | MacOS | Linux / X11 | Linux / Wayland (GNOME) |
|---|---|---|---|---|
| Mouse movement & clicks | ✅ | ✅ | ✅ | ✅ |
| Keyboard input | ✅ | ✅ | ✅ | ✅ |
| Screen capture | ✅ | ✅ | ✅ | ✅ |
| Pixel reading | ✅ | ✅ | ✅ | ✅ |
| Image search | ✅ | ✅ | ✅ | ✅ |
| Cursor position | ✅ | ✅ | ✅ | ✅ ¹ |
| Screen size detection | ✅ | ✅ | ✅ | ✅ ¹ |
| Keyboard layout detection | ✅ | ✅ | ✅ | ✅ ¹ |
| Window management | ✅ | ✅ | ⚠️ ² | ⚠️ ² |
| Native dialogs | ✅ | ✅ | ✅ | ✅ |

**¹** Requires the PyAutoGUI2 GNOME Shell extension — see [Linux / Wayland](linux/wayland.md).
**²** Uses `pygetwindow` that not supports Linux.
