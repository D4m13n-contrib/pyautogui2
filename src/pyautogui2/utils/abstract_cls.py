"""Base abstract classes for the PyAutoGUI architecture.

This module defines the foundational abstract classes that establish the
contract between controllers and platform-specific OSAL implementations:

- _AbstractBase: Root class with shared introspection utilities
- AbstractController: Base for high-level controller interfaces
- AbstractOSAL: Base for OS Abstraction Layer implementations

These classes implement the decorator propagation system that allows abstract
methods to automatically inherit decorators (like @pause_decorator or @log_screenshot)
unless explicitly removed by subclasses.
"""
import importlib
import inspect

from abc import ABC
from collections.abc import Callable
from functools import wraps
from typing import Any, Optional

from .decorators import DEFAULTS as DEFAULT_ABSTRACTMETHOD_DECORATORS


def _normalize_decorator_id(decorator_id: str | Callable) -> str:
    """Normalize a decorator identifier to a canonical string form.

    This utility converts decorator references (either string names or callable
    functions) into a consistent string representation for comparison and
    storage in __abstractmethod_decorators__ and __abstractmethod_remove_decorators__.

    Args:
        decorator_id: Either a string name (e.g., 'pause_decorator', 'log_screenshot')
            or a callable decorator function.

    Returns:
        The canonical string identifier. For callables, returns the __name__
        attribute. For strings, returns the input unchanged.

    Raises:
        TypeError: If the input is neither a string nor callable.

    Example:
        >>> _normalize_decorator_id('pause_decorator')
        'pause_decorator'
        >>> _normalize_decorator_id(my_decorator_func)
        'my_decorator_func'

    Note:
        Used internally by __init_subclass__ to reconcile decorator specifications
        across class hierarchies.
    """
    if isinstance(decorator_id, str):
        return decorator_id
    if inspect.isfunction(decorator_id):
        return decorator_id.__name__
    raise TypeError(f"Unsupported decorator type: {type(decorator_id)}")

def _resolve_decorator(name_or_func: str | Callable) -> Callable:
    """Resolve a decorator reference to a callable function.

    This utility allows decorators to be specified in class attributes either
    as string names (auto-imported from the decorators module) or as direct
    callable references.

    Args:
        name_or_func: Either:
            - A string name matching a decorator in pyautogui.utils.decorators
              (e.g., 'pause_decorator', 'failsafe_decorator', 'log_screenshot')
            - A callable decorator function

    Returns:
        The resolved callable decorator function.

    Raises:
        ImportError: If a string name does not correspond to any decorator
            in the decorators module.
        TypeError: If the input is neither a string nor a callable.

    Example:
        >>> pause_func = _resolve_decorator('pause_decorator')
        >>> pause_func = _resolve_decorator(my_custom_decorator)

    Note:
        String resolution uses dynamic import of the decorators package to
        avoid circular dependencies during module initialization.
    """
    if inspect.isfunction(name_or_func):
        return name_or_func

    if isinstance(name_or_func, str):
        # Import the decorators package dynamically
        decorators_pkg = importlib.import_module(".decorators", __package__)

        if not hasattr(decorators_pkg, name_or_func):
            raise ImportError(
                f"Decorator '{name_or_func}' not found in {decorators_pkg.__name__} "
                f"(available: {getattr(decorators_pkg, '__all__', [])})"
            )
        return getattr(decorators_pkg, name_or_func)     # type: ignore[no-any-return]

    raise TypeError(f"Unsupported decorator reference: {type(name_or_func)}")

def _merge_doc(impl_doc: Optional[str], base_doc: Optional[str]) -> Optional[str]:
    r"""Merge implementation and inherited docstrings.

    When a concrete class overrides an abstract method, this function combines
    the implementation-specific documentation with the base contract documentation,
    preserving both for API reference tools.

    Args:
        impl_doc: The docstring of the overriding implementation method, or None.
        base_doc: The docstring of the abstract base method, or None.

    Returns:
        The merged docstring, or None if both inputs are None. If only one
        docstring exists, it is returned as-is. If both exist, they are
        concatenated with a '---' separator, base first.

    Example:
        >>> base = "Contract: Must return int."
        >>> impl = "Returns the cached value."
        >>> _merge_doc(impl, base)
        'Contract: Must return int.\n---\nReturns the cached value.'

    Note:
        The separator '---' is used by documentation tools to distinguish
        between implementation notes and abstract contract specifications.
    """
    if impl_doc and base_doc:
        return base_doc.strip() + "\n---\n" + impl_doc.strip()
    return impl_doc or base_doc

def _make_wrapper(method: Callable, ref_func: Callable) -> Callable:
    """Create a wrapper that preserves the signature of a reference function.

    This utility is used during decorator application to ensure that decorated
    methods retain the original signature of their abstract base method, which
    is important for introspection tools, IDEs, and runtime type checkers.

    Args:
        method: The concrete implementation method to wrap (after decorators
            have been applied).
        ref_func: The reference function whose signature should be preserved
            (typically the abstract base method).

    Returns:
        A wrapper function that calls method() but reports ref_func's signature
        to inspection tools via functools.wraps.

    Example:
        >>> def abstract_method(x: int) -> str: ...
        >>> def impl(x): return str(x * 2)
        >>> wrapped = _make_wrapper(impl, abstract_method)
        >>> import inspect
        >>> inspect.signature(wrapped)  # Shows (x: int) -> str

    Note:
        Used internally by __init_subclass__ after all decorators have been
        applied to a method implementation.
    """
    sig = inspect.signature(ref_func)

    @wraps(method)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return method(*args, **kwargs)

    # Override the signature with the one from the abstract function
    setattr(wrapper, '__signature__', sig)  # noqa: B010

    return wrapper


class _AbstractBase(ABC):   # noqa: B024
    """Root base class for the PyAutoGUI abstract class hierarchy.

    This class implements the decorator propagation mechanism that allows abstract
    methods to automatically inherit decorators (like @pause_decorator or @failsafe_decorator)
    from class-level specifications, while allowing subclasses to selectively
    remove or add decorators on a per-method basis.

    Class Attributes:
        __abstractmethod_decorators__ (dict[str, list[Union[str, Callable]]]):
            Maps method names to additional decorators that should be applied
            to implementations. Decorators are specified as either string names
            (resolved from utils.decorators) or callable functions.

        __abstractmethod_remove_decorators__ (dict[str, list[Union[str, Callable]]]):
            Maps method names to decorators that should NOT be applied to
            implementations, overriding defaults or parent class specifications.

    Example:
        >>> class MyController(_AbstractBase):
        ...     __abstractmethod_decorators__ = {
        ...         "click": ["log_screenshot", "pause_decorator"]
        ...     }
        ...     __abstractmethod_remove_decorators__ = {
        ...         "get_position": ["pause_decorator"]  # Skip pause for getters
        ...     }

    Note:
        This class should not be instantiated directly. It serves as the common
        ancestor for AbstractController and AbstractOSAL.
    """

    # Add extra decorators (per method)
    __abstractmethod_decorators__: dict[str, list[str | Callable]] = {}

    # Remove specific default decorators (per method)
    __abstractmethod_remove_decorators__: dict[str, list[str | Callable]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Automatic decorator propagation hook for subclasses.

        This method is invoked automatically by Python whenever a class inherits
        from _AbstractBase. It performs the following tasks:

        1. Collects all abstract methods from the entire MRO (Method Resolution Order)
        2. For each abstract method that has an implementation in the subclass:
           - Merges the implementation's docstring with the abstract docstring
           - Collects decorators from:
             * DEFAULT_ABSTRACTMETHOD_DECORATORS (global defaults)
             * Parent class __abstractmethod_decorators__ attributes
             * Current class __abstractmethod_decorators__ attribute
           - Removes decorators specified in __abstractmethod_remove_decorators__
           - Applies the final decorator stack in reverse order
           - Wraps the result to preserve the abstract method's signature

        This ensures consistent behavior across all implementations while allowing
        fine-grained control over which decorators are active for specific methods.

        Args:
            **kwargs: Additional subclass creation parameters passed automatically
                by Python's class creation machinery.

        Example:
            >>> # This happens automatically when you define:
            >>> class ConcretePointer(AbstractPointer):
            ...     def click(self, x, y):  # Automatically gets @pause_decorator, etc.
            ...         ...

        Note:
            Decorators are applied in reverse order of specification, so the first
            decorator in the list becomes the outermost wrapper.
        """
        super().__init_subclass__(**kwargs)

        # Collect all abstract methods from the hierarchy
        abstract_methods: set[str] = set()
        for base in cls.__mro__:
            abstract_methods |= getattr(base, "__abstractmethods__", set())

        # Special methods available for doc merging but not any decorators
        special_methods = ("__init__", "setup_postinit")

        # Add special non-abstract methods for doc merging
        for s_m in special_methods:
            abstract_methods.add(s_m)

        decorators: list[str | Callable] = []

        for name in abstract_methods:
            method = cls.__dict__.get(name)
            if method and inspect.isfunction(method):
                decorators = []
                if method.__name__ not in special_methods:
                    # Collect default decorators
                    decorators = list(DEFAULT_ABSTRACTMETHOD_DECORATORS)

                    # Remove unwanted
                    to_remove = cls.__abstractmethod_remove_decorators__.get(name, [])
                    normalized_remove = {_normalize_decorator_id(d) for d in to_remove}
                    decorators = [
                        d for d in decorators
                        if _normalize_decorator_id(d) not in normalized_remove
                    ]

                    # Add extra
                    extra = cls.__abstractmethod_decorators__.get(name, [])
                    decorators.extend(extra)

                # Merge docstring with inheritance
                abstract_func = None
                prev_candidate = None
                for base in cls.__mro__[1:]:
                    if base is _AbstractBase:
                        # Nothing to do: top level class has been reached
                        break

                    candidate = getattr(base, name, None)

                    if prev_candidate is not None and candidate == prev_candidate:
                        # Nothing to do: docstring already merged
                        break
                    prev_candidate = candidate

                    if candidate:
                        method.__doc__ = _merge_doc(method.__doc__, candidate.__doc__)
                        if getattr(candidate, "__isabstractmethod__", False):
                            abstract_func = candidate
                            break
                else:  # pragma: no cover
                    # Theoretically unreachable: all names in `abstract_methods` are either
                    # declared @abstractmethod somewhere in the MRO (guaranteeing at least one
                    # candidate with __isabstractmethod__=True) or are special methods
                    # (__init__, setup_postinit) which are never abstract.
                    pass

                # Wrap to preserve signature
                if abstract_func:
                    method = _make_wrapper(method, abstract_func)

                # Resolve and apply decorators
                for deco in decorators:
                    deco = _resolve_decorator(deco)
                    method = deco(method)

                setattr(cls, name, method)


class AbstractController(_AbstractBase):
    """Base class for high-level controller interfaces.

    Controllers provide the user-facing API for interacting with system resources
    (pointer, keyboard, screen, dialogs). They delegate platform-specific operations
    to OSAL implementations while adding cross-platform logic like:

    - Coordinate normalization
    - Timing and animation (tweening)
    - Failsafe checks
    - Logging and debugging hooks

    Controllers are instantiated and managed by ControllerManager, which handles
    dependency injection and lifecycle coordination.

    Example:
        >>> # Typically instantiated by ControllerManager:
        >>> from pyautogui2 import ControllerManager
        >>> cm = ControllerManager()
        >>> cm.pointer.move_to(100, 200)

    Note:
        Subclasses (PointerController, KeyboardController, etc.) must implement
        all abstract methods defined in their respective abstract_cls.py files.
    """

    def __init__(self, *_args, **_kwargs):
        """Initialize the controller.

        Args:
            *args: Positional arguments (typically unused; reserved for extensions).
            **kwargs: Keyword arguments (typically unused; reserved for extensions).
        """
        super().__init__()

    # Not abstractmethod
    def setup_postinit(self, *_args, **_kwargs):
        """Perform post-initialization setup after all controllers are created.

        This method is called by ControllerManager after all four controllers
        (pointer, keyboard, screen, dialogs) have been instantiated. It allows
        controllers to:

        - Access sibling controllers via controller_manager
        - Perform cross-controller initialization
        - Set up runtime state that depends on other components

        Implementations are optional; the base implementation is a no-op.

        Args:
            *args: Positional arguments (currently unused; reserved for extensions).
            **kwargs: Keyword arguments (currently unused; reserved for extensions).

        Example:
            >>> def setup_postinit(self, controller_manager, *args, **kwargs):
            ...     # Access screen size from sibling controller:
            ...     self._screen_controller = controller_manager.screen
            ...     self._screen_controller.get_size()

        Note:
            This is called automatically by ControllerManager; users should not
            invoke it directly.
        """
        pass


class AbstractOSAL(_AbstractBase):
    """Base class for OS Abstraction Layer implementations.

    OSAL classes provide the platform-specific primitives that controllers
    delegate to. Each OSAL class (Pointer, Keyboard, Screen, Dialogs) has
    OS-specific implementations (Windows, MacOS, Linux) that handle:

    - Native API calls (Win32, Cocoa, X11, Wayland, etc.)
    - Platform-specific data structures and constants
    - Error handling and edge cases unique to each OS

    OSAL instances are created by factory functions in osal/__init__.py and
    are typically not instantiated directly by users.

    Args:
        **kwargs: Platform-specific initialization parameters. Common examples:
            - display: X11 Display connection (Linux/X11)
            - screen_index: Monitor index for multi-screen setups

    Example:
        >>> # Typically created via factory:
        >>> from pyautogui2.osal import get_osal
        >>> pointer = get_osal('pointer')
        >>> pointer.move_to(100, 200)

    Note:
        Subclasses must implement all abstract methods defined in
        osal/abstract_cls.py for their respective component (Pointer, Keyboard,
        Screen, or Dialogs).
    """

    def __init__(self, *_args, **_kwargs):
        """Initialize the OSAL implementation with platform-specific parameters.

        Args:
            *args: Positional arguments (platform-specific).
            **kwargs: Platform-specific keyword arguments. Examples:
                - display: X11 Display object (Linux/X11)
                - session: Wayland session handle (Linux/Wayland)
                - screen_index: Monitor index (all platforms)

        Note:
            Subclasses should call super().__init__(*args, **kwargs) and then perform
            their own platform-specific initialization.
        """
        super().__init__()

    # Not abstractmethod
    def setup_postinit(self, *_args, **_kwargs):
        """Perform post-initialization setup with runtime context.

        This method is called after the OSAL instance is created to provide
        runtime context that was not available during __init__, such as:

        - Screen dimensions from the screen OSAL
        - References to the controller manager
        - Configuration loaded from settings

        Unlike controller setup_postinit, OSAL setup_postinit receives explicit
        context via kwargs rather than accessing a controller_manager attribute.

        Args:
            *args: Runtime context.
            **kwargs: Runtime context dictionary.

        Example:
            >>> osal.setup_postinit(
            ...     screen_size_max=(1920, 1080)
            ... )

        Note:
            Called automatically by ControllerManager during initialization.
            Implementations should be idempotent (safe to call multiple times).
        """
        pass

