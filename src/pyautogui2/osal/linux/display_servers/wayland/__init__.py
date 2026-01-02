"""Wayland display server OSAL loader.

This module detects the active Wayland compositor (backend) such as GNOME Shell,
and dynamically composes the final Wayland*Part classes by combining
Wayland base parts with compositor-specific parts.
"""
from typing import Any

from .compositor import get_wayland_compositor_osal_parts


# ---------------------------------------------------------------------------
# Class factory for Wayland + backend composition
# ---------------------------------------------------------------------------

def _make_wayland_part(base_part: type[Any], backend_part: type[Any]) -> type[Any]:
    """Create a dynamically composed Wayland*Part class
    that includes both Wayland and compositor-specific behavior.

    Args:
        base_part: The base Wayland part class.
        backend_part: The compositor-specific part class.

    Returns:
        The dynamically composed class (e.g. WaylandPointerPartWithGnomeShell).
    """
    name = base_part.__name__.replace("Part", "")
    backend_name = backend_part.__name__.replace("Part", "")
    cls_name = f"{name}{backend_name}Part"

    cls = type(
        cls_name,
        (base_part, backend_part),
        {
            "BACKEND_ID": f"{base_part.__name__}, {backend_part.__name__}",
            "__doc__": f"{base_part.__name__} composed with {backend_part.__name__} "
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
    backend_parts = get_wayland_compositor_osal_parts()

    # Required to be know by locals() calls below
    from .dialogs import WaylandDialogsPart  # noqa: F401
    from .keyboard import WaylandKeyboardPart  # noqa: F401
    from .pointer import WaylandPointerPart  # noqa: F401
    from .screen import WaylandScreenPart  # noqa: F401

    wayland_parts = {
        "pointer": WaylandPointerPart,
        "keyboard": WaylandKeyboardPart,
        "screen": WaylandScreenPart,
        "dialogs": WaylandDialogsPart,
    }

    return {
        name: _make_wayland_part(wayland_parts[name], backend_parts[name])
        for name in wayland_parts
    }
