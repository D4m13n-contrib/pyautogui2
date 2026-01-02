"""Mocks for testing OSAL Linux."""

from unittest.mock import MagicMock


class MockDBus:
    """Fake D-Bus backend for simulating session and portal access."""

    def __init__(self):
        self.signals = []
        self.services = {"org.freedesktop.portal.Desktop": True}

        self._object = MagicMock()

    def SystemBus(self):
        """Simulate dbus.SystemBus()."""
        return self

    def SessionBus(self):
        """Simulate dbus.SessionBus()."""
        return self

    def get_object(self, service_name, path):
        """Return a fake DBus object reference."""
        if service_name not in self.services:
            raise RuntimeError(f"Unknown service: {service_name}")
        self._object = MagicMock(name=f"DBusObject:{service_name}:{path}")
        return self._object

    def __repr__(self):
        return f"<MockDBus services={list(self.services.keys())}>"

    def reset_mock(self, **kwargs):
        self._object.reset_mock(**kwargs)
