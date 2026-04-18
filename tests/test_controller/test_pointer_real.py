"""Real integration tests for PointerController.
No mocks - requires actual graphical environment.
"""
import time

from contextlib import nullcontext

import pytest

from pyautogui2.utils.exceptions import FailSafeException, PyAutoGUIException
from pyautogui2.utils.types import Point


@pytest.mark.real
class TestMoveToGetPositionIntegration:
    """Integration tests for move_to() + get_position() chain.

    Critical: These tests validate that coordinates are preserved exactly,
    which is required for the failsafe mechanism to work correctly.
    """

    @pytest.mark.flaky(retries=1, delay=1, only_on=[PyAutoGUIException])
    @pytest.mark.parametrize("target_x, target_y", [
        (1, 2),
        (33, 44),
        (555, 666),
    ])
    def test_move_to_integer_coordinates_exact_match(self, target_x, target_y, pyautogui_real):
        """Test move_to() with integers reaches EXACT coordinates.
        No tolerance allowed - failsafe depends on exact position matching.
        """
        pyautogui_real.pointer.move_to(0, 0)
        pyautogui_real.pointer.move_to(target_x, target_y)

        actual = pyautogui_real.pointer.get_position()

        assert actual == Point(target_x, target_y)

    @pytest.mark.flaky(retries=1, delay=1, only_on=[PyAutoGUIException])
    @pytest.mark.parametrize("get_pos_test, expectation", [
        (lambda _w, _h: (0, 0), pytest.raises(FailSafeException)),
        (lambda w, _h: (w - 1, 0), pytest.raises(FailSafeException)),
        (lambda _w, h: (0, h - 1), pytest.raises(FailSafeException)),
        (lambda w, h: (w - 1, h - 1), pytest.raises(FailSafeException)),
        (lambda w, h: (w // 2, h // 2), nullcontext()),
    ], ids=["top-left", "top-right", "bottom-left", "bottom-right", "center"])
    def test_move_to_screen_boundaries(self, get_pos_test, expectation, pyautogui_real):
        """Test move_to() works at screen edges (failsafe corner)."""
        from pyautogui2.utils.decorators.failsafe import FailsafeManager

        width, height = pyautogui_real.screen.get_size_max()
        failsafe_x, failsafe_y = get_pos_test(width, height)

        FailsafeManager().enabled = True    # Force Failsafe to be enabled
        try:
            with expectation:
                pyautogui_real.pointer.move_to(failsafe_x, failsafe_y)

            pos = pyautogui_real.pointer.get_position()
            assert pos.x == failsafe_x and pos.y == failsafe_y, \
                f"Failed to reach failsafe corner ({failsafe_x},{failsafe_y}): got ({pos.x}, {pos.y})"
        finally:
            # Reset Failsafe and move pointer to safe position
            FailsafeManager().enabled = False    # Disable Failsafe to permit move_to below
            pyautogui_real.pointer.move_to(10, 10)     # Move pointer to a safe position

    @pytest.mark.flaky(retries=1, delay=1, only_on=[PyAutoGUIException])
    @pytest.mark.parametrize("float_x, float_y, expected_x, expected_y", [
        (100.3, 200.7, 100, 201),  # Round down .3, up .7
        (150.9, 250.1, 151, 250),  # Round up .9, down .1
        (201.5, 202.5, 202, 202),  # Round up <odd>.5, down <even>.5
    ], ids=["round-down", "round-up", "round-odd-even"])
    def test_move_to_float_coordinates_proper_rounding(self, float_x, float_y, expected_x, expected_y, pyautogui_real):
        """Test move_to() with floats rounds to integers correctly.

        Note: This test documents platform-specific rounding behavior.
        If this fails on your platform, it's important to understand why
        (affects pixel-perfect operations).
        """
        pyautogui_real.pointer.move_to(float_x, float_y)
        actual = pyautogui_real.pointer.get_position()

        assert actual.x == expected_x, \
            f"Float {float_x} rounded to {actual.x} (expected {expected_x})"
        assert actual.y == expected_y, \
            f"Float {float_y} rounded to {actual.y} (expected {expected_y})"

    @pytest.mark.flaky(retries=1, delay=1, only_on=[PyAutoGUIException])
    def test_move_to_successive_calls_independent(self, pyautogui_real):
        """Test multiple move_to() calls don't accumulate errors."""
        positions = [(100, 100), (200, 200), (150, 150), (300, 250)]

        for x, y in positions:
            pyautogui_real.pointer.move_to(x, y)
            actual = pyautogui_real.pointer.get_position()
            assert actual.x == x and actual.y == y, \
                f"Accumulated error at ({x}, {y}): got ({actual.x}, {actual.y})"

    @pytest.mark.flaky(retries=1, delay=1, only_on=[PyAutoGUIException])
    def test_move_to_with_duration_reaches_destination(self, pyautogui_real):
        """Test animated movement eventually reaches exact coordinates."""
        start_x, start_y = 100, 100
        target_x, target_y = 500, 400
        duration = 0.5

        pyautogui_real.pointer.move_to(start_x, start_y, duration=0)  # Instant start

        pyautogui_real.pointer.move_to(target_x, target_y, duration=duration)
        time.sleep(duration + 0.15)  # Wait for animation + settling time

        actual = pyautogui_real.pointer.get_position()

        assert actual.x == target_x, \
            f"Animated move missed target X: {actual.x} vs {target_x}"
        assert actual.y == target_y, \
            f"Animated move missed target Y: {actual.y} vs {target_y}"

    @pytest.mark.flaky(retries=1, delay=1, only_on=[PyAutoGUIException])
    def test_failsafe_corner_detection_requires_exact_position(self, pyautogui_real):
        """Document that failsafe relies on exact (0, 0) detection.

        This test explicitly moves to (0, 0) and verifies the position
        is reported exactly, which is what failsafe checks.
        """
        pyautogui_real.pointer.move_to(0, 0)
        pos = pyautogui_real.pointer.get_position()

        # This MUST be exact for failsafe to work
        assert pos.x == 0 and pos.y == 0, \
            f"Failsafe corner not exact: ({pos.x}, {pos.y}) != (0, 0). " \
            f"Failsafe mechanism may not trigger correctly!"
