"""Pytest fixtures for PyAutoGUI tests."""
import os
import sys
import threading
import time
import tkinter as tk

from contextlib import contextmanager, suppress
from typing import Optional

import pytest

from pyautogui2.utils.abstract_cls import AbstractController


@contextmanager
def clean_pyautogui(controllers: Optional[dict[str, AbstractController]] = None):
    """Context manager for clean PyAutoGUI state."""
    from pyautogui2.core import PyAutoGUI
    from pyautogui2.utils.singleton import Singleton

    # Remove any existing singleton instance to force re-creation with our controllers
    Singleton.remove_instance("PyAutoGUI")

    controllers = {} if controllers is None else controllers

    instance = PyAutoGUI(**controllers)

    try:
        yield instance
    finally:
        # Clean up so the next test gets a fresh instance
        Singleton.remove_instance("PyAutoGUI")


@pytest.fixture
def osal_mocked():
    """Provide a valid mocked OSAL for PyAutoGUI instantiation."""
    from pyautogui2.osal import OSAL
    from tests.mocks.osal.generic.mock_dialogs_osal import MockDialogsOSAL
    from tests.mocks.osal.generic.mock_keyboard_osal import MockKeyboardOSAL
    from tests.mocks.osal.generic.mock_pointer_osal import MockPointerOSAL
    from tests.mocks.osal.generic.mock_screen_osal import MockScreenOSAL

    return OSAL(
        pointer=MockPointerOSAL(),
        keyboard=MockKeyboardOSAL(),
        screen=MockScreenOSAL(),
        dialogs=MockDialogsOSAL(),
    )


@pytest.fixture
def pyautogui_mocked(osal_mocked):
    """Provide PyAutoGUI instance with generic mocked OSAL."""
    from pyautogui2.controllers.dialogs import DialogsController
    from pyautogui2.controllers.keyboard import KeyboardController
    from pyautogui2.controllers.pointer import PointerController
    from pyautogui2.controllers.screen import ScreenController

    controllers = {
        "pointer": PointerController(osal=osal_mocked.pointer),
        "keyboard": KeyboardController(osal=osal_mocked.keyboard),
        "screen": ScreenController(osal=osal_mocked.screen),
        "dialogs": DialogsController(osal=osal_mocked.dialogs),
    }

    with clean_pyautogui(controllers) as instance:
        yield instance


@pytest.fixture
def pyautogui_real():
    """Provide a real PyAutoGUI instance with actual OSAL implementations.

    Warning:
        This fixture performs REAL system operations:
        - Mouse movements
        - Keyboard input
        - Screen capture
        - System dialogs

        Tests using this fixture should be marked with @pytest.mark.real
        and can be skipped in CI environments.
    """
    def _has_display():
        """Check if a graphical display is available."""
        if sys.platform == "linux":
            return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        elif sys.platform in ("win32", "cygwin"):
            return True  # Windows always has a display
        elif sys.platform == "darwin":
            return True  # MacOS always has a display
        return False

    if not _has_display():
        pytest.skip(
            "Real PyAutoGUI tests require a graphical environment",
            allow_module_level=True
        )

    with clean_pyautogui() as instance:
        try:
            yield instance
        finally:
            # Cleanup: move mouse to safe position (center of screen)
            # Prevents mouse from staying in failsafe corner between tests
            with suppress(Exception):
                width, height = instance.screen.get_size_max()
                instance.pointer.move_to(width // 2, height // 2, duration=0)
                # If cleanup fails, don't break the test suite


class TkinterWindow:
    """Wrapper around a tkinter Text widget used to capture keyboard input during tests.

    The window is created once per test session (scope=session) and reset between
    each test (scope=function) to avoid the Tcl_AsyncDelete crash that occurs when
    multiple Tcl interpreters are created and destroyed in the same process.
    """

    def __init__(self,
                 root: tk.Tk,
                 textarea: tk.Text,
                 input_event: threading.Event,
                 window_closed_event: threading.Event,
                 result_holder: list):
        self.root = root
        self.textarea = textarea
        self.input_event = input_event
        self.window_closed_event = window_closed_event
        self.result_holder = result_holder

    def read(self, timeout: float = 5.0) -> str | None:
        """Poll the Text widget until it contains text or the timeout expires.

        Fetching is delegated to the tkinter thread via root.after() to remain
        thread-safe. Returns the Text content as a string, or None on timeout.
        """
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            result_holder_local = []
            done = threading.Event()

            def _fetch():
                result_holder_local.append(self.textarea.get("1.0", "end-1c"))  # noqa: B023
                done.set()                                                      # noqa: B023

            self.root.after(0, _fetch)
            done.wait(timeout=1.0)

            if result_holder_local and result_holder_local[0]:
                return result_holder_local[0]

            time.sleep(0.1)

        return None

    def reset(self) -> None:
        """Clear the Text widget and restore focus to it.

        Called by the function-scoped fixture before each test to simulate
        a fresh window without recreating the Tcl interpreter.
        """
        done = threading.Event()

        def _reset():
            self.textarea.delete("1.0", tk.END)
            self.textarea.focus_force()
            done.set()

        self.root.after(0, _reset)
        done.wait(timeout=2.0)

    def show(self) -> None:
        """Make the window visible and give focus to the Text widget.

        Combines deiconify, lift, topmost and focus_force to ensure the OS
        window manager actually grants focus before pyautogui starts typing.
        A short sleep is added to let the WM process the focus change.
        """
        done = threading.Event()

        def _show():
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            self.textarea.focus_force()
            done.set()

        self.root.after(0, _show)
        done.wait(timeout=2.0)
        time.sleep(0.2)

    def hide(self) -> None:
        """Hide the window without destroying it.

        Called after each test so the window does not interfere with other
        applications while tests that do not need it are running.
        """
        done = threading.Event()

        def _hide():
            self.root.withdraw()
            done.set()

        self.root.after(0, _hide)
        done.wait(timeout=2.0)


@pytest.fixture(scope="session")
def tkinter_session():
    """Create a single tkinter window for the entire test session.

    Using scope=session prevents the Tcl_AsyncDelete crash that occurs when
    multiple Tcl interpreters are created and destroyed in the same process.
    The window is destroyed cleanly at the end of the session.
    """
    ready_event = threading.Event()
    stop_event = threading.Event()
    tkinter_alive = threading.Event()
    input_event = threading.Event()
    window_closed_event = threading.Event()
    result_holder = []
    components: dict = {}

    def _run_tkinter():
        root = tk.Tk()
        root.title("PyAutoGUI Test Window")
        root.geometry("400x200")

        textarea = tk.Text(root, height=5, width=40)
        textarea.pack()
        textarea.focus_force()

        components["root"] = root
        components["textarea"] = textarea

        tkinter_alive.set()
        ready_event.set()

        def _check_stop():
            """Periodically check whether the session teardown has requested a stop."""
            if stop_event.is_set():
                root.quit()
            else:
                root.after(100, _check_stop)

        root.after(100, _check_stop)
        root.mainloop()

        tkinter_alive.clear()

        # Unblock any callers still waiting on these events after mainloop exits.
        window_closed_event.set()
        input_event.set()

    tkinter_thread = threading.Thread(target=_run_tkinter, daemon=True)
    tkinter_thread.start()

    ready_event.wait(timeout=5.0)

    window = TkinterWindow(
        root=components["root"],
        textarea=components["textarea"],
        input_event=input_event,
        window_closed_event=window_closed_event,
        result_holder=result_holder,
    )

    yield window

    # Session teardown: stop the tkinter thread cleanly
    stop_event.set()
    tkinter_thread.join(timeout=5.0)


@pytest.fixture
def tkinter_window(tkinter_session):
    """Reset the shared tkinter window before each test and hide it afterwards.

    Resetting instead of recreating gives the illusion of a fresh window while
    keeping the same Tcl interpreter alive, which avoids Tcl_AsyncDelete crashes.
    """
    tkinter_session.reset()
    tkinter_session.show()

    try:
        yield tkinter_session
    finally:
        tkinter_session.hide()


@pytest.fixture
def pyautogui_real_capkb(pyautogui_real, tkinter_window):
    """Combine a real pyautogui instance with the tkinter window fixture to capture keyboard input.

    Clicks the center of the Text widget before yielding so that the OS
    focus is guaranteed regardless of the window manager behaviour.
    """
    x = tkinter_window.textarea.winfo_rootx() + tkinter_window.textarea.winfo_width() // 2
    y = tkinter_window.textarea.winfo_rooty() + tkinter_window.textarea.winfo_height() // 2
    pyautogui_real.pointer.click(x, y)
    time.sleep(0.1)

    yield pyautogui_real, tkinter_window


__all__ = [
    "osal_mocked",
    "pyautogui_mocked",
    "pyautogui_real",
    "tkinter_window",
    "pyautogui_real_capkb",
]
