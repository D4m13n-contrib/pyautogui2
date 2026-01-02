# OSAL Internals

This document explains how the OS Abstraction Layer (OSAL) works internally:
the class hierarchy, the decorator injection mechanism, the Linux composition
pattern, and how to add a new platform backend.

---

## Overview

The OSAL is the layer between the public controllers (`PointerController`,
`KeyboardController`, etc.) and the actual OS-level calls. Each controller
holds a reference to an OSAL component and delegates every low-level operation
to it:

```

PointerController._osal  →  AbstractPointer  →  (MacOSPointer | WindowsPointer | LinuxPointer)

```

The `OSAL` dataclass is the container that groups the four components together:

```python
@dataclass
class OSAL:
    pointer:  AbstractPointer
    keyboard: AbstractKeyboard
    screen:   AbstractScreen
    dialogs:  AbstractDialogs
```

At runtime, `get_osal()` in `osal/__init__.py` detects the current OS and
delegates to the matching backend:

```python
def get_osal() -> OSAL:
    os_id = get_platform_info()["os_id"]
    backends = {"darwin": "macos", "linux": "linux", "win32": "windows"}

    if os_id not in backends:
        raise RuntimeError(f"Unsupported OS: {os_id}")

    mod = import_module(f".{backends[os_id]}", __package__)
    return mod.get_osal()
```

Each backend module exposes its own `get_osal()` that instantiates and returns
a fully populated `OSAL`.

---

## Class Hierarchy

```

_AbstractBase (ABC)
└── AbstractOSAL
    ├── AbstractPointer   ← implemented by MacOSPointer, WindowsPointer, LinuxPointer
    ├── AbstractKeyboard  ← implemented by MacOSKeyboard, WindowsKeyboard, LinuxKeyboard
    ├── AbstractScreen    ← implemented by MacOSScreen, WindowsScreen, LinuxScreen
    └── AbstractDialogs   ← implemented by MacOSDialogs, WindowsDialogs, LinuxDialogs

```

`AbstractOSAL` itself has no abstract methods. It exists to carry the
`_AbstractBase` machinery (decorator injection, docstring merging) into every
component through inheritance.

The abstract methods are declared on `AbstractPointer`, `AbstractKeyboard`,
etc. Concrete implementations inherit from these classes and provide the
platform-specific logic.

---

## Automatic Decorator Injection

### The problem it solves

Every low-level method (`move_to()`, `key_down()`, `button_down()`, etc.)
needs the same cross-cutting behavior: a configurable pause after execution,
a failsafe check, and so on.

Requiring every backend author to manually decorate each method would be
error-prone and inconsistent. `_AbstractBase` solves this by injecting
decorators automatically at class definition time, via `__init_subclass__`.

### How it works

When a concrete class (e.g. `MacOSPointer`) is defined, Python calls
`_AbstractBase.__init_subclass__()` on it. At that point the machinery:

1. **Collects all abstract methods** from the full MRO of the new class.
2. **For each method that the class defines concretely**, it:
   - Starts from the default decorator list (`DEFAULT_ABSTRACTMETHOD_DECORATORS`).
   - Removes any decorators listed in `__abstractmethod_remove_decorators__` for that method.
   - Appends any extra decorators listed in `__abstractmethod_decorators__` for that method.
   - Merges the method's docstring with the abstract method's docstring.
   - Wraps the method to preserve the abstract method's signature.
   - Applies all resolved decorators and replaces the method on the class.

The result: the backend author writes a plain method, and it automatically
gets the correct decorators — no manual decoration required.

### Customizing decorators per method

A concrete class (or an abstract intermediary) can fine-tune which decorators
apply to a specific method using two class-level attributes:

```python
class MyPointer(AbstractPointer):

    # Add an extra decorator to a specific method
    __abstractmethod_decorators__ = {
        "move_to": [my_extra_decorator],
    }

    # Remove a default decorator from a specific method
    __abstractmethod_remove_decorators__ = {
        "move_raw": ["pause_decorator"],
    }
```

These dicts are merged across the MRO, so an abstract intermediary can define
defaults that a concrete subclass can still override.

---

## Docstring Merging

When a concrete method overrides an abstract one, `_AbstractBase` automatically
prepends the abstract method's docstring to the concrete implementation's
docstring. This means:

- The abstract docstring documents the **contract** (what the method must do,
  what it returns, what it raises).
- The concrete docstring documents the **implementation** (platform-specific
  details, caveats, edge cases).

Both are visible in `help()` and generated API docs without any duplication of
effort.

Special methods (`__init__`, `setup_postinit`) participate in docstring merging
but receive **no decorators**.

---

## Linux: Composition Pattern

Linux is the only platform with a three-part composition model. Instead of a
single concrete class per component, each Linux OSAL component is built by
combining three Parts at instantiation time:

| Part | Responsibility |
|------|---------------|
| `BasePart` | Core logic that works on any Linux system |
| `DEPart` | Desktop environment specifics (GNOME, KDE, XFCE) |
| `DSPart` | Display server specifics (X11, Wayland) |

The three Parts are merged into a single class via multiple inheritance:

```python
LinuxPointer = type("LinuxPointer", (BasePointerPart, DEPointerPart, DSPointerPart), {})
```

Because each Part covers a distinct set of responsibilities, there is
intentionally **no method overlap** between them. The MRO order therefore has
no practical effect on method resolution in normal operation. It matters only
if you introduce a deliberate override in a new Part — in that case, place it
earlier in the base tuple to give it precedence.

See [platforms/index.md](../platforms/index.md) for the full matrix of
supported desktop environments and display servers.

---

## Adding a New Platform Backend

> **This is a rare operation.** Windows, MacOS, and Linux already cover the
> three major platforms. This section is provided for completeness.

To add a new platform (e.g. `freebsd`):

1. **Create the backend package** at `osal/freebsd/`.

2. **Implement the four components**, each inheriting from the corresponding
   abstract class:

   ```python
   # osal/freebsd/pointer.py
   from pyautogui2.osal.abstract_cls import AbstractPointer

   class FreeBSDPointer(AbstractPointer):
       def move_to(self, x: int, y: int) -> None:
           ...  # platform-specific implementation
       # ... all other abstract methods
   ```

3. **Expose `get_osal()`** from `osal/freebsd/__init__.py`:

   ```python
   from pyautogui2.osal.abstract_cls import OSAL
   from .pointer import FreeBSDPointer
   # ... other imports

   def get_osal() -> OSAL:
       return OSAL(
           pointer=FreeBSDPointer(),
           keyboard=FreeBSDKeyboard(),
           screen=FreeBSDScreen(),
           dialogs=FreeBSDDialogs(),
       )
   ```

4. **Register the OS ID** in `osal/__init__.py`:

   ```python
   backends = {
       "darwin": "macos",
       "linux": "linux",
       "win32": "windows",
       "freebsd": "freebsd",   # add this line
   }
   ```

5. **Add fixtures and tests** in `tests/fixtures/` and `tests/mocks/` following
   the patterns established for the existing backends.

> Do not add decorators manually to your methods. `_AbstractBase` injects them
> automatically. If a specific method needs a different decorator set, use
> `__abstractmethod_decorators__` or `__abstractmethod_remove_decorators__` as
> described above.

---

## Key Files Reference

| File | Role |
|------|------|
| `osal/__init__.py` | Platform detection and backend dispatch |
| `osal/abstract_cls.py` | `_AbstractBase`, `AbstractOSAL`, `AbstractPointer`, etc. |
| `osal/macos/` | MacOS backend |
| `osal/windows/` | Windows backend |
| `osal/linux/` | Linux backend (composition model) |
