"""Real integration tests for GnomeShell extension communication."""
from unittest.mock import MagicMock, patch

import pytest

from tests.fixtures.helpers import is_linux_compositor_gnome_shell


if not is_linux_compositor_gnome_shell():
    pytest.skip("Requires platform with GnomeShell compositor", allow_module_level=True)


class TestGnomeShellExtensionBasics:
    """Basic tests for GnomeShell extension functionality."""

    def test_singleton_behavior(self, gnome_shell_backend_real):
        """Verify that GnomeShellBackend is a singleton."""
        from pyautogui2.osal.linux.display_servers.wayland.compositor.gnome_shell._backend import (
            GnomeShellBackend,
        )

        # Get another instance
        backend2 = GnomeShellBackend()

        # Should be the exact same object
        assert backend2 is gnome_shell_backend_real
        assert id(backend2) == id(gnome_shell_backend_real)

    def test_proxy_is_created_on_first_access(self, gnome_shell_backend_real):
        """Verify that proxy is created on first access."""
        # Access proxy
        proxy = gnome_shell_backend_real.proxy

        # Should be a valid proxy object
        assert proxy is not None
        assert hasattr(proxy, "GetKeyboardLayout")
        assert hasattr(proxy, "GetPosition")
        assert hasattr(proxy, "GetOutputs")
        assert hasattr(proxy, "GetAuthTokenPath")

    def test_proxy_is_cached(self, gnome_shell_backend_real):
        """Verify that proxy is cached and reused."""
        # Access proxy twice
        proxy1 = gnome_shell_backend_real.proxy
        proxy2 = gnome_shell_backend_real.proxy

        # Should be the same object
        assert proxy1 is proxy2
        assert id(proxy1) == id(proxy2)

    def test_proxy_methods_are_callable(self, gnome_shell_backend_real):
        """Verify that proxy methods can be called successfully."""
        proxy = gnome_shell_backend_real.proxy

        # Call each method
        layout = proxy.GetKeyboardLayout()
        position = proxy.GetPosition()
        outputs = proxy.GetOutputs()

        # Basic type checks
        assert isinstance(layout, str)
        assert isinstance(position, tuple)
        assert len(position) == 2
        assert isinstance(outputs, str)

    def test_methods_are_callable(self, gnome_shell_backend_real):
        """Verify that methods call proxy."""
        res = gnome_shell_backend_real.get_screen_outputs()
        assert isinstance(res, str)

        res = gnome_shell_backend_real.get_pointer_position()
        assert isinstance(res, tuple)
        assert len(res) == 2

        res = gnome_shell_backend_real.get_keyboard_layout()
        assert isinstance(res, str)


class TestBusNameRegistration:
    """Tests for D-Bus name registration."""

    def test_bus_name_format(self, gnome_shell_backend_real):
        """Verify bus name follows pyautogui.{token} format."""
        # Trigger proxy creation (which registers bus name)
        _ = gnome_shell_backend_real.proxy

        # Check bus name format via D-Bus
        import pydbus
        bus = pydbus.SessionBus()
        dbus_proxy = bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
        names = dbus_proxy.ListNames()

        # Find our bus name
        pyautogui_names = [name for name in names if name.startswith("pyautogui.")]
        assert len(pyautogui_names) >= 1

        # Verify format
        bus_name = pyautogui_names[0]
        assert bus_name.startswith("pyautogui.")
        token = bus_name.split(".", 1)[1]
        assert len(token) == (1 + 32)  # "t" + UUID
        assert token.isalnum()
        assert token[0] == "t"

    def test_bus_name_cleanup(self, gnome_shell_backend_real):
        """Verify bus name is released on cleanup."""
        # Trigger proxy creation
        _ = gnome_shell_backend_real.proxy

        # Get bus name
        import pydbus
        bus = pydbus.SessionBus()
        dbus_proxy = bus.get("org.freedesktop.DBus", "/org/freedesktop/DBus")
        names_before = dbus_proxy.ListNames()
        pyautogui_names_before = [
            name for name in names_before if name.startswith("pyautogui.")
        ]
        assert len(pyautogui_names_before) >= 1
        bus_name = pyautogui_names_before[0]

        # Cleanup
        gnome_shell_backend_real.cleanup()

        # Bus name should be released
        names_after = dbus_proxy.ListNames()
        assert bus_name not in names_after, \
            f"Bus name {bus_name} still registered after cleanup!"

    def test_cleanup_is_idempotent(self, gnome_shell_backend_real):
        """Verify cleanup can be called multiple times safely."""
        # Trigger proxy creation
        _ = gnome_shell_backend_real.proxy

        # Call cleanup multiple times
        gnome_shell_backend_real.cleanup()
        gnome_shell_backend_real.cleanup()
        gnome_shell_backend_real.cleanup()

        # Should not crash


class TestTokenLoading:
    """Tests for auth token loading."""

    def test_token_is_loaded_successfully(self, gnome_shell_backend_real):
        """Verify token can be loaded and used."""
        # If proxy creation succeeds, token was loaded successfully
        proxy = gnome_shell_backend_real.proxy
        assert proxy is not None

        # Verify we can call methods (which require authentication)
        layout = proxy.GetKeyboardLayout()
        assert isinstance(layout, str)

    def test_load_auth_token_without_token_path_raise(self, gnome_shell_backend_real):
        """Verify _load_auth_token() raises RuntimeError when token_path not found."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetAuthTokenPath = MagicMock(return_value=None)

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with pytest.raises(RuntimeError, match="Failed to load auth token") as exc_info:
            gnome_shell_backend_real._load_auth_token()

        cause = exc_info.value.__cause__
        assert isinstance(cause, RuntimeError)
        assert "Extension not installed" in str(cause)

    def test_load_auth_token_file_not_found_raise(self, gnome_shell_backend_real):
        """Verify _load_auth_token() raises RuntimeError when token file not found."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetAuthTokenPath = MagicMock(return_value="unexist")

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with pytest.raises(RuntimeError, match="Token file not found") as exc_info:
            gnome_shell_backend_real._load_auth_token()

        cause = exc_info.value.__cause__
        assert isinstance(cause, FileNotFoundError)

    def test_load_auth_token_bad_permission_file_raise(self, gnome_shell_backend_real, tmp_path):
        """Verify _load_auth_token() raises RuntimeError when token file has bad permissions."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        fake_file_path = tmp_path / "fake_file"
        fake_file_path.write_text("content", encoding="utf-8")
        fake_file_path.chmod(0o333)
        mock_proxy.GetAuthTokenPath = MagicMock(return_value=str(fake_file_path))

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with pytest.raises(RuntimeError, match="Cannot read token file") as exc_info:
            gnome_shell_backend_real._load_auth_token()

        cause = exc_info.value.__cause__
        assert isinstance(cause, PermissionError)

    def test_load_auth_token_with_empty_token_raise(self, gnome_shell_backend_real, tmp_path):
        """Verify _load_auth_token() raises RuntimeError when token file is empty."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        fake_file_path = tmp_path / "fake_file"
        fake_file_path.write_text("", encoding="utf-8")
        mock_proxy.GetAuthTokenPath = MagicMock(return_value=str(fake_file_path))

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with pytest.raises(RuntimeError, match="Failed to load auth token") as exc_info:
            gnome_shell_backend_real._load_auth_token()

        cause = exc_info.value.__cause__
        assert isinstance(cause, RuntimeError)
        assert "Token file is empty" in str(cause)


class TestStaleRegistration:
    """Tests for stale registration bus."""

    def test_is_stale_registration_cannot_determine(self, gnome_shell_backend_real):
        """Verify _is_stale_registration() catch Exception cannot determine bus state."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetNameOwner = MagicMock(side_effect=Exception("Error"))

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with patch("os.kill", return_value=True) as mock_kill:
            res = gnome_shell_backend_real._is_stale_registration()
            mock_kill.assert_not_called()
            assert res is False

    def test_is_stale_registration_process_exist(self, gnome_shell_backend_real):
        """Verify _is_stale_registration() when process exists (not stale)."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetNameOwner = MagicMock(return_value="ID")
        mock_proxy.GetConnectionUnixProcessID = MagicMock(return_value=1234)

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with patch("os.kill", return_value=True) as mock_kill:
            res = gnome_shell_backend_real._is_stale_registration()
            mock_kill.assert_called_once_with(1234, 0)
            assert res is False

    def test_is_stale_registration_kill_catch_exceptions(self, gnome_shell_backend_real):
        """Verify _is_stale_registration() catch os.kill() Exceptions."""
        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetNameOwner = MagicMock(return_value="ID")
        mock_proxy.GetConnectionUnixProcessID = MagicMock(return_value=1234)

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        for exception in [ProcessLookupError, PermissionError]:
            with patch("os.kill", side_effect=exception("Error")) as mock_kill:
                res = gnome_shell_backend_real._is_stale_registration()
                mock_kill.assert_called_once_with(1234, 0)
                assert res is True


class TestForceReleaseViaDBus:
    """Tests for _force_release_via_dbus()."""

    def test_force_release_via_dbus_get_bus_failed(self, gnome_shell_backend_real):
        """Verify _force_release_via_dbus() if get bus failed should return False."""
        mock_bus = MagicMock()

        mock_bus.get = MagicMock(side_effect=Exception("Error"))
        gnome_shell_backend_real._bus_handle = mock_bus

        # Should not raise
        res = gnome_shell_backend_real._force_release_via_dbus()
        assert res is False

    def test_force_release_via_dbus_release_bus_failed(self, gnome_shell_backend_real):
        """Verify _force_release_via_dbus() if release bus failed should return False."""
        import signal

        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetNameOwner = MagicMock(return_value="ID")
        mock_proxy.GetConnectionUnixProcessID = MagicMock(return_value=1234)

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with patch("os.kill", return_value=True) as mock_kill:
            # Should not raise
            res = gnome_shell_backend_real._force_release_via_dbus()

            mock_kill.assert_called_once_with(1234, signal.SIGTERM)
            assert res is False

    def test_force_release_via_dbus_release_bus_success(self, gnome_shell_backend_real):
        """Verify _force_release_via_dbus() if bus successful released should return True."""
        import signal

        mock_bus = MagicMock()
        mock_proxy = MagicMock()

        mock_proxy.GetNameOwner = MagicMock(side_effect=[
            "ID",
            Exception("Not owned"),
        ])
        mock_proxy.GetConnectionUnixProcessID = MagicMock(return_value=1234)

        mock_bus.get = MagicMock(return_value=mock_proxy)
        gnome_shell_backend_real._bus_handle = mock_bus

        with patch("os.kill", return_value=True) as mock_kill:
            # Should not raise
            res = gnome_shell_backend_real._force_release_via_dbus()

            mock_kill.assert_called_once_with(1234, signal.SIGTERM)
            assert res is True


class TestCreateProxy:
    """Tests for _create_proxy()."""

    def test_create_proxy_already_owned(self, gnome_shell_backend_real):
        """Verify _create_proxy() already owned should not raise."""
        gnome_shell_backend_real._proxy = None
        gnome_shell_backend_real._uuid = "UUID"
        gnome_shell_backend_real._name_owner = None

        mock_bus = MagicMock()
        mock_bus.get = MagicMock(return_value="Created Proxy")
        mock_bus.request_name = MagicMock(side_effect=RuntimeError("already the owner"))

        gnome_shell_backend_real._bus_handle = mock_bus

        res = gnome_shell_backend_real._create_proxy()
        assert res == "Created Proxy"

    def test_create_proxy_request_name_raise(self, gnome_shell_backend_real):
        """Verify _create_proxy() raises RuntimeError if request_name failed."""
        gnome_shell_backend_real._proxy = None
        gnome_shell_backend_real._uuid = "UUID"
        gnome_shell_backend_real._name_owner = None

        mock_bus = MagicMock()
        mock_bus.request_name = MagicMock(side_effect=RuntimeError("Error request_name"))

        gnome_shell_backend_real._bus_handle = mock_bus

        with pytest.raises(RuntimeError, match="Could not connect to Wayland Gnome Shell extension via D-Bus") as exc_info:
            gnome_shell_backend_real._create_proxy()

        cause = exc_info.value.__cause__
        assert isinstance(cause, RuntimeError)
        assert str(cause) == "Request name failed"

        cause2 = cause.__cause__
        assert isinstance(cause2, RuntimeError)
        assert str(cause2) == "Error request_name"

    def test_create_proxy_stale_bus_raise(self, gnome_shell_backend_real):
        """Verify _create_proxy() raises RuntimeError if bus could not be released."""
        gnome_shell_backend_real._proxy = None
        gnome_shell_backend_real._uuid = "UUID"
        gnome_shell_backend_real._name_owner = None

        mock_bus = MagicMock()

        gnome_shell_backend_real._bus_handle = mock_bus

        for err_msg in ["name already exists", "already in use"]:
            mock_bus.request_name = MagicMock(side_effect=Exception(err_msg))

            gnome_shell_backend_real._is_stale_registration = MagicMock(return_value=False)
            gnome_shell_backend_real._force_release_via_dbus = MagicMock(return_value=False)

            with pytest.raises(RuntimeError, match="Could not release stale bus name"):
                gnome_shell_backend_real._create_proxy()

    def test_create_proxy_bus_already_exist_recurse(self, gnome_shell_backend_real):
        """Verify _create_proxy() if bus already in use should not raise."""
        gnome_shell_backend_real._proxy = None
        gnome_shell_backend_real._uuid = "UUID"
        gnome_shell_backend_real._name_owner = None

        mock_bus = MagicMock()

        gnome_shell_backend_real._bus_handle = mock_bus

        original_create_proxy = gnome_shell_backend_real._create_proxy

        def _create_proxy_non_recursive():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return original_create_proxy()
            raise KeyboardInterrupt("Test recursive call")

        gnome_shell_backend_real._create_proxy = MagicMock(side_effect=_create_proxy_non_recursive)

        for err_msg in ["name already exists", "already in use"]:
            mock_bus.request_name = MagicMock(side_effect=Exception(err_msg))

            gnome_shell_backend_real._is_stale_registration = MagicMock(return_value=True)
            gnome_shell_backend_real._force_release_via_dbus = MagicMock(return_value=True)

            call_count = 0

            with pytest.raises(KeyboardInterrupt, match="Test recursive call"):
                gnome_shell_backend_real._create_proxy()


class TestCleanupBehavior:
    """Tests for cleanup and resource management."""

    def test_usage_after_cleanup(self, gnome_shell_backend_real):
        """Verify backend can be used again after cleanup."""
        # Use backend
        layout1 = gnome_shell_backend_real.get_keyboard_layout()
        assert isinstance(layout1, str)

        # Cleanup
        gnome_shell_backend_real.cleanup()

        # Use again (should recreate proxy)
        layout2 = gnome_shell_backend_real.get_keyboard_layout()
        assert isinstance(layout2, str)
        assert layout1 == layout2  # Layout shouldn't change

    def test_cleanup_mechanism_works(self, gnome_shell_backend_real):
        """Verify cleanup mechanism is functional."""
        _ = gnome_shell_backend_real.proxy

        try:
            gnome_shell_backend_real.cleanup()
        except Exception as e:
            pytest.fail(f"Cleanup failed: {e}")

        try:
            _ = gnome_shell_backend_real.proxy
        except Exception as e:
            pytest.fail(f"Proxy recreation after cleanup failed: {e}")

    def test_cleanup_with_invalid_bus_log(self, gnome_shell_backend_real, caplog):
        """Verify cleanup log error during releasing bus."""
        import logging
        gnome_shell_backend_real._bus_handle = ""
        gnome_shell_backend_real._uuid = ""

        # Should not raise
        gnome_shell_backend_real.cleanup()

        errors = [x.message for x in caplog.get_records("call") if x.levelno == logging.ERROR]
        assert len(errors) == 1
        assert "ReleaseName failed" in errors[0]


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_method_call(self, gnome_shell_backend_real):
        """Verify invalid method calls raise appropriate errors."""
        proxy = gnome_shell_backend_real.proxy

        # Try to call a method that doesn't exist
        with pytest.raises(AttributeError):
            _ = proxy.NonExistentMethod()

    def test_repeated_access_is_safe(self, gnome_shell_backend_real):
        """Verify repeated sequential access is safe."""
        for _ in range(10):
            layout = gnome_shell_backend_real.get_keyboard_layout()
            assert isinstance(layout, str)

