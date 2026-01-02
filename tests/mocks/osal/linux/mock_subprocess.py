"""Mock for subprocess module with predefined command responses.

Provides a configurable mock that returns realistic outputs for common
Linux commands used by OSAL (gsettings, xrandr, setxkbmap, etc.).
"""

from unittest.mock import Mock


class MockSubprocess:
    r"""Reusable mock for subprocess module.

    Features:
        - Predefined responses for common commands
        - Configurable return values
        - Call history tracking
        - Failure simulation

    Example:
        >>> mock_subprocess = MockSubprocess()
        >>> mock_subprocess.set_gsettings_response("left-handed", "true")
        >>> output = mock_subprocess.check_output(["gsettings", "get", ...])
        >>> assert output == "true\n"
    """

    def __init__(self):
        # Command response registry
        self._responses: dict[str, str | Exception] = {}

        # Default responses for common commands
        self._setup_default_responses()

        # Mock objects for subprocess functions
        self.check_output = Mock(side_effect=self._mock_check_output)
        self.run = Mock(side_effect=self._mock_run)
        self.Popen = Mock(side_effect=self._mock_popen)

        # Track all calls
        self.call_history: list[list[str]] = []

    def _setup_default_responses(self):
        """Setup default responses for common Linux commands."""
        # ==================== GNOME gsettings ====================
        # Mouse settings
        self._responses["gsettings|org.gnome.desktop.peripherals.mouse|left-handed"] = "false\n"

        # Touchpad settings
        self._responses["gsettings|org.gnome.desktop.peripherals.touchpad|left-handed"] = "false\n"

        # Input sources (keyboard layout)
        self._responses["gsettings|org.gnome.desktop.input-sources|sources"] = "[('xkb', 'us')]\n"
        self._responses["gsettings|org.gnome.desktop.input-sources|current"] = "0\n"

        # ==================== X11 Commands ====================
        # setxkbmap (keyboard layout)
        self._responses["setxkbmap|-query"] = """rules:      evdev
model:      pc105
layout:     us
"""

        # xrandr (screen outputs)
        self._responses["xrandr|--current"] = """Screen 0: minimum 320 x 200, current 1920 x 1080, maximum 16384 x 16384
HDMI-1 connected primary 1920x1080+0+0 (normal left inverted right x axis y axis) 527mm x 296mm
   1920x1080     60.00*+  50.00    59.94
"""

        # ==================== Wayland Commands ====================
        # localectl (keyboard layout - systemd)
        self._responses["localectl|status"] = """   System Locale: LANG=en_US.UTF-8
       VC Keymap: us
      X11 Layout: us
"""

        # swaymsg (Sway compositor)
        self._responses["swaymsg|-t|get_inputs"] = """[
  {
    "identifier": "keyboard",
    "xkb_active_layout_name": "English (US)"
  }
]
"""

    def _build_key(self, cmd: list[str]) -> str:
        """Build a key for command lookup.

        Examples:
            ["gsettings", "get", "org.gnome...", "left-handed"]
            -> "gsettings|org.gnome...|left-handed"

            ["setxkbmap", "-query"]
            -> "setxkbmap|-query"
        """
        if not cmd:
            return ""

        # Special handling for gsettings
        if cmd[0] == "gsettings" and len(cmd) >= 4:
            # ["gsettings", "get", "schema", "key"] -> "gsettings|schema|key"
            return f"gsettings|{cmd[2]}|{cmd[3]}"

        # For other commands, join command name + relevant args
        return "|".join(cmd[:3])  # Keep first 3 parts

    def _mock_check_output(self, cmd: list[str], **kwargs) -> str:
        """Mock subprocess.check_output()."""
        self.call_history.append(cmd)

        key = self._build_key(cmd)
        response = self._responses.get(key)

        if response is None:
            # Fallback: return empty or raise
            return ""

        if isinstance(response, Exception):
            raise response

        # Handle text=True kwarg
        if kwargs.get("text", False) or kwargs.get("universal_newlines", False):
            return response

        # Return bytes by default
        return response.encode("utf-8")

    def _mock_run(self, cmd: list[str], **kwargs):
        """Mock subprocess.run()."""
        self.call_history.append(cmd)

        key = self._build_key(cmd)
        response = self._responses.get(key, "")

        if isinstance(response, Exception):
            raise response

        # Return CompletedProcess-like object
        result = Mock()
        result.returncode = 0
        result.stdout = response if kwargs.get("capture_output") else None
        result.stderr = None
        return result

    def _mock_popen(self, cmd: list[str], **kwargs):
        """Mock subprocess.Popen()."""
        self.call_history.append(cmd)

        key = self._build_key(cmd)
        response = self._responses.get(key, "")

        # Return Popen-like object
        process = Mock()
        process.communicate = Mock(return_value=(response.encode("utf-8"), b""))
        process.returncode = 0
        process.stdout = Mock()
        process.stdout.read = Mock(return_value=response.encode("utf-8"))
        return process

    # ========================================================================
    # Configuration Methods (for tests to customize responses)
    # ========================================================================

    def set_response(self, cmd: str | list[str], output: str | Exception):
        r"""Set custom response for a command.

        Args:
            cmd: Command as list or key string (e.g., "gsettings|schema|key")
            output: String output or Exception to raise

        Example:
            >>> mock.set_response(["gsettings", "get", "schema", "key"], "custom\n")
            >>> mock.set_response("xrandr|--current", FileNotFoundError())
        """
        key = self._build_key(cmd) if isinstance(cmd, list) else cmd
        self._responses[key] = output

    def set_gsettings_response(self, key: str, value: str, schema: str = "org.gnome.desktop.peripherals.mouse"):
        """Convenience method for gsettings responses.

        Args:
            key: GSettings key (e.g., "left-handed")
            value: Value to return (e.g., "true")
            schema: GSettings schema (default: mouse settings)

        Example:
            >>> mock.set_gsettings_response("left-handed", "true")
        """
        response_key = f"gsettings|{schema}|{key}"
        self._responses[response_key] = f"{value}\n"

    def set_keyboard_layout(self, layout: str, method: str = "setxkbmap"):
        """Set keyboard layout response.

        Args:
            layout: Layout code (e.g., "us", "fr", "de")
            method: Detection method ("setxkbmap" or "localectl")

        Example:
            >>> mock.set_keyboard_layout("fr")
        """
        if method == "setxkbmap":
            self._responses["setxkbmap|-query"] = f"""rules:      evdev
model:      pc105
layout:     {layout}
"""
        elif method == "localectl":
            self._responses["localectl|status"] = f"""   System Locale: LANG=en_US.UTF-8
       VC Keymap: {layout}
      X11 Layout: {layout}
"""

    def simulate_command_failure(self, cmd: str | list[str], error: Exception = FileNotFoundError("Command not found")):
        """Simulate command failure.

        Args:
            cmd: Command to fail
            error: Exception to raise (default: FileNotFoundError)

        Example:
            >>> mock.simulate_command_failure(["xrandr"], FileNotFoundError())
        """
        self.set_response(cmd, error)

    def reset_mock(self):
        """Reset mock state and restore default responses."""
        self.call_history.clear()
        self.check_output.reset_mock()
        self.run.reset_mock()
        self.Popen.reset_mock()
        self._responses.clear()
        self._setup_default_responses()

    def assert_command_called(self, expected_cmd: list[str]):
        """Assert a specific command was called.

        Args:
            expected_cmd: Expected command as list

        Raises:
            AssertionError: If command was not called
        """
        assert expected_cmd in self.call_history, \
            f"Command {expected_cmd} not found in history: {self.call_history}"

    def get_call_count(self, cmd_prefix: str) -> int:
        """Get number of times commands starting with prefix were called.

        Args:
            cmd_prefix: Command prefix (e.g., "gsettings")

        Returns:
            Number of matching calls

        Example:
            >>> count = mock.get_call_count("gsettings")
        """
        return sum(1 for cmd in self.call_history if cmd and cmd[0] == cmd_prefix)


# ========================================================================
# Fixture-ready instance
# ========================================================================

def create_mock_subprocess() -> MockSubprocess:
    """Factory function to create a fresh MockSubprocess instance.

    Returns:
        MockSubprocess: Configured mock with default responses

    Example:
        >>> @pytest.fixture
        >>> def mock_subprocess():
        >>>     return create_mock_subprocess()
    """
    return MockSubprocess()
