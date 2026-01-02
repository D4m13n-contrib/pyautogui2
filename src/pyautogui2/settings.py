"""Default settings for PyAutoGUI.

These are initial values only. To modify at runtime, use managers:
- PauseManager (utils.decorators.pause)
- FailsafeManager (utils.decorators.failsafe)
"""

# ============================================================================
# Pause Settings (Defaults)
# ============================================================================

# Pause after controller-level actions (pointer, keyboard)
PAUSE_CONTROLLER_DURATION: float = 0.1  # seconds

# Pause after OSAL-level operations (key_down, key_up, etc.)
PAUSE_OSAL_DURATION: float = 0.0  # seconds (no pause by default)

# Legacy constant (for v1 compatibility in docs)
PAUSE: float = PAUSE_CONTROLLER_DURATION

# Enable debug output for pause timings
PAUSE_DEBUG: bool = False


# ============================================================================
# Failsafe Settings (Defaults)
# ============================================================================

# Enable emergency stop by moving mouse to screen corner
FAILSAFE: bool = True


# ============================================================================
# Other Settings
# ============================================================================

LOG_SCREENSHOTS = False  # If True, save screenshots for clicks and key presses.
LOG_SCREENSHOTS_FOLDER = "log_screenshots_output"

# If not None, PyAutoGUI deletes old screenshots when this limit has been reached:
LOG_SCREENSHOTS_LIMIT = 10

# Interface need some catch up time on darwin (MacOS) systems. Possible values probably differ based on your system performance.
# This value affects mouse move_to, drag_to and key event duration.
# TODO: Find a dynamic way to let the system catch up instead of blocking with a magic number.
DARWIN_CATCH_UP_TIME = 0.01
