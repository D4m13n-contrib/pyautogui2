"""Tweening (easing functions)."""
import logging

from collections.abc import Callable
from importlib import import_module
from typing import Optional

from .exceptions import PyAutoGUIException
from .singleton import Singleton


class TweeningManager(metaclass=Singleton):
    """Interpolation manager for smooth pointer operations."""

    _AVAILABLE_TWEENS: dict[str, Optional[Callable[[float], float]]] = {
        "easeInQuad": None,
        "easeOutQuad": None,
        "easeInOutQuad": None,
        "easeInCubic": None,
        "easeOutCubic": None,
        "easeInOutCubic": None,
        "easeInQuart": None,
        "easeOutQuart": None,
        "easeInOutQuart": None,
        "easeInQuint": None,
        "easeOutQuint": None,
        "easeInOutQuint": None,
        "easeInSine": None,
        "easeOutSine": None,
        "easeInOutSine": None,
        "easeInExpo": None,
        "easeOutExpo": None,
        "easeInOutExpo": None,
        "easeInCirc": None,
        "easeOutCirc": None,
        "easeInOutCirc": None,
        "easeInElastic": None,
        "easeOutElastic": None,
        "easeInOutElastic": None,
        "easeInBack": None,
        "easeOutBack": None,
        "easeInOutBack": None,
        "easeInBounce": None,
        "easeOutBounce": None,
        "easeInOutBounce": None,
        "linear": None,
    }

    def __init__(self):
        try:
            mod = import_module("pytweening")
            for tween in self._AVAILABLE_TWEENS:
                self._AVAILABLE_TWEENS[tween] = getattr(mod, tween, None)
        except ModuleNotFoundError:
            logging.warning("Could not import pytweening module => degraded mode (only 'linear' tweening is available)")
            self._AVAILABLE_TWEENS['linear'] = self._internal_linear

    def add_tween(self, name: str, func: Callable, force: bool = False) -> None:
        if not force and name in self._AVAILABLE_TWEENS:
            raise ValueError(f"Tweening '{name}' already set (to override it use force=True)")
        self._AVAILABLE_TWEENS[name] = func

    def __call__(self, tween: str):
        return self.__getattr__(tween)

    def __getattr__(self, key):
        if key not in self._AVAILABLE_TWEENS:
            raise PyAutoGUIException(f"Unknown tweening name '{key}' "
                                     f"(available: {list(self._AVAILABLE_TWEENS.keys())})")

        tween = self._AVAILABLE_TWEENS.get(key)
        if tween is None:
            raise PyAutoGUIException(f"The tweening '{key}' is not available")

        def tween_protected(n, *args, **kwargs):
            if not 0.0 <= n <= 1.0:
                raise PyAutoGUIException("Argument must be between 0.0 and 1.0.")
            return tween(n, *args, **kwargs)
        return tween_protected

    @property
    def tweens(self):
        return list(self._AVAILABLE_TWEENS.keys())

    @staticmethod
    def _internal_linear(n):
        """Returns ``n``, where ``n`` is the float argument between ``0.0`` and ``1.0``. This function is for the default
        linear tween for mouse moving functions.

        This function was copied from PyTweening module, so that it can be called even if PyTweening is not installed.
        """
        # We use this function instead of pytweening.linear for the default tween function just in case pytweening couldn't be imported.
        return n

    @staticmethod
    def get_point_on_line(x1, y1, x2, y2, n):
        """Returns an (x, y) tuple of the point that has progressed a proportion ``n`` along the line defined by the two
        ``x1``, ``y1`` and ``x2``, ``y2`` coordinates.

        This function was copied from pytweening module, so that it can be called even if PyTweening is not installed.
        """
        x = ((x2 - x1) * n) + x1
        y = ((y2 - y1) * n) + y1
        return (x, y)
