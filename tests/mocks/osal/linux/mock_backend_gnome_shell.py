from unittest.mock import MagicMock


class MockGnomeShellBackend:

    def __init__(self, *_args, **_kwargs):
        self.get_keyboard_layout = MagicMock(return_value="us")
        self.get_pointer_position = MagicMock(return_value=(10, 20))
        self.get_screen_outputs = MagicMock(return_value='[{"x":0,"y":0,"width":1920,"height":1080}]')

    def reset_mock(self):
        self.get_keyboard_layout.reset_mock(side_effect=True)
        self.get_pointer_position.reset_mock(side_effect=True)
        self.get_screen_outputs.reset_mock(side_effect=True)
