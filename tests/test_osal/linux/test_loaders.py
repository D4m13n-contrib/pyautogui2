"""Tests for Linux OSAL dynamic loaders (desktop, display server, compositor).

Architecture:
    The loader system detects the runtime environment and dynamically imports
    the appropriate OSAL parts:

    1. Desktop detection (GNOME, KDE, XFCE)
    2. Display server detection (Wayland, X11)
    3. Wayland compositor detection (GNOME Shell, etc.)

    Each loader returns a dict mapping component names to Part classes.
"""

from unittest.mock import patch

import pytest

from pyautogui2.osal.linux.desktops import get_desktop_osal_parts
from pyautogui2.osal.linux.display_servers import get_display_server_osal_parts


class TestDesktopLoader:
    """Tests for get_desktop_osal_parts() loader."""

    @pytest.mark.parametrize("test_desktop, test_cls_name", [
        ("cinnamon", "CinnamonPointerPart"),
        ("gnome", "GnomePointerPart"),
        ("xfce", "XfcePointerPart"),
    ])
    def test_get_desktop_parts_gnome(self, test_desktop, test_cls_name, isolated_linux):
        """get_desktop_osal_parts() loads parts."""
        with patch("pyautogui2.osal.linux.desktops.get_linux_info", return_value={"linux_desktop": test_desktop}):
            parts = get_desktop_osal_parts()

            assert "pointer" in parts
            assert parts["pointer"].__name__ == test_cls_name

            assert "keyboard" not in parts
            assert "screen" not in parts
            assert "dialogs" not in parts

    @patch("pyautogui2.osal.linux.desktops.get_linux_info", return_value={"linux_desktop": "unknown"})
    def test_get_desktop_parts_unknown_raises_error(self, mock_detect, isolated_linux):
        """get_desktop_osal_parts() raises RuntimeError for unknown desktop."""
        with pytest.raises(RuntimeError, match="Unsupported desktop: unknown"):
            get_desktop_osal_parts()


class TestDisplayServerLoader:
    """Tests for get_display_server_osal_parts() loader."""

    @patch("pyautogui2.osal.linux.display_servers.get_linux_info", return_value={"linux_display_server": "wayland"})
    @patch("pyautogui2.osal.linux.display_servers.wayland.compositor.get_linux_info", return_value={"linux_compositor": "gnome_shell"})
    def test_get_display_server_parts_wayland(self, mock_linux_info, mock_detect, isolated_linux):
        """get_display_server_osal_parts() loads Wayland parts."""
        parts = get_display_server_osal_parts()

        assert "pointer" in parts
        assert "keyboard" in parts
        assert "screen" in parts
        assert "dialogs" not in parts

        # Verify composed names (Wayland + compositor)
        assert "Wayland" in parts["pointer"].__name__
        assert "GnomeShell" in parts["pointer"].__name__

    @patch("pyautogui2.osal.linux.display_servers.get_linux_info", return_value={"linux_display_server": "x11"})
    def test_get_display_server_parts_x11(self, mock_detect, isolated_linux):
        """get_display_server_osal_parts() loads X11 parts."""
        parts = get_display_server_osal_parts()

        assert "pointer" in parts
        assert "keyboard" in parts
        assert "screen" in parts
        assert "dialogs" not in parts

        # Verify class names
        assert parts["pointer"].__name__ == "X11PointerPart"
        assert parts["keyboard"].__name__ == "X11KeyboardPart"
        assert parts["screen"].__name__ == "X11ScreenPart"

    @patch("pyautogui2.osal.linux.display_servers.get_linux_info", return_value={"linux_display_server": "unsupported_DS"})
    def test_get_display_server_parts_unsupported_raises_error(self, mock_detect, isolated_linux):
        """get_display_server_osal_parts() raises RuntimeError for unsupported display server."""
        with pytest.raises(RuntimeError, match="Unsupported display server: unsupported_DS"):
            get_display_server_osal_parts()


class TestWaylandCompositor:
    """Tests for Wayland compositor detection and loading."""

    @patch("pyautogui2.osal.linux.display_servers.wayland.compositor.get_linux_info",
           return_value={"linux_compositor": "gnome_shell"})
    def test_get_wayland_compositor_parts_gnome_shell(self, mock_linux_info, isolated_linux):
        """get_wayland_compositor_osal_parts() loads GNOME Shell parts."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor import (
            get_wayland_compositor_osal_parts,
        )

        parts = get_wayland_compositor_osal_parts()

        assert "pointer" in parts
        assert "keyboard" in parts
        assert "screen" in parts
        assert "dialogs" not in parts

        # Verify class names
        assert parts["pointer"].__name__ == "GnomeShellPointerPart"
        assert parts["keyboard"].__name__ == "GnomeShellKeyboardPart"
        assert parts["screen"].__name__ == "GnomeShellScreenPart"

    @patch("pyautogui2.osal.linux.display_servers.wayland.compositor.get_linux_info",
           return_value={"linux_compositor": "unsupported_compositor"})
    def test_get_wayland_compositor_parts_unsupported_raises_error(self, mock_linux_info, isolated_linux):
        """get_wayland_compositor_osal_parts() raises RuntimeError for unsupported compositor."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor import (
            get_wayland_compositor_osal_parts,
        )

        with pytest.raises(RuntimeError, match="Unsupported Wayland compositor: unsupported_compositor"):
            get_wayland_compositor_osal_parts()


class TestWaylandPartComposition:
    """Tests for Wayland + compositor part composition."""

    @patch("pyautogui2.osal.linux.display_servers.wayland.compositor.get_linux_info",
           return_value={"linux_compositor": "gnome_shell"})
    def test_make_wayland_part_composes_correctly(self, mock_linux_info, isolated_linux):
        """_make_wayland_part() correctly composes Wayland base + compositor parts."""
        from pyautogui2.osal.linux.display_servers.wayland import get_wayland_osal_parts

        parts = get_wayland_osal_parts()

        # Verify all parts are composed
        for name in ("pointer", "keyboard"):
            assert name in parts
            cls = parts[name]

            # Verify it's a composed class
            assert "Wayland" in cls.__name__
            assert "GnomeShell" in cls.__name__

            # Verify BACKEND_ID includes both parts
            assert hasattr(cls, "BACKEND_ID")
            backend_id = cls.BACKEND_ID
            assert "Wayland" in backend_id
            assert "GnomeShell" in backend_id

    @patch("pyautogui2.osal.linux.display_servers.wayland.compositor.get_linux_info",
           return_value={"linux_compositor": "gnome_shell"})
    def test_wayland_parts_have_multiple_inheritance(self, mock_linux_info, isolated_linux):
        """Wayland parts use multiple inheritance from base + compositor."""
        from pyautogui2.osal.linux.display_servers.wayland import get_wayland_osal_parts
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell.pointer import (
            GnomeShellPointerPart,
        )
        from pyautogui2.osal.linux.display_servers.wayland.pointer import WaylandPointerPart

        parts = get_wayland_osal_parts()
        pointer_cls = parts["pointer"]

        # Verify inheritance
        assert issubclass(pointer_cls, WaylandPointerPart)
        assert issubclass(pointer_cls, GnomeShellPointerPart)


class TestIndividualGetters:
    """Tests for individual getter functions (gnome, kde, xfce, x11, gnome_shell)."""

    def test_get_gnome_osal_parts(self, isolated_linux):
        """get_gnome_osal_parts() returns correct GNOME parts."""
        from pyautogui2.osal.linux.desktops.gnome import get_gnome_osal_parts

        parts = get_gnome_osal_parts()

        assert len(parts) == 1
        assert parts["pointer"].__name__ == "GnomePointerPart"

    def test_get_kde_osal_parts(self, isolated_linux):
        """get_kde_osal_parts() returns correct KDE parts."""
        from pyautogui2.osal.linux.desktops.kde import get_kde_osal_parts

        parts = get_kde_osal_parts()

        assert len(parts) == 4
        assert parts["pointer"].__name__ == "KdePointerPart"
        assert parts["keyboard"].__name__ == "KdeKeyboardPart"
        assert parts["screen"].__name__ == "KdeScreenPart"
        assert parts["dialogs"].__name__ == "KdeDialogsPart"

    def test_get_xfce_osal_parts(self, isolated_linux):
        """get_xfce_osal_parts() returns correct XFCE parts."""
        from pyautogui2.osal.linux.desktops.xfce import get_xfce_osal_parts

        parts = get_xfce_osal_parts()

        assert len(parts) == 1
        assert parts["pointer"].__name__ == "XfcePointerPart"

    def test_get_cinnamon_osal_parts(self, isolated_linux):
        """get_cinnamon_osal_parts() returns correct Cinnamon parts."""
        from pyautogui2.osal.linux.desktops.cinnamon import get_cinnamon_osal_parts

        parts = get_cinnamon_osal_parts()

        assert len(parts) == 1
        assert parts["pointer"].__name__ == "CinnamonPointerPart"

    def test_get_x11_osal_parts(self, isolated_linux):
        """get_x11_osal_parts() returns correct X11 parts."""
        from pyautogui2.osal.linux.display_servers.x11 import get_x11_osal_parts

        parts = get_x11_osal_parts()

        assert len(parts) == 3
        assert parts["pointer"].__name__ == "X11PointerPart"
        assert parts["keyboard"].__name__ == "X11KeyboardPart"
        assert parts["screen"].__name__ == "X11ScreenPart"

    def test_get_gnome_shell_osal_parts(self, isolated_linux):
        """get_gnome_shell_osal_parts() returns correct GNOME Shell parts."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell import (
            get_gnome_shell_osal_parts,
        )

        parts = get_gnome_shell_osal_parts()

        assert len(parts) == 3
        assert parts["pointer"].__name__ == "GnomeShellPointerPart"
        assert parts["keyboard"].__name__ == "GnomeShellKeyboardPart"
        assert parts["screen"].__name__ == "GnomeShellScreenPart"
