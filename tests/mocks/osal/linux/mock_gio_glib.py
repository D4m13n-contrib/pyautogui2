"""Mocks for Gio and GLib libraries."""

from unittest.mock import MagicMock


class MockGio(MagicMock):
    """Mock for the Gio module (GDBus portal interface).

    Attributes:
        bus_get_sync: Mock for Gio.bus_get_sync().
        BusType: Mock for Gio.BusType enum (SESSION attribute).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.BusType = MagicMock()
        self.BusType.SESSION = 0

        _mock_bus = MagicMock()
        _mock_bus.signal_subscribe = MagicMock(return_value=1)
        _mock_bus.call_sync = MagicMock(return_value=MagicMock(
            unpack=MagicMock(return_value=("handle_token_value",))
        ))

        self.bus_get_sync = MagicMock(return_value=_mock_bus)


class MockGLib(MagicMock):
    """Mock for the GLib module (main loop and variant types).

    Attributes:
        MainLoop: Mock class for GLib.MainLoop.
        Variant: Mock for GLib.Variant.
        VariantType: Mock for GLib.VariantType.
        timeout_add_seconds: Mock for GLib.timeout_add_seconds.
        PRIORITY_DEFAULT: Mock for GLib.PRIORITY_DEFAULT.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.MainLoop = MagicMock(return_value=MagicMock())
        self.Variant = MagicMock(side_effect=lambda type_str, value: (type_str, value))
        self.VariantType = MagicMock(side_effect=lambda type_str: type_str)
        self.timeout_add_seconds = MagicMock(return_value=0)
        self.PRIORITY_DEFAULT = 0
