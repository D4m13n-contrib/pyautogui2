"""KeyboardController for PyAutoGUI.

See AbstractKeyboardController for documentation.
"""

import time

from collections.abc import Iterator
from contextlib import contextmanager

from more_itertools import mark_ends

from ..osal.abstract_cls import AbstractKeyboard
from ..utils.exceptions import PyAutoGUIException
from .abstract_cls import AbstractKeyboardController


class KeyboardController(AbstractKeyboardController):
    """Concrete implementation of keyboard controller.

    This implementation adds important keyboard layout mapping logic and
    key validation on top of OSAL delegation. It handles multi-character
    keys normalization and automatic codepoint typing for unmapped characters.
    See AbstractKeyboardController for detailed method documentation.

    Class Attributes:
        KEY_NAMES: Tuple of all valid key names across platforms.
        KEYBOARD_MODIFIERS: Valid modifier combinations for layout mappings.
        KEYBOARD_MAPPINGS: Character mappings for QWERTY/QWERTZ/AZERTY layouts.

    Implementation Notes:
        - Multi-character keys are normalized to lowercase.
        - Unmapped characters are automatically typed via codepoint.
        - Layout detection is delegated to OSAL during setup.
    """

    KEY_NAMES: tuple[str, ...] = (
        "\t", "\n", "\r", " ",
        "!", '"', "#", "$", "%", "&", "'", "(", ")",
        "*", "+", ",", "-", ".", "/",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`",
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "{", "|", "}", "~",
        "accept",
        "add",
        "alt",
        "altgr",
        "altleft",
        "altright",
        "apps",
        "backspace",
        "browserback",
        "browserfavorites",
        "browserforward",
        "browserhome",
        "browserrefresh",
        "browsersearch",
        "browserstop",
        "capslock",
        "clear",
        "convert",
        "ctrl",
        "ctrlleft",
        "ctrlright",
        "decimal",
        "del",
        "delete",
        "divide",
        "down",
        "end",
        "enter",
        "esc",
        "escape",
        "execute",
        "f1", "f10", "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19",
        "f2", "f20", "f21", "f22", "f23", "f24",
        "f3", "f4", "f5", "f6", "f7", "f8", "f9",
        "final",
        "fn",
        "hanguel",
        "hangul",
        "hanja",
        "help",
        "home",
        "insert",
        "junja",
        "kana",
        "kanji",
        "launchapp1",
        "launchapp2",
        "launchmail",
        "launchmediaselect",
        "left",
        "modechange",
        "multiply",
        "nexttrack",
        "nonconvert",
        "num0",
        "num1",
        "num2",
        "num3",
        "num4",
        "num5",
        "num6",
        "num7",
        "num8",
        "num9",
        "numlock",
        "pagedown",
        "pageup",
        "pause",
        "pgdn",
        "pgup",
        "playpause",
        "prevtrack",
        "print",
        "printscreen",
        "prntscrn",
        "prtsc",
        "prtscr",
        "return",
        "right",
        "scrolllock",
        "select",
        "separator",
        "shift",
        "shiftleft",
        "shiftright",
        "sleep",
        "space",
        "stop",
        "subtract",
        "tab",
        "up",
        "volumedown",
        "volumemute",
        "volumeup",
        "win",
        "winleft",
        "winright",
        "yen",
        "command",
        "option",
        "optionleft",
        "optionright",
    )

    KEYBOARD_MODIFIERS: tuple[str, ...] = ("_", "shift", "altgr", "shift_altgr")

    KEYBOARD_MAPPINGS: dict[str, dict[str, str]] = {
        "QWERTY": {
            "_"           : r"""`1234567890-=qwertyuiop[]asdfghjkl;'\zxcvbnm,./""",
            "shift"       : r"""~!@#$%^&*()_+QWERTYUIOP{}ASDFGHJKL:"|ZXCVBNM<>?""",
            "altgr"       : r"""""",
            "shift_altgr" : r"""""",
        },
        "QWERTZ": {
            "_"           : r"""§1234567890'^qwertzuiopü¨asdfghjklöä$yxcvbnm,.-""",      # do not list "<" key (that not exists in QWERTY keyboard)
            "shift"       : r"""°+"*ç%&/()=?`QWERTZUIOPè!ASDFGHJKLéà£YXCVBNM;:_""",      # do not list ">" key (that not exists in QWERTY keyboard)
            "altgr"       : r"""¬|@#¼½¬|¢]}´~@ſ€¶ŧ←↓→œþ[]æßðđŋħˀĸł´{}«»¢„“”µ•·.""",      # do not list "\" key (that not exists in QWERTY keyboard)
            "shift_altgr" : r"""¬¡⅛£$⅜⅝⅞™±°¿˛Ω§E®Ŧ¥↑ıŒÞ˚¯ÆẞÐªŊĦ̛&Ł˝ˇ˘<>©‚‘’º×÷˙""",      # do not list "¦" key (that not exists in QWERTY keyboard)
        },
        "AZERTY": {
            "_"           : r"""²&é"'(-è_çà)=azertyuiop^$qsdfghjklmù*wxcvbn,;:!""",      # do not list "<" key (that not exists in QWERTY keyboard)
            "shift"       : r"""~1234567890°+AZERTYUIOP¨£QSDFGHJKLM%µWXCVBN?./§""",      # do not list ">" key (that not exists in QWERTY keyboard)
            "altgr"       : r"""¬¹~#{[|`\^@]}æ«€¶ŧ←↓→øþ¨¤@ßðđŋħˀĸłµ^`ł»¢„“”´•·.""",      # do not list "|" key (that not exists in QWERTY keyboard)
            "shift_altgr" : r"""¬¡⅛£$⅜⅝⅞™±°¿˛Æ<¢®Ŧ¥↑ıØÞ˚¯ΩẞÐªŊĦ̛&Łºˇ˘Ł>©‚‘’˝×÷˙""",      # do not list "¦" key (that not exists in QWERTY keyboard)
        },
    }

    # Characters that can be "dead keys" (combining diacritics) depending on
    # the active keyboard layout. When a dead key is pressed, the system waits
    # for a follow-up character to produce a combined glyph (e.g. dead_tilde + n
    # = ñ). If no valid combination exists, the dead key character appears alone
    # only after a second keypress (typically space).
    #
    # This is problematic for automated input: if we send a dead key character
    # via normal key simulation, it may silently wait for the next character
    # instead of being typed immediately. To avoid this, we bypass the keyboard
    # layout entirely and send these characters via Unicode codepoint injection.
    #
    # The list below covers all characters that are mapped to a dead_* keysym
    # on at least one common keyboard layout. We intentionally include characters
    # that are NOT dead keys on most layouts (e.g. ~ is normal on AZERTY but
    # dead on QWERTZ). Since codepoint injection produces the exact same visible
    # result, there is no downside to always using it for these characters.
    #
    # Dead key name         | Char | Affected layouts (non-exhaustive)
    # ----------------------+------+-------------------------------------------
    # dead_tilde            |  ~   | QWERTZ (de), US-international
    # dead_circumflex       |  ^   | QWERTZ (de), AZERTY (fr)
    # dead_grave            |  `   | US-international, UK-international
    # dead_acute            |  ´   | QWERTZ (de/ch), US-intl, Latin American
    # dead_diaeresis        |  ¨   | QWERTZ (de/ch), US-international
    # dead_cedilla          |  ¸   | Canadian French, Portuguese
    # dead_abovering        |  °   | QWERTZ (de/ch), Scandinavian layouts
    # dead_breve            |  ˘   | Romanian, Turkish
    # dead_doubleacute      |  ˝   | Hungarian
    # dead_ogonek           |  ˛   | Polish, Lithuanian
    # dead_caron            |  ˇ   | Czech, Slovak
    # dead_abovedot         |  ˙   | Lithuanian, Turkish
    # dead_macron           |  ¯   | Māori, Latvian
    # dead_stroke           |  /   | Scandinavian (ø, đ)
    # dead_acute (ASCII)    |  '   | US-international (' = dead_acute)
    # dead_diaeresis (ASCII)|  "   | US-international (" = dead_diaeresis)
    #
    # Note: dead_hook, dead_horn, and dead_belowdot (used in Vietnamese layouts)
    # are omitted because they produce combining diacritics with no standalone
    # visible character. They are relevant only for Vietnamese input and would
    # require dedicated handling beyond this workaround.
    POTENTIALLY_DEAD_KEYS = set(r"""~^`´¨¸°˘˝˛ˇ˙¯/"'""")

    def __init__(self, osal: AbstractKeyboard, *args, **kwargs):
        """Store OSAL backend reference for keyboard operations.

        Args:
            osal: Platform-specific keyboard OSAL implementation.
            *args: List arguments (internal usage).
            **kwargs: Keyword arguments (internal usage).

        Raises:
            PyAutoGUIException: If osal is not an AbstractKeyboard subclass.

        Implementation Notes:
            - Validates OSAL type at instantiation.
        """
        super().__init__(*args, **kwargs)

        if not isinstance(osal, AbstractKeyboard):
            raise PyAutoGUIException(f"Error: '{osal}' should be a subclass of AbstractKeyboard")
        self._osal = osal

    def setup_postinit(self, *args, **kwargs):
        """Configure OSAL with keyboard layout data.

        Passes KEY_NAMES and KEYBOARD_MAPPINGS to the OSAL layer for
        platform-specific keyboard layout detection and key validation.

        Implementation Details:
            - Injects class-level keyboard configuration into OSAL.
            - Enables OSAL to perform layout-specific key mapping.
        """
        super().setup_postinit(*args, **kwargs)

        kwargs.update({
            "key_names": self.KEY_NAMES,
            "all_keymapping": self.KEYBOARD_MAPPINGS,
        })
        self._osal.setup_postinit(*args, **kwargs)

    def teardown_postinit(self, *args, **kwargs):
        self._osal.teardown_postinit(*args, **kwargs)
        super().teardown_postinit(*args, **kwargs)

    def get_layout(self, **_kwargs) -> str:
        return self._osal.get_layout()

    def key_down(self, key: str, **_kwargs) -> None:
        """Implementation Notes:
        - Multi-character keys (e.g., 'shift', 'ctrl')
         are automatically normalized to lowercase before delegation to OSAL.
        - Single-character keys preserve their case.
        """
        if len(key) > 1:
            key = key.lower()

        self._osal.key_down(key)

    def key_up(self, key: str, **_kwargs) -> None:
        """Implementation Notes:
        - Multi-character keys (e.g., 'shift', 'ctrl')
        are automatically normalized to lowercase before delegation to OSAL.
        - Single-character keys preserve their case.
        """
        if len(key) > 1:
            key = key.lower()

        self._osal.key_up(key)

    def press_key(self, key: str, presses: int = 1, interval: float = 0.0, **_kwargs) -> None:
        """Implementation details:
        - If a character is not mapped on the current keyboard layout,
          it will be automatically typed using its Unicode codepoint.
        - Multi-key presses are executed sequentially with interval delay.
        - Internal key_down/key_up calls bypass logging/pause decorators.
        """
        if presses < 1:
            raise PyAutoGUIException(f"presses value must be >= 1 ({presses})")

        if interval < 0.0:
            raise PyAutoGUIException(f"interval must be non-negative ({interval})")

        for _, is_last, _ in mark_ends(range(presses)):
            if len(key) == 1 and key in self.POTENTIALLY_DEAD_KEYS:
                # If key is potentially a dead key type it as codepoint
                self.codepoint(f"U+{ord(key):04x}", _log_screenshot=False, _pause=False)
            elif not self.is_valid_key(key, _log_screenshot=False, _pause=False):
                if len(key) == 1:
                    # If the key is a single character and not directly mapped on keyboard type it as codepoint
                    self.codepoint(f"U+{ord(key):04x}", _log_screenshot=False, _pause=False)
                else:
                    raise PyAutoGUIException(f"unmapped key '{key}' (codepoint fallback not possible without a single character)")
            else:
                self.key_down(key, _log_screenshot=False, _pause=False)
                self.key_up(key, _log_screenshot=False, _pause=False)

            if interval > 0.0 and not is_last:
                time.sleep(interval)

    def write(self, text: str, interval: float = 0.0, **_kwargs) -> None:
        """Implementation details:
        - Each character is processed through press_key() which handles
          unmapped characters automatically via codepoint typing.
        - Interval delay applied after each character.
        - Internal press_key calls bypass logging/pause decorators.
        """
        if interval < 0.0:
            raise PyAutoGUIException(f"interval must be non-negative ({interval})")

        for _, is_last, c in mark_ends(text):
            self.press_key(c, _log_screenshot=False, _pause=False)
            if interval > 0.0 and not is_last:
                time.sleep(interval)

    def is_valid_key(self, key: str, **_kwargs) -> bool:
        """Implementation Notes:
        - Delegates to OSAL's key_is_mapped() which checks
          against the currently detected keyboard layout.
        """
        return self._osal.key_is_mapped(key)

    @contextmanager
    def hold(self, *args, interval: float = 0.0, **_kwargs) -> Iterator:
        """Implementation details:
        - Keys are released in reverse order (LIFO) upon context exit.
        - Internal key_down/key_up calls bypass logging/pause decorators.
        """
        # Convert args to a list for processing
        keys_to_hold: list[str] = []

        if len(args) == 1:
            if isinstance(args[0], list):
                keys_to_hold = args[0]
            elif isinstance(args[0], str):
                keys_to_hold = args[0].split("+")
            else:
                keys_to_hold = list(args[0])
        else:
            keys_to_hold = list(args)

        # Store pressed keys to guarantee to keys are pressed only once
        holded_keys: list[str] = []

        # Press keys
        for _, is_last, key in mark_ends(keys_to_hold):
            if key in holded_keys:
                # If a key is aldready pressed ignore it
                continue

            if not self.is_valid_key(key, _log_screenshot=False, _pause=False):
                raise PyAutoGUIException(f"unmapped key '{key}' to press")

            self.key_down(key, _log_screenshot=False, _pause=False)

            holded_keys.append(key)

            if not is_last:
                time.sleep(interval)

        try:
            yield
        finally:
            # Release holded keys
            for _, is_last, key in mark_ends(reversed(holded_keys)):
                self.key_up(key, _log_screenshot=False, _pause=False)

                if not is_last:
                    time.sleep(interval)

    def hotkey(self, *args, interval: float = 0.0, **_kwargs) -> None:
        """Implementation Notes:
        - This is a convenience wrapper around hold()
          that immediately releases all keys. Equivalent to an empty context
          manager body.
        """
        with self.hold(*args, interval=interval, _log_screenshot=False, _pause=False):
            pass

    def codepoint(self, codepoint: int | str, **_kwargs) -> None:
        """Implementation details:
        - Uses OSAL's platform-specific codepoint input mechanism.
        """
        codepoint_value: int = 0

        if isinstance(codepoint, str):
            # Remove prefix ("U+00E9", "\\xe9", "\\u1234")
            if codepoint.upper().startswith(("U+", "\\X", "\\U")):
                codepoint = codepoint[2:]
            codepoint_value = int(codepoint, 16)
        elif isinstance(codepoint, int):
            codepoint_value = codepoint
        else:
            raise PyAutoGUIException(
                f"Invalid type '{type(codepoint).__name__}' for codepoint '{codepoint}'."
            )

        with self._osal.codepoint_ctx() as ctx:
            ctx.type_codepoint_value(f"{codepoint_value:04x}")
