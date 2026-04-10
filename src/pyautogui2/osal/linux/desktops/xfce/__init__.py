"""XFCE desktop parts for OSAL."""

from .pointer import XfcePointerPart


def get_xfce_osal_parts() -> dict[str, type]:
    """Return XFCE desktop-specific OSAL parts for Linux integration."""
    return {"pointer": XfcePointerPart}
