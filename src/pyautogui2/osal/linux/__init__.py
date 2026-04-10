"""Top-level Linux backend loader.

This module dynamically constructs the concrete Linux OSAL implementation
by composing the Linux*Part base classes with platform-specific parts
provided by the detected display server (X11, Wayland, etc.)
and desktop environment (GNOME, KDE, etc.).
"""
from typing import TYPE_CHECKING, Optional, cast

from ...utils.exceptions import PyAutoGUIException
from ..abstract_cls import OSAL

# Desktop and display server getters
from .desktops import get_desktop_osal_parts
from .display_servers import get_display_server_osal_parts

# Local base implementations (exposed for dynamic loading)
from .dialogs import LinuxDialogsPart  # noqa: F401
from .keyboard import LinuxKeyboardPart  # noqa: F401
from .pointer import LinuxPointerPart  # noqa: F401
from .screen import LinuxScreenPart  # noqa: F401

from ..abstract_cls import AbstractDialogs, AbstractKeyboard, AbstractPointer, AbstractScreen
from ...utils.abstract_cls import AbstractOSAL

if TYPE_CHECKING:
    from ...utils.abstract_cls import AbstractOSAL


# ---------------------------------------------------------------------------
# Generic class factory
# ---------------------------------------------------------------------------

def _compose_linux_class(name: str,
                         base_part: type["AbstractOSAL"],
                         desktop_part: Optional[type["AbstractOSAL"]],
                         display_part: Optional[type["AbstractOSAL"]]) -> type["AbstractOSAL"]:
    """Dynamically compose a Linux* class from the given parts.

    This function is used:
    - by `_make_class` in production to assemble the real parts
    - by tests (fixtures) to compose a mock version

    Args:
        name: name of the component (e.g. "keyboard")
        base_part: Linux*Part base class
        desktop_part: desktop environment class (e.g. GnomeKeyboardPart)
        display_part: display server class (e.g. WaylandKeyboardPart)
    """
    cls_name = f"Linux{name.capitalize()}"
    cls_parts = [base_part]
    if desktop_part is not None:
        cls_parts.append(desktop_part)
    if display_part is not None:
        cls_parts.append(display_part)
    cls: type[AbstractOSAL] = type(
        cls_name,
        tuple(cls_parts),
        {
            "BACKEND_ID": ", ".join(
                getattr(b, "BACKEND_ID", b.__name__) for b in cls_parts
            ),
            "__doc__": f"Concrete Linux {name.capitalize()} implementation "
                       f"({', '.join(b.__name__ for b in cls_parts)}).",
        },
    )

    # Verification of unimplemented abstract methods
    unimplemented_methods = getattr(cls, "__abstractmethods__", [])
    if unimplemented_methods:
        raise PyAutoGUIException(
            f"Error: class {cls.__name__} (inherit: {getattr(cls, 'BACKEND_ID', 'Unknown')}) "
            f"needs to implement {', '.join(unimplemented_methods)} functions"
        )

    return cls

def _make_class(name: str) -> type["AbstractOSAL"]:
    """Dynamically build the final Linux* class for the given OSAL component type.

    Args:
        name: The name of the component (e.g. "pointer", "keyboard", "screen", "dialogs").

    Returns:
        A dynamically composed subclass combining:
        - The Linux*Part base implementation
        - The display server-specific part
        - The desktop environment-specific part
    """
    # Retrieve the Linux*Part base class dynamically
    base_part_name = f"Linux{name.capitalize()}Part"
    base_part = globals().get(base_part_name)
    if base_part is None:
        raise RuntimeError(f"Missing base part class: {base_part_name}")

    # Retrieve the Desktop part
    desktop_part = get_desktop_osal_parts().get(name)

    # Retrieve the Display Server part
    display_part = get_display_server_osal_parts().get(name)

    return _compose_linux_class(name, base_part, desktop_part, display_part)


# ---------------------------------------------------------------------------
# OSAL assembly
# ---------------------------------------------------------------------------

def get_osal() -> OSAL:
    """Build and return the fully assembled Linux OSAL object.

    Returns:
        An OSAL instance containing the concrete Linux classes for:
        - pointer
        - keyboard
        - screen
        - dialogs
    """
    # Dynamic class composition with runtime type narrowing
    # Safe casts: we know the types from the component names
    LinuxPointer: type[AbstractPointer] = cast(type["AbstractPointer"], _make_class("pointer"))
    LinuxKeyboard: type[AbstractKeyboard] = cast(type["AbstractKeyboard"], _make_class("keyboard"))
    LinuxScreen: type[AbstractScreen] = cast(type["AbstractScreen"], _make_class("screen"))
    LinuxDialogs: type[AbstractDialogs] = cast(type["AbstractDialogs"], _make_class("dialogs"))

    return OSAL(
        pointer=LinuxPointer(),
        keyboard=LinuxKeyboard(),
        screen=LinuxScreen(),
        dialogs=LinuxDialogs(),
    )
