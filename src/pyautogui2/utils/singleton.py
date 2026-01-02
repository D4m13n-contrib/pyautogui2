"""Singleton metaclass."""
import threading

from typing import Any


class Singleton(type):
    """Thread-safe Singleton metaclass.

    Uses double-checked locking pattern for optimal performance:
    - Fast path: No lock overhead for already-created instances
    - Safe path: Lock protects instance creation from race conditions

    Example:
        class MyClass(metaclass=Singleton):
            pass

        # All calls return the same instance, even across threads
        instance1 = MyClass()
        instance2 = MyClass()
        assert instance1 is instance2
    """

    _instances: dict[str, Any] = {}

    # Create a reentrant lock (RLock)
    # to permit Singleton class to create another Singleton class
    _lock: threading.RLock = threading.RLock()

    def __call__(cls, *args, **kwargs):
        # First check (no lock) - fast path for already created instances
        if cls.__name__ not in cls._instances:
            # Acquire lock only if instance doesn't exist yet
            with cls._lock:
                # Second check (with lock) - prevent race condition
                if cls.__name__ not in cls._instances:      # pragma: no branch
                    cls._instances[cls.__name__] = super().__call__(*args, **kwargs)
        return cls._instances[cls.__name__]

    @staticmethod
    def remove_instance(name: str):
        if name in Singleton._instances:
            del Singleton._instances[name]
