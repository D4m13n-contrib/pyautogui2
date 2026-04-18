"""Tests for WaylandScreenPart._take_screenshot()."""
from unittest.mock import MagicMock, patch

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


class TestWaylandScreenPartTakeScreenshot:
    """Tests for WaylandScreenPart._take_screenshot()."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_response_params(code: int, uri: str = "") -> MagicMock:
        """Build a fake GLib.Variant params mock for _on_response."""
        params = MagicMock()
        params.unpack.return_value = (code, {"uri": uri})
        return params

    @staticmethod
    def _make_sync_thread_patch():
        """Patch threading.Thread so that _run_loop runs synchronously on start()."""

        class FakeSyncThread:
            def __init__(self, target=None, daemon=None, **kwargs):
                self._target = target

            def start(self):
                if self._target is not None:
                    self._target()

            def join(self, timeout=None):
                pass

        return patch(
            "pyautogui2.osal.linux.display_servers.wayland.screen.threading.Thread",
            new=FakeSyncThread,
        )

    @staticmethod
    def _subscribe_side_effect(response_params):
        """Return a signal_subscribe side_effect that calls _on_response immediately."""

        def side_effect(*args, **kwargs):
            on_response = args[6]
            on_response(None, None, None, None, None, response_params, None)
            return 1

        return side_effect

    # ------------------------------------------------------------------
    # Success path
    # ------------------------------------------------------------------

    def test_take_screenshot_success(self, linux_ds_wayland_screen):
        """Should return a PIL Image on success."""
        gi_mocks = linux_ds_wayland_screen._mocks["gi"]
        mock_gio = gi_mocks.Gio

        file_path = "/path/to/screenshot.png"
        response_params = self._make_response_params(0, f"file://{file_path}")
        mock_gio.bus_get_sync.return_value.signal_subscribe.side_effect = (
            self._subscribe_side_effect(response_params)
        )

        mock_image = MagicMock()
        mock_image.copy.return_value = mock_image

        with self._make_sync_thread_patch(), \
             patch("pyautogui2.osal.linux.display_servers.wayland.screen.Image.open", return_value=mock_image) as mock_open, \
             patch("pathlib.Path.unlink") as mock_unlink:
            result = linux_ds_wayland_screen._take_screenshot()
            mock_open.assert_called_once()
            mock_image.copy.assert_called_once()
            mock_unlink.assert_called_once_with(missing_ok=True)
            assert result is mock_image

    # ------------------------------------------------------------------
    # Failure paths
    # ------------------------------------------------------------------

    def test_take_screenshot_portal_error_code(self, linux_ds_wayland_screen):
        """Should raise PyAutoGUIException when portal returns non-zero response code."""
        gi_mocks = linux_ds_wayland_screen._mocks["gi"]
        mock_gio = gi_mocks.Gio

        response_params = self._make_response_params(1)
        mock_gio.bus_get_sync.return_value.signal_subscribe.side_effect = (
            self._subscribe_side_effect(response_params)
        )

        with self._make_sync_thread_patch(), \
             pytest.raises(PyAutoGUIException, match="Portal screenshot request failed"):
            linux_ds_wayland_screen._take_screenshot()

    def test_take_screenshot_invalid_uri_scheme(self, linux_ds_wayland_screen):
        """Should raise PyAutoGUIException when URI does not start with file://."""
        gi_mocks = linux_ds_wayland_screen._mocks["gi"]
        mock_gio = gi_mocks.Gio

        response_params = self._make_response_params(0, "https://unexpected.example.com/img.png")
        mock_gio.bus_get_sync.return_value.signal_subscribe.side_effect = (
            self._subscribe_side_effect(response_params)
        )

        with self._make_sync_thread_patch(), \
             pytest.raises(PyAutoGUIException, match="Unexpected URI format"):
            linux_ds_wayland_screen._take_screenshot()

    def test_take_screenshot_timeout(self, linux_ds_wayland_screen):
        """Should raise PyAutoGUIException when no response is received (timeout)."""
        with self._make_sync_thread_patch(), \
             pytest.raises(PyAutoGUIException, match="timed out or returned no result"):
            linux_ds_wayland_screen._take_screenshot()

    def test_take_screenshot_bus_exception(self, linux_ds_wayland_screen):
        """Should raise PyAutoGUIException when DBus bus_get_sync raises."""
        gi_mocks = linux_ds_wayland_screen._mocks["gi"]
        mock_gio = gi_mocks.Gio

        mock_gio.bus_get_sync.side_effect = RuntimeError("DBus unavailable")

        with self._make_sync_thread_patch(), \
             pytest.raises(PyAutoGUIException, match="DBus unavailable"):
            linux_ds_wayland_screen._take_screenshot()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def test_take_screenshot_unlink_called_on_success(self, linux_ds_wayland_screen):
        """Path.unlink() is called in finally block even on success."""
        gi_mocks = linux_ds_wayland_screen._mocks["gi"]
        mock_gio = gi_mocks.Gio

        file_path = "/path/to/screenshot.png"
        response_params = self._make_response_params(0, f"file://{file_path}")

        def subscribe_side_effect(*args, **kwargs):
            on_response = args[6]
            on_response(None, None, None, None, None, response_params, None)
            return 1

        mock_gio.bus_get_sync.return_value.signal_subscribe.side_effect = subscribe_side_effect

        mock_image = MagicMock()
        mock_image.copy.return_value = mock_image

        with self._make_sync_thread_patch(), \
             patch("pyautogui2.osal.linux.display_servers.wayland.screen.Image.open", return_value=mock_image), \
             patch("pyautogui2.osal.linux.display_servers.wayland.screen.Path.unlink") as mock_unlink:
            linux_ds_wayland_screen._take_screenshot()

        mock_unlink.assert_called_once_with(missing_ok=True)

    def test_take_screenshot_unlink_called_on_image_open_failure(self, linux_ds_wayland_screen):
        """Should call Path.unlink even when Image.open raises OSError."""
        gi_mocks = linux_ds_wayland_screen._mocks["gi"]
        mock_gio = gi_mocks.Gio

        file_path = "/path/to/screenshot.png"
        response_params = self._make_response_params(0, f"file://{file_path}")
        mock_gio.bus_get_sync.return_value.signal_subscribe.side_effect = (
            self._subscribe_side_effect(response_params)
        )

        with self._make_sync_thread_patch(), \
             patch("pyautogui2.osal.linux.display_servers.wayland.screen.Image.open", side_effect=OSError("Cannot open file")), \
             patch("pathlib.Path.unlink") as mock_unlink, \
             pytest.raises(OSError, match="Cannot open file"):
            linux_ds_wayland_screen._take_screenshot()

        mock_unlink.assert_called_once_with(missing_ok=True)

