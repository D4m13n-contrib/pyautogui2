"""Mock for LaunchServices framework."""

from unittest.mock import MagicMock


class MockLaunchServices:
    """Reusable mock object simulating LaunchServices framework.
    Instances are safe to use as a direct replacement for the LaunchServices module.
    """

    def __init__(self) -> None:
        self._input_source_id = "com.apple.keylayout.US"
        self._input_source_name = "U.S."

        # Constants
        self.kTISPropertyInputSourceID = "TISPropertyInputSourceID"
        self.kTISPropertyLocalizedName = "TISPropertyLocalizedName"

        # Functions
        self.TISCopyCurrentKeyboardLayoutInputSource = MagicMock(return_value=MagicMock())
        self.TISGetInputSourceProperty = MagicMock(
            side_effect=self._get_input_source_property,
        )

    def _get_input_source_property(self, source, prop):
        if prop == self.kTISPropertyInputSourceID:
            return self._input_source_id
        if prop == self.kTISPropertyLocalizedName:
            return self._input_source_name
        return None

    def mock_set_keyboard_layout(self, source_id: str, name: str) -> None:
        """Helper to change keyboard layout for testing."""
        self._input_source_id = source_id
        self._input_source_name = name

    def reset_mock(self, **kwargs):
        self.TISCopyCurrentKeyboardLayoutInputSource.reset_mock(**kwargs)
        self.TISGetInputSourceProperty.reset_mock(**kwargs)
