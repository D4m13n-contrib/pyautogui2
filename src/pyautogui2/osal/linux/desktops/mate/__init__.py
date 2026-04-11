"""MATE desktop parts for OSAL."""

from .pointer import MatePointerPart


def get_mate_osal_parts() -> dict[str, type]:
    """Return MATE desktop-specific OSAL parts for Linux integration."""
    return {"pointer": MatePointerPart}
