"""Real integration tests for KeyboardController.
No mocks - requires actual graphical environment.
"""
import string
import time

import pytest


@pytest.mark.real
class TestKeyboardRealWrite:

    @pytest.mark.parametrize("text", [
        string.ascii_lowercase,
        string.ascii_uppercase,
        string.digits,
        string.punctuation,
        " \t\n",
        "éèçà€",
        "".join([chr(c) for c in range(0x024D0, 0x024DA)]), # ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙ
        "".join([chr(c) for c in range(0x04E10, 0x04E1A)]), # 丐丑丒专且丕世丗丘丙
        "".join([chr(c) for c in range(0x1F380, 0x1F38A)]), # 🎀🎁🎂🎃🎄🎅🎆🎇🎈🎉
    ], ids=["ascii_lower", "ASCII_UPPER", "digits", "punctuation", "whitespaces",
            "accentued", "unicode_circled_letters", "unicode_cjk", "unicode_emoji"])
    def test_write(self, text, pyautogui_real_capkb):
        """Write some text."""
        pyautogui_real, capkb = pyautogui_real_capkb

        pyautogui_real.keyboard.write(text, interval=0.1)
        time.sleep(0.3)

        result = capkb.read()
        assert result == text
