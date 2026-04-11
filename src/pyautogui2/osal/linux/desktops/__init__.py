"""Desktop detection layer for Linux.
Detects whether the system is running under Gnome, KDE, etc.
and imports the corresponding backend module.
"""
from pyautogui2.osal.platform_info import get_linux_info


def get_desktop_osal_parts() -> dict[str, type]:
    """Get the OSAL desktop environment Part of the current Linux platform."""
    desktop = get_linux_info()["linux_desktop"]

    if desktop == "cinnamon":
        from .cinnamon import get_cinnamon_osal_parts as _get_osal_parts
    elif desktop == "gnome":
        from .gnome import get_gnome_osal_parts as _get_osal_parts
    elif desktop == "xfce":
        from .xfce import get_xfce_osal_parts as _get_osal_parts
    else:
        raise RuntimeError(f"Unsupported desktop: {desktop}")

    return _get_osal_parts()
