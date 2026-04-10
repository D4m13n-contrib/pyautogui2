"""LinuxKeyboardPart - Base part for all Linux keyboards."""
import time

from collections.abc import Generator
from contextlib import contextmanager

from ..abstract_cls import AbstractKeyboard


class LinuxKeyboardPart(AbstractKeyboard):
    """Base Linux keyboard implementation providing Unicode codepoint input support.

    Provides the Linux-standard method for typing arbitrary Unicode characters
    via the Ctrl+Shift+U hex input sequence. This mechanism works across most
    Linux desktop environments and applications that support GTK/Qt input methods.

    Implementation Notes:
        - Uses Ctrl+Shift+U + hex digits + Enter for Unicode input.
        - Works independently of keyboard layout.
        - Actual key press/release delegated to display server Parts.
        - 100ms delay before final Enter to ensure input registration.
    """

    class _CodepointCtx(AbstractKeyboard.AbstractCodepointCtx):
        """Context manager for typing Unicode codepoint hex sequences.

        Handles typing individual hex digits during a Ctrl+Shift+U input session.
        Each character of the hex string is sent as a separate key press/release.
        """
        def type_codepoint_value(self, hexstr: str) -> None:
            """Type hex digits for Unicode codepoint input.

            Implementation Notes:
                - Presses and releases each hex digit character individually.
                - Disables pause between keystrokes (_pause=False).
                - Called within codepoint_ctx context manager.
            """
            for c in hexstr:
                self._keyboard.key_down(c, _pause=False)
                self._keyboard.key_up(c, _pause=False)

    @contextmanager
    def codepoint_ctx(self) -> Generator["LinuxKeyboardPart._CodepointCtx", None, None]:
        """Implementation Notes:
        - Presses Ctrl+Shift+U to start Unicode input mode.
        - Releases keys immediately to prepare for hex digits.
        - Adds 100ms delay before final Enter (input stability).
        - Sends Space to finalize the Unicode character.
        """
        keys = ('ctrl', 'shift', 'u')
        for k in keys:
            self.key_down(k, _pause=False)
        for k in reversed(keys):
            self.key_up(k, _pause=False)

        ctx = self._CodepointCtx(self)

        try:
            yield ctx
        finally:
            time.sleep(.1)  # Sometimes required, else the SPACE key below could be ignored
            self.key_down('space', _pause=False)
            self.key_up('space', _pause=False)
