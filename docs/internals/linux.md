# Linux Internals — Part Composition

This document explains how PyAutoGUI2 assembles its Linux backend at runtime.
It is intended for contributors who need to understand, extend, or debug the
Linux-specific code.

---

## Overview

Linux desktop environments are highly fragmented. The same machine can run
GNOME or KDE, on X11 or Wayland, with or without a specific compositor. Rather
than maintaining one monolithic class per combination, PyAutoGUI2 uses
**dynamic class composition**: small, focused `Part` classes are assembled at
runtime into a single concrete class that exactly matches the detected environment.

---

## The Four Part Categories

Each Linux backend class (pointer, keyboard, screen, dialogs) is composed from
up to four Parts, assembled in a fixed order:

| # | Category | Role | Always present? |
|---|---|---|---|
| 1 | **Base** | Core Linux logic shared across all environments | ✅ Always |
| 2 | **Desktop Environment (DE)** | DE-specific behaviour (GNOME, KDE, XFCE…) | ✅ Always |
| 3 | **Display Server (DS)** | X11 or Wayland input/output primitives | ✅ Always |
| 4 | **Compositor** | Compositor-specific extensions (e.g. GNOME Shell) | ⚠️ Wayland only |

> **Rule:** Compositor is optional on X11 (not used), but mandatory on Wayland.
> The Wayland Part itself is responsible for resolving and requiring its Compositor.

---

## Assembly Mechanism

### 1. Detection

At startup, `get_platform_info()` inspects the running environment and returns
a dict with keys such as `linux_display_server`, `linux_desktop`, and
`linux_compositor`. Each sub-`__init__.py` uses these values to select the
correct Part class via a simple conditional import:

```python
# osal/linux/display_servers/__init__.py (simplified)
def get_display_server_osal_parts() -> dict[str, type]:
    server = get_linux_info()["linux_display_server"]

    if server == "wayland":
        from .wayland import get_wayland_osal_parts as _get_osal_parts
    elif server == "x11":
        from .x11 import get_x11_osal_parts as _get_osal_parts
    else:
        raise RuntimeError(f"Unsupported display server: {server}")

    return _get_osal_parts()
```

The same pattern applies for desktop environment detection and, when on Wayland,
compositor detection. Each level delegates to the level below it — the Wayland
loader is the one that resolves the Compositor Part, not the top-level assembler.

### 2. Collection cascade

`osal/linux/__init__.py` orchestrates the full assembly:

1. It instantiates the **Base** Part directly.
2. It calls `osal/linux/desktops/__init__.py` → returns the **DE** Part.
3. It calls `osal/linux/display_servers/__init__.py` → returns the **DS** Part.
   - If the display server is Wayland, the Wayland loader additionally calls
     `osal/linux/display_servers/wayland/compositor/__init__.py` to resolve the
     **Compositor** Part, which is then merged into (or composed with) the DS Part
     before being returned.

### 3. Dynamic class creation

Once all Parts are collected, `_compose_linux_class()` builds the final class
using Python's built-in `type()`:

```python
cls_name = f"Linux{name.capitalize()}"          # e.g. "LinuxPointer"
cls_bases = (base_part, desktop_part, display_part)

cls = type(
    cls_name,
    cls_bases,
    {
        "BACKEND_ID": ", ".join(
            getattr(b, "BACKEND_ID", b.__name__) for b in cls_bases
        ),
        "__doc__": f"Concrete Linux {name.capitalize()} implementation "
                   f"({cls_bases[0].__name__}, {cls_bases[1].__name__}, "
                   f"{cls_bases[2].__name__}).",
    },
)
```

The MRO order is fixed and intentional:

```
LinuxPointer
 └── BasePart          ← 1st: core shared logic
 └── DEPart            ← 2nd: desktop-specific overrides
 └── DSPart            ← 3rd: display server primitives
      └── CompositorPart  (merged into DSPart on Wayland)
```

Each Part covers a distinct set of responsibilities — there is intentionally
no method overlap between `BasePart`, `DEPart`, and `DSPart`. The MRO order
therefore has no practical effect on method resolution in normal operation.
It matters only if you introduce a deliberate override in a new Part, in
which case place it earlier in the base tuple to give it precedence.

### 4. Validation

After composition, the assembler verifies that all abstract methods declared in
the `Abstract*` base class are concretely implemented in the final class. If any
method is missing, a `TypeError` is raised at initialization time — not at the
moment the method is first called. This means an unsupported or incomplete
combination fails immediately and loudly, rather than silently at runtime.

---

## Adding a New Part

### Adding a new Desktop Environment

1. Create `osal/linux/desktops/<name>/` with the four component modules:
   `pointer.py`, `keyboard.py`, `screen.py`, `dialogs.py`.
2. Each module defines a `<Name>PointerPart` (etc.) class that inherits from
   the corresponding `Abstract*` class. Implement only the methods that differ
   from the base or other Parts — leave the rest to MRO resolution.
3. Register the new desktop in `osal/linux/desktops/__init__.py` by adding a
   branch to `_detect_desktop()` and returning the new Parts from
   `get_desktop_osal_parts()`.

### Adding a new Display Server

Follow the same pattern as DE, but under `osal/linux/display_servers/`.
If the new display server requires a compositor, add a `compositor/` subdirectory
and follow the Wayland compositor pattern.

### Adding a new Compositor (Wayland only)

1. Create `osal/linux/display_servers/wayland/compositor/<name>/` with the four
   component modules.
2. Register it in `osal/linux/display_servers/wayland/compositor/__init__.py`.

---

## Method Resolution — Practical Guide

When debugging or overriding a method, the resolution order matters. Given:

```
LinuxPointer(BasePart, DEPart, DSPart)
```

Python resolves methods left to right, depth first (C3):

- `BasePart.some_method()` → called first if defined there
- `DEPart.some_method()` → called if not in `BasePart`
- `DSPart.some_method()` → called if not in either

To verify the actual MRO at runtime:

```python
from pyautogui2 import PyAutoGUI
gui = PyAutoGUI()
print(type(gui.pointer._osal).__mro__)
```

---

## What the Compositor Part Is Not

The Compositor Part is **not** a fourth independent layer in the MRO. On Wayland,
it is resolved inside the Wayland DS loader and contributes its methods as part of
the DS slot. From the top-level assembler's perspective, there are always exactly
three bases: `(BasePart, DEPart, DSPart)`. The Compositor is an implementation
detail of how the Wayland DS Part is built.

---

## Related

- [Platform guide — Linux](../platforms/linux/installation.md) — installation and
  system requirements
- [Platform guide — Wayland](../platforms/linux/wayland.md) — Wayland-specific
  setup and the GNOME Shell extension
- [Contributing guide](../support/contributing.md) — general contribution workflow
