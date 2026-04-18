"""Common helper functions for Wayland implementation."""
import logging
import subprocess

from pathlib import Path

from .....utils.exceptions import PyAutoGUIException


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
