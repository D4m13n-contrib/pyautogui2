"""Internal decorators."""
from collections.abc import Callable

from .failsafe import failsafe_decorator
from .log_screenshot import log_screenshot
from .pause import pause_decorator


DEFAULTS: list[str | Callable] = ['failsafe_decorator', 'pause_decorator']

__all__ = ['failsafe_decorator', 'pause_decorator', 'log_screenshot']
