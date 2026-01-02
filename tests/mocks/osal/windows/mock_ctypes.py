"""Mock ctypes structures and types for Windows testing."""

# ============================================================================
# Mock C types
# ============================================================================

class MockCType:
    """Base class for mock C types."""
    def __init__(self, value=0):
        self.value = value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    def __eq__(self, other):
        """Compare by value."""
        if isinstance(other, (self.__class__, int)):
            return self.value == (other.value if hasattr(other, 'value') else other)
        return False

    def __hash__(self):
        """Make hashable."""
        return hash(self.value)


class c_long(MockCType):
    """Mock ctypes.c_long type."""
    pass


class c_long_p(MockCType):
    """Mock ctypes.c_long_p type."""
    pass


class c_ulong(MockCType):
    """Mock ctypes.c_ulong type."""
    pass


class c_int(MockCType):
    """Mock ctypes.c_int type."""
    pass


class c_uint(MockCType):
    """Mock ctypes.c_uint type."""
    pass


class c_uint32(MockCType):
    """Mock ctypes.c_uint32 type."""
    pass


class c_uint64(MockCType):
    """Mock ctypes.c_uint64 type."""
    pass


class c_short(MockCType):
    """Mock ctypes.c_short type."""
    pass


class c_ushort(MockCType):
    """Mock ctypes.c_ushort type."""
    pass


class c_void_p(MockCType):
    """Mock ctypes.c_void_p type."""
    pass


# ============================================================================
# Mock wintypes
# ============================================================================

class DWORD(c_ulong):
    """Mock wintypes.DWORD (unsigned 32-bit)."""
    pass


class WORD(c_ushort):
    """Mock wintypes.WORD (unsigned 16-bit)."""
    pass


class LONG(c_long):
    """Mock wintypes.LONG (signed 32-bit)."""
    pass


class ULONG(c_ulong):
    """Mock wintypes.ULONG (unsigned 32-bit)."""
    pass


class UINT(c_uint):
    """Mock wintypes.UINT (unsigned int)."""
    pass


class HMONITOR(c_void_p):
    """Mock wintypes.HMONITOR (void pointer)."""
    pass


class HDC(c_void_p):
    """Mock wintypes.HDC (void pointer)."""
    pass


class LPARAM(c_long_p):
    """Mock wintypes.LPARAM (long pointer)."""
    pass


# ============================================================================
# Pointer Functions
# ============================================================================

class MockPointer:
    """Mock for ctypes pointer."""

    def __init__(self, obj):
        """Create a mock pointer to an object.

        Args:
            obj: Object to point to (Structure, Union, or basic type)
        """
        self._obj = obj
        self.contents = obj

    def __repr__(self):
        return f"<MockPointer to {self._obj}>"

    def __bool__(self):
        """Pointer is truthy if it points to something."""
        return self._obj is not None


def pointer(obj):
    """Create a mock pointer to a ctypes instance.

    Args:
        obj: Object to create pointer to

    Returns:
        MockPointer instance

    Example:
        >>> rect = RECT()
        >>> p_rect = pointer(rect)
        >>> p_rect.contents.left = 10
    """
    return MockPointer(obj)


def POINTER(type_):
    """Create a mock pointer type.

    Args:
        type_: Type to create pointer type for

    Returns:
        A class that creates MockPointer instances

    Example:
        >>> LPRECT = POINTER(RECT)
        >>> p_rect = LPRECT()
    """
    class PointerType:
        def __init__(self, *args):
            if args:
                self._pointer = MockPointer(args[0])
            else:
                self._pointer = MockPointer(None)

        def __call__(self, obj=None):
            if obj is None:
                return MockPointer(type_())
            return MockPointer(obj)

        @property
        def contents(self):
            return self._pointer.contents

        def __repr__(self):
            return f"<POINTER({type_.__name__})>"

    PointerType.__name__ = f"LP_{type_.__name__ if hasattr(type_, '__name__') else str(type_)}"
    return PointerType


# ============================================================================
# Mock Structures
# ============================================================================

class MockStructure:
    """Base class for mock ctypes.Structure."""
    _fields_ = []

    # Add storage info for ctypes.pointer() compatibility
    _type_ = "MockStructure"
    _length_ = 1

    def __init__(self, **kwargs):
        # Initialize all fields to their default values
        for field_name, field_type in self._fields_:
            if hasattr(field_type, '_type_'):  # Array type
                setattr(self, field_name, field_type())
            elif callable(field_type):
                try:
                    setattr(self, field_name, field_type())
                except Exception:
                    setattr(self, field_name, None)
            else:
                setattr(self, field_name, None)

        # Set provided values
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        # Unwrap MockCType fields to native Python values (mirrors real ctypes behavior)
        fields = super().__getattribute__("_fields_")
        field_names = {f[0] for f in fields}
        if name in field_names and isinstance(value, MockCType):
            return value.value
        return value

    def __repr__(self):
        fields = ", ".join(
            f"{name}={getattr(self, name, None)!r}"
            for name, _ in self._fields_
        )
        return f"{self.__class__.__name__}({fields})"

    def __eq__(self, other):
        """Compare structures by field values.

        Args:
            other: Other structure to compare with

        Returns:
            True if all fields are equal, False otherwise
        """
        if not isinstance(other, self.__class__):
            return False

        for field_name, _ in self._fields_:
            self_value = getattr(self, field_name, None)
            other_value = getattr(other, field_name, None)

            if hasattr(self_value, 'value') and hasattr(other_value, 'value'):
                if self_value.value != other_value.value:
                    return False
            elif self_value != other_value:
                return False

        return True

    def __hash__(self):
        """Make structure hashable (needed for set/dict operations).

        Note: This is a simplified hash. In production, you might want
        to make structures immutable or use a different approach.
        """
        try:
            field_values = tuple(
                getattr(self, name, None)
                for name, _ in self._fields_
            )
            return hash((self.__class__.__name__, field_values))
        except TypeError:
            # If fields contain unhashable types, fall back to id
            return hash(id(self))


class MockUnion(MockStructure):
    """Base class for mock ctypes.Union.

    In real ctypes, Union members share the same memory.
    For testing, we simplify this by treating it like a Structure.
    """

    _type_ = "MockUnion"

    def __init__(self):
        # Only initialize the first field (simulate union behavior)
        if self._fields_:
            field_name, field_type = self._fields_[0]
            if callable(field_type):
                setattr(self, field_name, field_type())
            else:
                setattr(self, field_name, 0)

        # Initialize other fields to None
        for field_name, _ in self._fields_[1:]:
            setattr(self, field_name, None)


class POINT(MockStructure):
    """Mock wintypes.POINT structure."""
    _fields_ = [
        ("x", LONG),
        ("y", LONG),
    ]

    def __init__(self):
        self.x = 0
        self.y = 0

    def __repr__(self):
        return f"POINT(x={self.x}, y={self.y})"

Structure = MockStructure
Union = MockUnion


# ============================================================================
# Mock functions
# ============================================================================

def byref(obj):
    """Mock ctypes.byref - returns object directly."""
    return obj


def sizeof(obj_or_type):
    """Mock ctypes.sizeof - returns a fake size."""
    if isinstance(obj_or_type, type):
        # It's a type
        if hasattr(obj_or_type, '_fields_'):
            # Count fields (very simplified)
            return len(obj_or_type._fields_) * 4
        return 32
    # It's an instance
    return 32


# ============================================================================
# Mock DLL loading functions
# ============================================================================

def WinDLL(name, *_args, **_kwargs):
    """Mock ctypes.WinDLL.

    Returns the appropriate mock DLL from sys.modules.

    Args:
        name: DLL name (e.g., "user32", "kernel32")

    Returns:
        Mock DLL object from sys.modules
    """
    import sys

    # Normalize name (user32.dll -> user32)
    dll_name = name.lower().replace('.dll', '')

    # Return from sys.modules if available
    if dll_name in sys.modules:
        return sys.modules[dll_name]

    # Fallback: return a MagicMock
    from unittest.mock import MagicMock
    mock_dll = MagicMock(name=f"MockDLL({dll_name})")
    sys.modules[dll_name] = mock_dll
    return mock_dll


def WINFUNCTYPE(*args, **_kwargs):
    """Mock ctypes.WINFUNCTYPE.

    In real ctypes, this creates a callback type.
    For mocking, we just return a decorator that passes through the function.

    Usage:
        @WINFUNCTYPE(c_int, c_int)
        def my_callback(x):
            return x * 2

    Returns:
        Identity decorator (returns the function unchanged)
    """
    def decorator(func):
        """Pass-through decorator."""
        # Optionally mark the function as a callback
        func._is_winfunctype = True
        func._winfunctype_args = args
        return func
    return decorator


# ============================================================================
# Mock windll namespace (will be populated by fixture)
# ============================================================================

# This will be replaced by the fixture with proper mocks
windll = None


# ============================================================================
# Expose wintypes as a module attribute
# ============================================================================

class _WinTypes:
    """Mock ctypes.wintypes module.

    This allows: from ctypes import wintypes
    """
    DWORD = DWORD
    WORD = WORD
    LONG = LONG
    ULONG = ULONG
    UINT = UINT
    HMONITOR = HMONITOR
    HDC = HDC
    LPARAM = LPARAM
    POINT = POINT

# Create instance that can be imported
wintypes = _WinTypes()


def reset_mock(**_kw): pass
