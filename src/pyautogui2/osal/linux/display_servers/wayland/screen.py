"""WaylandScreenPart - Display server part for all Linux screens."""
import importlib
import threading

from pathlib import Path

from PIL import Image

from .....utils.exceptions import PyAutoGUIException
from .....utils.lazy_import import lazy_load_object
from ....abstract_cls import AbstractScreen


class WaylandScreenPart(AbstractScreen):
    """Wayland display server screen implementation."""

    _PORTAL_BUS_NAME = "org.freedesktop.portal.Desktop"
    _PORTAL_OBJECT_PATH = "/org/freedesktop/portal/desktop"
    _PORTAL_INTERFACE = "org.freedesktop.portal.Screenshot"
    _PORTAL_METHOD = "Screenshot"
    _REQUEST_INTERFACE = "org.freedesktop.portal.Request"
    _PORTAL_TIMEOUT_SECONDS = 30

    _Gio = lazy_load_object("Gio", lambda: importlib.import_module("gi.repository").Gio)
    _GLib = lazy_load_object("GLib", lambda: importlib.import_module("gi.repository").GLib)

    def _take_screenshot(self) -> "Image.Image":
        """Capture a screenshot via the XDG Desktop Portal (Wayland).

        Uses the org.freedesktop.portal.Screenshot D-Bus interface to request
        a screenshot from the compositor. Blocks until the response is received
        or the timeout is reached.

        Returns:
            PIL Image object containing the captured screenshot.

        Raises:
            PyAutoGUIException: If the portal request fails, times out, or
                returns an unexpected response.
        """
        result_container: dict[str, object] = {}
        loop = self._GLib.MainLoop()

        def _on_response(_connection: object,
                         _sender: str,
                         _path: str,
                         _iface: str,
                         _signal: str,
                         params: object,
                         _user_data: object) -> None:
            response_code, results = params.unpack()    # type: ignore[attr-defined]
            if response_code == 0:
                uri: str = results.get("uri", "")
                if uri.startswith("file://"):
                    result_container["path"] = uri[len("file://"):]
                else:
                    result_container["error"] = f"Unexpected URI format: {uri!r}"
            else:
                result_container["error"] = (
                    f"Portal screenshot request failed with code {response_code}."
                )
            loop.quit()

        def _run_loop() -> None:
            try:
                bus = self._Gio.bus_get_sync(self._Gio.BusType.SESSION, None)

                raw = bus.call_sync(self._PORTAL_BUS_NAME,
                                    self._PORTAL_OBJECT_PATH,
                                    self._PORTAL_INTERFACE,
                                    self._PORTAL_METHOD,
                                    self._GLib.Variant("(sa{sv})", ("", {
                                        "interactive": self._GLib.Variant("b", False),
                                        "modal":       self._GLib.Variant("b", False),
                                    })),
                                    self._GLib.VariantType("(o)"),
                                    self._Gio.DBusCallFlags.NONE,
                                    -1,
                                    None,
                )

                handle: str = raw[0]

                bus.signal_subscribe(None,
                                     self._REQUEST_INTERFACE,
                                     "Response",
                                     handle,
                                     None,
                                     self._Gio.DBusSignalFlags.NONE,
                                     _on_response,
                                     None,
                )

                self._GLib.timeout_add_seconds(self._PORTAL_TIMEOUT_SECONDS, loop.quit)
                loop.run()

            except Exception as exc:
                result_container["error"] = str(exc)
                loop.quit()

        thread = threading.Thread(target=_run_loop, daemon=True)
        thread.start()
        thread.join(timeout=self._PORTAL_TIMEOUT_SECONDS + 5)

        if "error" in result_container:
            raise PyAutoGUIException(
                f"Wayland portal screenshot failed: {result_container['error']}"
            )

        if "path" not in result_container:
            raise PyAutoGUIException(
                "Wayland portal screenshot timed out or returned no result."
            )

        path = Path(str(result_container["path"]))
        try:
            # Copy screenshot into PIL image object (in memory), then remove screenshot file
            img = Image.open(path).copy()
        finally:
            path.unlink(missing_ok=True)

        return img
