"""Lightweight Mock of the pytweening module used by TweeningManager tests."""

from pyautogui2.utils.tweening import TweeningManager


class MockPytweening:
    """Simplified replacement for pytweening used in tests."""

    def __init__(self) -> None:
        # Add all tween functions as simple lambdas for testing
        for tween_name in TweeningManager._AVAILABLE_TWEENS:
            if tween_name == 'linear':
                setattr(self, tween_name, lambda n: n)
            else:
                # Simple mock: square function for testing
                setattr(self, tween_name, lambda n: n * n)
