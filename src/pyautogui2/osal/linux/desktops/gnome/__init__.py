"""Gnome desktop parts for OSAL."""

from .pointer import GnomePointerPart


def get_gnome_osal_parts() -> dict[str, type]:
    """Return Gnome desktop-specific OSAL parts for Linux integration."""
    return {"pointer": GnomePointerPart}
