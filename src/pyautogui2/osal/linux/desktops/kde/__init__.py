"""KDE desktop parts for OSAL."""

from .pointer import KdePointerPart


def get_kde_osal_parts() -> dict[str, type]:
    """Return KDE desktop-specific OSAL parts for Linux integration."""
    return {"pointer": KdePointerPart}
