"""Wayland display server OSAL loader.

This module detects the active Wayland compositor (backend) such as GNOME Shell,
and dynamically composes the final Wayland*Part classes by combining
Wayland base parts with compositor-specific parts.
"""
from typing import Any, Optional

from .compositor import get_wayland_compositor_osal_parts


# ---------------------------------------------------------------------------
# Class factory for Wayland + backend composition
# ---------------------------------------------------------------------------

def _make_wayland_part(base_part: Optional[type[Any]], backend_part: Optional[type[Any]]) -> Optional[type[Any]]:
    """Create a dynamically composed Wayland*Part class
    that includes both Wayland and compositor-specific behavior.

    Args:
        base_part: The base Wayland part class.
        backend_part: The compositor-specific part class.

    Returns:
        The dynamically composed class (e.g. WaylandPointerPartWithGnomeShell).
    """
    cls_parts = []
    name = ""

    if base_part is not None:
        cls_parts.append(base_part)
        name += base_part.__name__.replace("Part", "")
    if backend_part is not None:
        cls_parts.append(backend_part)
        name += backend_part.__name__.replace("Part", "")

    if len(cls_parts) == 0:
        return None

    cls = type(
        f"{name}Part",
        tuple(cls_parts),
        {
            "BACKEND_ID": ", ".join(
                getattr(b, "BACKEND_ID", b.__name__) for b in cls_parts
            ),
            "__doc__": f"Composition: {' with '.join(b.__name__ for b in cls_parts)} "
                       f"to support Wayland compositor backends.",
        },
    )

    return cls


# ---------------------------------------------------------------------------
# Loader entrypoint
# ---------------------------------------------------------------------------

def get_wayland_osal_parts() -> dict[str, type[Any]]:
    """Build and return all OSAL parts for Wayland, including compositor integration.

    Returns:
        A dictionary mapping OSAL component names to their composed classes, e.g.:
        {
            "pointer": WaylandPointerPartWithGnomeShell,
            "keyboard": WaylandKeyboardPartWithGnomeShell,
            ...
        }
    """
    # Required to be know by locals() calls below
    from .keyboard import WaylandKeyboardPart  # noqa: F401
    from .pointer import WaylandPointerPart  # noqa: F401
    from .screen import WaylandScreenPart  # noqa: F401

    wayland_parts = {
        "pointer": WaylandPointerPart,
        "keyboard": WaylandKeyboardPart,
        "screen": WaylandScreenPart,
    }

    backend_parts = get_wayland_compositor_osal_parts()

    composed_parts = {
        name: _make_wayland_part(wayland_parts.get(name), backend_parts.get(name))
        for name in ("pointer", "keyboard", "screen", "dialogs")
    }

    return {k:v for k,v in composed_parts.items() if v is not None}
