"""Real integration tests for KeyboardController.
No mocks - requires actual graphical environment.
"""
import string
import time

import pytest

from tests.fixtures.helpers import is_linux_xim_compatible


@pytest.mark.real
class TestKeyboardRealWrite:
    """Real keyboard write tests."""

    @pytest.mark.parametrize("text", [
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        " \t\n",
    ], ids=["ascii_lower", "ASCII_UPPER", "digits", "whitespaces"])
    def test_write_basic(self, text, pyautogui_real_capkb):
        """Write basic ASCII text."""
        pyautogui_real, capkb = pyautogui_real_capkb

        pyautogui_real.keyboard.write(text, interval=0.1)
        time.sleep(0.3)

        result = capkb.read()
        assert result == text

    @pytest.mark.parametrize("text", [
        string.punctuation,
        "éèçà€",
        "".join([chr(c) for c in range(0x024D0, 0x024DA)]),  # ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙ
        "".join([chr(c) for c in range(0x04E10, 0x04E1A)]),  # 丐丑丒专且丕世丗丘丙
        "".join([chr(c) for c in range(0x1F380, 0x1F38A)]),  # 🎀🎁🎂🎃🎄🎅🎆🎇🎈🎉
    ], ids=["punctuation", "accentued", "unicode_circled_letters", "unicode_cjk", "unicode_emoji"])
    def test_write_codepoint(self, text, pyautogui_real_capkb):
        """Write text requiring codepoint injection - xfail on Linux without IBus/XIM."""
        if not is_linux_xim_compatible():
            pytest.xfail("Codepoint input on TKinter requires an active XIM-compatible input method (e.g. IBus).")

        pyautogui_real, capkb = pyautogui_real_capkb

        pyautogui_real.keyboard.write(text, interval=0.1)
        time.sleep(0.3)

        result = capkb.read()
        assert result == text
