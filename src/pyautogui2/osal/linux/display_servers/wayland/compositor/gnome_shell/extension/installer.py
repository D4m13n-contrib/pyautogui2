#!/usr/bin/env python3
"""Installer/updater/remover the Wayland GNOME Shell extension for pyAutoGUI."""

import argparse
import os
import secrets
import subprocess
import sys

from pathlib import Path
from shutil import copytree


EXTENSION_ID = "gnome-wayland@pyautogui.org"

EXTENSION_SRC_PATH = Path(__file__).parent / EXTENSION_ID

GNOME_SHELL_EXTENSIONS_PATH = Path.home() / ".local" / "share" / "gnome-shell" / "extensions"
EXTENSION_INSTALL_PATH = GNOME_SHELL_EXTENSIONS_PATH / EXTENSION_ID
AUTH_TOKEN_PATH = EXTENSION_INSTALL_PATH / "auth_token"


def check_platform():
    """Ensure we are running on Linux + GNOME Shell + Wayland."""
    if not sys.platform.startswith("linux"):
        sys.exit("❌ This installer only works on Linux.")

    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session_type != "wayland":
        sys.exit("❌ This extension is only needed on Wayland sessions.")

    try:
        subprocess.run(["pgrep", "gnome-shell"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        sys.exit("❌ GNOME Shell is not running.")

    print("✅ Platform check passed (Linux + Wayland + GNOME Shell).")


def install_extension():
    """Install the extension from source."""
    if not EXTENSION_SRC_PATH.exists():
        sys.exit(f"❌ Error: {EXTENSION_SRC_PATH} not found.")

    if EXTENSION_INSTALL_PATH.exists():
        print(f"🔄 Removing old extension at {EXTENSION_INSTALL_PATH}")
        for f in EXTENSION_INSTALL_PATH.glob("*"):
            f.unlink()

    # Create the target directory if it doesn't exist
    EXTENSION_INSTALL_PATH.mkdir(parents=True, exist_ok=True)

    print(f"📦 Copying {EXTENSION_SRC_PATH} to {EXTENSION_INSTALL_PATH}")
    copytree(EXTENSION_SRC_PATH, EXTENSION_INSTALL_PATH, dirs_exist_ok=True)

    # Generate a random authentication token
    # Note: enforce token to start with a letter ('t') for DBus compatibility
    auth_token = 't' + secrets.token_hex(16)
    with open(AUTH_TOKEN_PATH, "w", encoding="utf-8") as token_file:
        token_file.write(auth_token)
    os.chmod(AUTH_TOKEN_PATH, 0o600)  # Read/Write only for proprietary
    print("ℹ️ The authentication token is stored securely in the extension directory")

    print(f"🔌 Enabling extension {EXTENSION_ID}")
    subprocess.run(["gnome-extensions", "enable", EXTENSION_ID], check=False)

    print("✅ Installation complete — you may need to restart GNOME Shell (Alt+F2 → r) or log out/in.")


def remove_extension():
    """Remove the extension if installed."""
    if EXTENSION_INSTALL_PATH.exists():
        print(f"🗑️ Removing extension at {EXTENSION_INSTALL_PATH}")
        subprocess.run(["gnome-extensions", "disable", EXTENSION_ID], check=False)
        for f in EXTENSION_INSTALL_PATH.glob("*"):
            f.unlink()
        EXTENSION_INSTALL_PATH.rmdir()
        print("✅ Extension removed.")
    else:
        print("ℹ️ Extension is not installed.")


def main():
    """Main entry point for CLI."""
    check_platform()

    parser = argparse.ArgumentParser(description="Manage Wayland GNOME Shell pyAutoGUI extension.")
    parser.add_argument("--install",
                        action="store_true",
                        help="Install or update the extension (default).")
    parser.add_argument("--remove",
                        action="store_true",
                        help="Remove the extension.")

    args = parser.parse_args()

    if args.remove:
        remove_extension()
    else:
        # default action = install/update
        install_extension()


if __name__ == "__main__":
    main()
