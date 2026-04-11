"""Cinnamon desktop parts for OSAL."""

from .pointer import CinnamonPointerPart


def get_cinnamon_osal_parts() -> dict[str, type]:
    """Return Cinnamon desktop-specific OSAL parts for Linux integration."""
    return {"pointer": CinnamonPointerPart}
