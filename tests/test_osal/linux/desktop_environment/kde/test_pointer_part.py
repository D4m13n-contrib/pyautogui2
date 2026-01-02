"""Tests for KDE Desktop Environment Parts.

Desktop Environment Parts are responsible for detecting the primary mouse button
based on system settings (left-handed mode, accessibility, etc.).

Test strategy:
- Mock system calls (gsettings, kwriteconfig, etc.)
- Verify correct button returned based on system configuration
- Ensure error handling works correctly
"""

from unittest.mock import patch

import pytest


pytest.skip('//TODO waiting implementation...', allow_module_level=True)

class TestKdePointerPart:
    """Tests for KdeDesktopPart."""

    def test_get_primary_button_returns_left_by_default(self, linux_de_kde_pointer):
        """get_primary_button() returns 'left' for KDE when not left-handed."""
        # Mock KDE config reading (kreadconfig5 or similar)
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = b"false\n"

            button = linux_de_kde_pointer.get_primary_button()

            assert button == "left"

    def test_get_primary_button_returns_right_when_left_handed(self, linux_de_kde_pointer):
        """get_primary_button() returns 'right' when KDE left-handed mode is enabled."""
        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = b"true\n"

            button = linux_de_kde_pointer.get_primary_button()

            assert button == "right"

    def test_get_primary_button_handles_missing_config(self, linux_de_kde_pointer):
        """get_primary_button() handles missing KDE configuration gracefully."""
        with patch("subprocess.check_output") as mock_subprocess:
            from subprocess import CalledProcessError
            mock_subprocess.side_effect = CalledProcessError(1, "kreadconfig5")

            # Should fallback to default
            with pytest.raises(Exception, match="Error"):
                linux_de_kde_pointer.get_primary_button()
