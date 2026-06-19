"""Common helper functions for Wayland implementation."""
import logging
import subprocess

from pathlib import Path

from .....utils.exceptions import PyAutoGUIException


# Installation guidance for PyGObject, which is not a hard pip dependency
# (see pyproject.toml: it lives in the optional 'gnome' extra).
GI_INSTALL_HINT = (
    'install the distro package instead (Debian/Ubuntu: "sudo apt install python3-gi '
    'python3-gi-cairo gir1.2-glib-2.0", venvs need --system-site-packages)'
)


def ensure_device_not_exists(device_name: str) -> None:
    """Raises PyAutoGUIException if a UInput device with the given name already exists.

    Args:
        device_name: The device name to search for in /proc/bus/input/devices.

    Raises:
        PyAutoGUIException: If the device is already registered.
    """
    devices_file = Path("/proc/bus/input/devices")

    if not devices_file.exists():
        logging.warning(
            "Devices file ('%s') does not exist, device uniqueness could not be checked.",
            devices_file,
        )
        return

    result = subprocess.run(["grep", "-qF", device_name, str(devices_file)])
    if result.returncode == 0:
        raise PyAutoGUIException(f"Device '{device_name}' is already registered.")
