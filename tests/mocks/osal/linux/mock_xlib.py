"""Mocks for testing OSAL Linux."""

from unittest.mock import MagicMock


class MockXlib:
    """Unified mock module for all Xlib submodules."""

    class MockDisplay(MagicMock):
        """Mock for Xlib.Display."""
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._cur_keycode = 0
            self._keycode_cache = {}

            self.sync = MagicMock()
            self.screen = MagicMock()

            self._mock_query_pointer = MagicMock()
            self.screen.return_value.root = MagicMock()
            self.screen.return_value.root.configure_mock(query_pointer=self._mock_query_pointer)
            self.screen.return_value.width_in_pixels = 1920
            self.screen.return_value.height_in_pixels = 1080

            self.mock_set_position(x=100, y=200)

        def keysym_to_keycode(self, keysym):
            if keysym not in self._keycode_cache:
                # deterministic but minimal keycode mapping
                self._cur_keycode += 1
                self._keycode_cache[keysym] = self._cur_keycode

            return self._keycode_cache[keysym]

        def mock_set_position(self, x, y):
            self._mock_query_pointer.return_value.configure_mock(root_x=x, root_y=y)

        def reset_mock(self):
            self._keycode_cache = {}
            self._cur_keycode = 0

            self.sync.reset_mock(side_effect=True)


    class MockX(MagicMock):
        """Mock for Xlib.X."""
        KeyPress = 2
        KeyRelease = 3
        ButtonPress = 4
        ButtonRelease = 5
        MotionNotify = 6


    def __init__(self):
        self.display = MagicMock()
        self.display.Display = self.MockDisplay

        # X constants
        self.X = self.MockX()

        # XK (keysyms)
        self.XK = MagicMock()
        self.XK.string_to_keysym = MagicMock(side_effect=lambda x: x)

        # XTest extension
        self.ext = MagicMock()
        self.ext.xtest = MagicMock()
        self.ext.xtest.fake_input = MagicMock()


    def reset_mock(self):
        self.display.reset_mock()

        self.XK.string_to_keysym.reset_mock(return_value=True, side_effect=True)
        self.XK.string_to_keysym.side_effect = lambda x: x

        self.ext.xtest.fake_input.reset_mock(return_value=True, side_effect=True)
