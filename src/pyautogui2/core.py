"""Core public API entrypoint for PyAutoGUI.
"""

from . import settings
from .controllers import ControllerManager
from .utils.decorators.failsafe import FailsafeManager
from .utils.decorators.pause import PauseManager


class PyAutoGUI(ControllerManager):
    """Main API class providing unified access to all OSAL components."""

    # ========================================================================
    # Convenience Properties (Safety & Timing)
    # ========================================================================

    @property
    def FAILSAFE(self) -> bool:
        """Enable/disable fail-safe mode.

        When enabled, moving mouse to any screen corner raises FailSafeException
        to emergency-stop the script.

        Examples:
            >>> pag = PyAutoGUI()
            >>> pag.FAILSAFE = True   # Enable (default)
            >>> pag.FAILSAFE = False  # Disable (NOT recommended!)

            >>> # Check current state
            >>> if pag.FAILSAFE:
            ...     print("Fail-safe is active")

        See Also:
            - FailsafeManager for advanced control
        """
        return FailsafeManager().enabled

    @FAILSAFE.setter
    def FAILSAFE(self, value: bool) -> None:
        FailsafeManager().enabled = value

    @property
    def PAUSE(self) -> float:
        """Get/set pause duration between controller actions (seconds).

        This is the time PyAutoGUI waits after each high-level action
        (click, write, hotkey, etc.) to allow applications to respond.

        Examples:
            >>> pag = PyAutoGUI()
            >>> pag.PAUSE = 0.5  # 500ms between actions
            >>> pag.pointer.click()  # Pauses 500ms after
            >>> pag.keyboard.write("hello")  # Pauses 500ms after

            >>> # Disable pauses for speed (careful!)
            >>> pag.PAUSE = 0

            >>> # Check current value
            >>> print(f"Current pause: {pag.PAUSE}s")

        Note:
            This controls controller_duration in PauseManager.
            For fine-grained control of OSAL-level pauses, use:

            >>> from pyautogui2.utils.decorators.pause import PauseManager
            >>> PauseManager().osal_duration = 0.01  # 10ms between key presses

        See Also:
            - PauseManager for advanced control
        """
        return PauseManager().controller_duration

    @PAUSE.setter
    def PAUSE(self, value: float) -> None:
        PauseManager().controller_duration = value

    @property
    def ENSURE_POSITION(self) -> bool:
        """Enable/disable re-asserting and verifying the pointer position.

        When enabled (default), pointer actions re-position the cursor right
        before executing and verify the move succeeded, raising
        PyAutoGUIException otherwise. When disabled, the cursor is not pulled
        back between clicks and a failed move no longer raises.

        Examples:
            >>> pag = PyAutoGUI()
            >>> pag.ENSURE_POSITION = False  # Let the user keep control of the mouse
            >>> pag.ENSURE_POSITION = True   # Restore the default safety behavior

            >>> # Per-call override
            >>> pag.pointer.click(100, 200, ensure_position=False)

        Note:
            Reads and writes the global `settings.ENSURE_POSITION` value, so
            changes take effect immediately.

        See Also:
            - Settings Guide for `ENSURE_POSITION`
        """
        return settings.ENSURE_POSITION

    @ENSURE_POSITION.setter
    def ENSURE_POSITION(self, value: bool) -> None:
        settings.ENSURE_POSITION = value
