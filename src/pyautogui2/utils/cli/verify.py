"""PyAutoGUI2 Installation Verification Tool.

This script helps users verify that PyAutoGUI2 is correctly installed
and functional on their system.
"""

import sys

from typing import NoReturn


# Documentation base URL - can be changed when docs are hosted elsewhere
DOCS_BASE_URL = "https://github.com/D4m13n-contrib/pyautogui2/blob/dev/docs"


def _get_doc_url(path: str) -> str:
    """Get full documentation URL for a given path.

    Args:
        path: Relative path to documentation (e.g., "get-started/installation.md")

    Returns:
        Full URL to documentation
    """
    return f"{DOCS_BASE_URL}/{path}"


def _print_troubleshooting_hint(error: Exception) -> None:
    """Print platform-specific troubleshooting hints based on error type."""
    error_str = str(error).lower()

    print("\n💡 Troubleshooting hints:")

    # X11 keyboard layout error
    if "keyboard layout" in error_str or "qwerty" in error_str:
        print("   ⚠️  X11 only supports US QWERTY keyboard layout")
        print("   Fix: setxkbmap us")
        print("   Or: Switch to Wayland (supports all layouts)")
        print(f"   Details: {_get_doc_url('architecture/linux/installation.md#known-limitations')}")

    # Permission errors (Linux)
    elif "permission denied" in error_str and "/dev/uinput" in error_str:
        print("   ⚠️  Missing uinput permissions (Wayland)")
        print("   Fix: sudo usermod -a -G input $USER")
        print("   Then: Log out and log back in")
        print(f"   Details: {_get_doc_url('architecture/linux/installation.md#wayland-installation')}")

    # MacOS accessibility
    elif "accessibility" in error_str or "trusted" in error_str:
        print("   ⚠️  Accessibility permissions not granted (MacOS)")
        print("   Fix: System Preferences → Security & Privacy → Accessibility")
        print(f"   Details: {_get_doc_url('architecture/macos/installation.md#permissions')}")

    # GNOME Shell extension
    elif "gnome" in error_str or "extension" in error_str:
        print("   ⚠️  GNOME Shell extension not installed (Wayland)")
        print("   Fix: pyautogui2-install-wayland-gnomeshell-extension")
        print(f"   Details: {_get_doc_url('architecture/linux/installation.md#gnome-shell-mutter')}")

    # Generic hint
    else:
        print("   • Platform detection: pyautogui2-detect-platform")
        print(f"   • Installation guide: {_get_doc_url('get-started/installation.md')}")
        print(f"   • Troubleshooting: {_get_doc_url('get-started/installation.md#troubleshooting')}")


def verify() -> int:
    """Verify PyAutoGUI2 installation.

    Returns:
        0 if all tests pass, 1 if any test fails
    """
    print("🔍 PyAutoGUI2 Installation Verification")
    print("=" * 50)
    print()

    # Test 1: Import
    print("📦 Testing import...", end=" ")
    try:
        from pyautogui2 import PyAutoGUI
        print("✅")
    except ImportError as e:
        print(f"❌\n   Error: {e}")
        print("\n💡 Solution: pip install pyautogui2")
        return 1

    # Test 2: Platform detection
    print("🖥️  Detecting platform...", end=" ")
    try:
        from pyautogui2.osal.platform_info import main
        main()
    except Exception as e:
        print(f"⚠️  Warning: {e}")

    print()

    # Test 3: Initialize PyAutoGUI
    print("🎮 Initializing PyAutoGUI2...", end=" ")
    try:
        gui = PyAutoGUI()
        print("✅")
    except Exception as e:
        print(f"❌\n   Error: {e}")
        _print_troubleshooting_hint(e)
        return 1

    # Test 4: Screen detection
    print("🖼️  Testing screen detection...", end=" ")
    try:
        width, height = gui.screen.get_size()
        print(f"✅ {width}x{height}")
    except Exception as e:
        print(f"❌\n   Error: {e}")
        _print_troubleshooting_hint(e)
        return 1

    # Test 5: Mouse control
    print("🖱️  Testing mouse control...", end=" ")
    try:
        x, y = gui.pointer.get_position()
        print(f"✅ ({x}, {y})")
    except Exception as e:
        print(f"❌\n   Error: {e}")
        _print_troubleshooting_hint(e)
        return 1

    # Test 6: Screenshot
    print("📸 Testing screenshot...", end=" ")
    try:
        screenshot = gui.screen.screenshot()
        print(f"✅ {screenshot.width}x{screenshot.height}")
    except Exception as e:
        print(f"❌\n   Error: {e}")
        _print_troubleshooting_hint(e)
        return 1

    # Test 7: Keyboard (basic test - just verify it doesn't crash)
    print("⌨️  Testing keyboard...", end=" ")
    try:
        # Don't actually type anything, just verify the module loads
        _ = gui.keyboard
        print("✅")
    except Exception as e:
        # Keyboard might fail on X11 with non-US layout, but that's expected
        if "keyboard layout" in str(e).lower():
            print("⚠️  Limited (X11 non-US layout)")
            print("   Note: Full keyboard support requires US layout on X11")
            print(f"   Details: {_get_doc_url('architecture/linux/installation.md#known-limitations')}")
        else:
            print(f"❌\n   Error: {e}")
            _print_troubleshooting_hint(e)
            return 1

    print()
    print("=" * 50)
    print("🎉 All tests passed! PyAutoGUI2 is working correctly.")
    print()
    print("📚 Next steps:")
    print(f"   • Quick Start: {_get_doc_url('get-started/quickstart.md')}")
    print("   • Examples: https://github.com/D4m13n-contrib/pyautogui2/blob/dev/examples/")
    print(f"   • API Reference: {_get_doc_url('api/')}")

    return 0


def main() -> NoReturn:
    """CLI entry point that exits with proper exit code."""
    sys.exit(verify())


if __name__ == "__main__":
    main()

