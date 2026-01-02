"""Mock for subprocess module used by MacOS OSAL.

Only covers `defaults read` commands used in pointer.py for mouse button detection.
"""

import subprocess as _real_subprocess

from unittest.mock import MagicMock


class MockSubprocess:
    """Reusable mock for subprocess module in MacOS context.

    Only mocks check_output for `defaults read` commands.
    """

    def __init__(self) -> None:
        self._responses: dict[str, str | Exception] = {}
        self._setup_default_responses()

        self.check_output = MagicMock(side_effect=self._mock_check_output)

        # Re-export constants
        self.DEVNULL = _real_subprocess.DEVNULL
        self.CalledProcessError = _real_subprocess.CalledProcessError

    def _setup_default_responses(self, default_value: str = "0") -> None:
        """Setup default responses for MacOS defaults commands."""
        domains = [
            "com.apple.driver.AppleHIDMouse",
            "com.apple.AppleMultitouchMouse",
            "com.apple.mouse",
        ]
        keys = ["swapLeftRightButton", "SwapMouseButtons"]

        for domain in domains:
            for key in keys:
                self._responses[f"{domain}|{key}"] = default_value

    def _build_key(self, cmd: list[str]) -> str:
        """Build lookup key from command.

        ["defaults", "read", "com.apple.mouse", "ButtonMapping"]
        -> "com.apple.mouse|ButtonMapping"
        """
        if len(cmd) >= 4 and cmd[0] == "defaults" and cmd[1] == "read":
            return f"{cmd[2]}|{cmd[3]}"
        return "|".join(cmd)

    def _mock_check_output(self, cmd: list[str], **kwargs) -> bytes | str:
        """Mock subprocess.check_output()."""
        key = self._build_key(cmd)
        response = self._responses.get(key)

        if response is None:
            raise _real_subprocess.CalledProcessError(1, cmd)

        if isinstance(response, Exception):
            raise response

        if kwargs.get("text", False):
            return response

        return response.encode("utf-8")

    # Configuration helpers

    def set_primary_button_left(self):
        self._setup_default_responses(default_value="0")

    def set_primary_button_right(self):
        self._setup_default_responses(default_value="1")

    def set_defaults_response(self, domain: str, key: str, value: str) -> None:
        """Set response for a `defaults read` command.

        Args:
            domain: Defaults domain (e.g., "com.apple.mouse")
            key: Defaults key (e.g., "ButtonMapping")
            value: Value to return
        """
        self._responses[f"{domain}|{key}"] = value

    def simulate_defaults_failure(self, domain: str, key: str) -> None:
        """Simulate `defaults read` failure (key not found).

        Args:
            domain: Defaults domain
            key: Defaults key
        """
        self._responses[f"{domain}|{key}"] = _real_subprocess.CalledProcessError(
            1, ["defaults", "read", domain, key],
        )

    def reset_mock(self, **kwargs):
        """Reset mock state and restore default responses."""
        self.check_output.reset_mock(**kwargs)
        self._responses.clear()
        self._setup_default_responses()
