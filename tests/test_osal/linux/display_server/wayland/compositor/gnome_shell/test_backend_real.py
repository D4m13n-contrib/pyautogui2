"""Real integration tests for Wayland backend minimal interface.

Tests that any Wayland backend provides the required methods and returns
correct data types, regardless of the compositor implementation.
"""
import pytest

from tests.fixtures.helpers import is_linux_wayland_compositor_gnome_shell


if not is_linux_wayland_compositor_gnome_shell():
    pytest.skip("Requires Wayland with GNOME Shell platform", allow_module_level=True)


class TestWaylandBackendBasics:
    """Basic tests for Wayland backend interface."""

    def test_backend_has_required_methods(self, linux_ds_wayland_backend_real):
        """Verify that backend implements all required methods.

        Args:
            linux_ds_wayland_backend_real: Wayland backend fixture (auto-detected).
        """
        assert hasattr(linux_ds_wayland_backend_real, "get_keyboard_layout")
        assert hasattr(linux_ds_wayland_backend_real, "get_pointer_position")
        assert hasattr(linux_ds_wayland_backend_real, "get_screen_outputs")
        assert callable(linux_ds_wayland_backend_real.get_keyboard_layout)
        assert callable(linux_ds_wayland_backend_real.get_pointer_position)
        assert callable(linux_ds_wayland_backend_real.get_screen_outputs)

    def test_get_keyboard_layout_returns_string(self, linux_ds_wayland_backend_real):
        """Verify get_keyboard_layout returns a string.

        Args:
            linux_ds_wayland_backend_real: Wayland backend fixture (auto-detected).
        """
        layout = linux_ds_wayland_backend_real.get_keyboard_layout()
        assert isinstance(layout, str)
        assert len(layout) > 0  # Should not be empty

    def test_get_pointer_position_returns_tuple(self, linux_ds_wayland_backend_real):
        """Verify get_pointer_position returns a tuple of two integers.

        Args:
            linux_ds_wayland_backend_real: Wayland backend fixture (auto-detected).
        """
        position = linux_ds_wayland_backend_real.get_pointer_position()
        assert isinstance(position, tuple)
        assert len(position) == 2
        assert all(isinstance(coord, int) for coord in position)
        assert all(coord >= 0 for coord in position)

    def test_get_screen_outputs_returns_string(self, linux_ds_wayland_backend_real):
        """Verify get_screen_outputs returns a string.

        Args:
            linux_ds_wayland_backend_real: Wayland backend fixture (auto-detected).
        """
        outputs = linux_ds_wayland_backend_real.get_screen_outputs()
        assert isinstance(outputs, str)
        assert len(outputs) > 0  # Should not be empty

    def test_backend_methods_do_not_crash(self, linux_ds_wayland_backend_real):
        """Verify that all methods can be called without crashing.

        Args:
            linux_ds_wayland_backend_real: Wayland backend fixture (auto-detected).
        """
        # Just call everything, should not raise
        _ = linux_ds_wayland_backend_real.get_keyboard_layout()
        _ = linux_ds_wayland_backend_real.get_pointer_position()
        _ = linux_ds_wayland_backend_real.get_screen_outputs()

    def test_multiple_calls_consistency(self, linux_ds_wayland_backend_real):
        """Verify that multiple calls return consistent types.

        Args:
            linux_ds_wayland_backend_real: Wayland backend fixture (auto-detected).
        """
        # Call each method multiple times
        for _ in range(3):
            layout = linux_ds_wayland_backend_real.get_keyboard_layout()
            assert isinstance(layout, str)

            position = linux_ds_wayland_backend_real.get_pointer_position()
            assert isinstance(position, tuple)
            assert len(position) == 2

            outputs = linux_ds_wayland_backend_real.get_screen_outputs()
            assert isinstance(outputs, str)

