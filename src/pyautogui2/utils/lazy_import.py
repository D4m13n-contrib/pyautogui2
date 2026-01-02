"""Lazy loading utilities for modules and objects."""

from __future__ import annotations

import contextlib
import importlib

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Generic, TypeVar
from weakref import WeakSet

from .exceptions import PyAutoGUIException


if TYPE_CHECKING:
    from types import ModuleType

T = TypeVar("T")


class LazyImportDescriptor:
    """Descriptor for lazy module imports with per-instance caching.

    The module is imported on first access and cached on the instance.
    This allows easy mocking by setting sys.modules before first access.

    Example:
        class MyClass:
            _uinput = lazy_import("uinput")

            def some_method(self):
                # First access imports and caches on self._lazy_uinput
                device = self._uinput.Device()
    """

    _instance_registry: WeakSet = WeakSet()

    def __init__(self, module_name: str) -> None:
        self.module_name: str = module_name
        # Default attr_name (fallback if __set_name__ isn't called)
        self.attr_name: str = f"_lazy_{module_name.replace('.', '_')}"

    def __set_name__(self, _owner: type, name: str) -> None:
        """Called when descriptor is assigned to a class attribute.

        Sets the cache attribute name based on the descriptor's name.

        Example:
            _uinput = lazy_import("uinput")
            # __set_name__ called with name="_uinput"
            #     attr_name becomes "_lazy_uinput"
        """
        # Remove leading underscores to avoid double-underscore issues
        clean_name = name.lstrip('_')
        self.attr_name = f"_lazy_{clean_name}"

    def __get__(self, instance: Any, _owner: type) -> ModuleType:
        """Get the module, loading it if necessary.

        Args:
            instance: The instance accessing the descriptor (None for class access)
            _owner: The owner class

        Returns:
            The imported module
        """
        if instance is None:
            # Class-level access: always import fresh (no caching)
            return self._load_module()

        # Instance-level access: check cache first
        if not hasattr(instance, self.attr_name):
            # Not cached yet: load and cache on instance
            module = self._load_module()
            setattr(instance, self.attr_name, module)
            LazyImportDescriptor._instance_registry.add(instance)

        result: ModuleType = getattr(instance, self.attr_name)
        return result

    def __set__(self, instance: Any, value: ModuleType) -> None:
        """Allow manual override of the module (useful for mocking).

        Example:
            obj._uinput = MockUInput  # Sets obj._lazy_uinput = MockUInput
        """
        setattr(instance, self.attr_name, value)

    def __delete__(self, instance: Any) -> None:
        """Allow deletion of the cached module (primarily for test cleanup).

        Example:
            del obj._uinput  # Deletes obj._lazy_uinput
        """
        with contextlib.suppress(AttributeError):
            delattr(instance, self.attr_name)

    def _load_module(self) -> ModuleType:
        """Import the module using importlib.

        Returns:
            The imported module

        Raises:
            PyAutoGUIException: If the module cannot be imported
        """
        try:
            return importlib.import_module(self.module_name)
        except ImportError as e:
            raise PyAutoGUIException(
                f"{self.module_name} is required but not installed. "
                f"Install it with: pip install {self.module_name}"
            ) from e


class LazyObjectDescriptor(Generic[T]):
    """Descriptor for lazy object creation with per-instance caching.

    The object is created on first access using the provided factory function.

    Example:
        class MyClass:
            _config = lazy_load_object("config", lambda: load_config())

            def some_method(self):
                # First access calls factory and caches on self._lazy_config
                value = self._config.get("key")
    """

    _instance_registry: WeakSet = WeakSet()

    def __init__(self, name: str, factory: Callable[[], T]) -> None:
        self.name = name
        self.factory = factory
        # Default attr_name
        self.attr_name = f"_lazy_{name}"

    def __set_name__(self, _owner: type, name: str) -> None:
        """Called when descriptor is assigned to a class attribute.

        Sets the cache attribute name based on the descriptor's name.
        """
        clean_name = name.lstrip('_')
        self.attr_name = f"_lazy_{clean_name}"

    def __get__(self, instance: Any, _owner: type) -> T:
        """Get the object, creating it if necessary.

        Args:
            instance: The instance accessing the descriptor (None for class access)
            _owner: The owner class

        Returns:
            The created object
        """
        if instance is None:
            # Class-level access: always create fresh
            return self.factory()

        # Instance-level access: check cache first
        if not hasattr(instance, self.attr_name):
            # Not cached yet: create and cache on instance
            obj = self.factory()
            setattr(instance, self.attr_name, obj)
            LazyObjectDescriptor._instance_registry.add(instance)

        result: T = getattr(instance, self.attr_name)
        return result

    def __set__(self, instance: Any, value: T) -> None:
        """Allow manual override of the object (useful for mocking).

        Example:
            obj._config = MockConfig()  # Sets obj._lazy_config = MockConfig()
        """
        setattr(instance, self.attr_name, value)

    def __delete__(self, instance: Any) -> None:
        """Allow deletion of the cached object (primarily for test cleanup).

        Example:
            del obj._config  # Deletes obj._lazy_config
        """
        with contextlib.suppress(AttributeError):
            delattr(instance, self.attr_name)


def lazy_import(module_name: str) -> LazyImportDescriptor:
    """Create a lazy import descriptor.

    Args:
        module_name: The name of the module to import (e.g., "uinput")

    Returns:
        A descriptor that will lazy-load the module on first access

    Example:
        class LinuxKeyboard:
            _uinput = lazy_import("uinput")

            def press_key(self, key):
                # First access to self._uinput imports the module
                self._uinput.Device().emit_click(key)
    """
    return LazyImportDescriptor(module_name)


def lazy_load_object(name: str, factory: Callable[[], T]) -> LazyObjectDescriptor[T]:
    """Create a lazy object descriptor.

    Args:
        name: A descriptive name for the object (used for cache attribute)
        factory: A callable that creates the object when first accessed

    Returns:
        A descriptor that will lazy-create the object on first access

    Example:
        class MyClass:
            _config = lazy_load_object("config", lambda: Config.load())

            def get_value(self):
                # First access to self._config calls the factory
                return self._config.get("key")
    """
    return LazyObjectDescriptor(name, factory)

