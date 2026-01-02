"""Base class for mock OSAL implementations."""
import inspect

from unittest.mock import MagicMock


class MockOSALBase:
    """Base class providing common mock management functionality.

    All mock OSAL implementations should inherit from this to get:
    - Automatic mock registration via register_mock()
    - Centralized storage in self.mocks MagicMock
    - Batch reset functionality via reset_mocks()

    Attributes:
        mocks: MagicMock containing all registered MagicMock methods.
               Used for assert_has_calls() to verify call sequences.

    Example:
        class MockPointerOSAL(AbstractPointer, MockOSALBase):
            def __init__(self):
                MockOSALBase.__init__(self)

                # Register mock with automatic storage in self.mocks
                self.move_to = self.register_mock(
                    MagicMock(side_effect=self._move_to_effect)
                )

                # Later in tests:
                # mock.mocks.assert_has_calls([call.move_to(10, 20)])
    """

    def __init__(self):
        """Initialize the mocks MagicMock."""
        self.mocks = MagicMock()

    def register_mock(self, mock_obj: MagicMock, name: str = None) -> MagicMock:
        """Register a MagicMock in the mocks namespace.

        This method automatically stores the mock in self.mocks using either
        the provided name or the mock's spec name (from _spec_name attribute).

        Args:
            mock_obj: MagicMock instance to register.
            name: Optional explicit name. If None, uses mock_obj._spec_name
                  or falls back to looking up the attribute name in the caller.

        Returns:
            The same MagicMock instance (for fluent chaining).

        Example:
            # Explicit name
            self.move_to = self.register_mock(MagicMock(...), "move_to")

            # Auto-detect from assignment (Python magic)
            self.move_to = self.register_mock(MagicMock(...))

            # Both result in: self.mocks.move_to = same mock object

        Note:
            Auto-detection works because Python evaluates the right side
            (register_mock) before the assignment, so we can inspect the
            frame to find the target attribute name.
        """
        # Auto-detect name from calling context if not provided
        if name is None:
            frame = inspect.currentframe().f_back
            # Get the source line: "self.move_to = self.register_mock(...)"
            code_context = inspect.getframeinfo(frame).code_context
            if code_context:
                line = code_context[0].strip()
                # Extract "move_to" from "self.move_to = ..."
                if "=" in line and "self." in line:
                    parts = line.split("=")[0].strip()
                    if parts.startswith("self."):
                        name = parts.replace("self.", "").strip()

        # Fallback: try to get spec name from MagicMock
        if name is None and hasattr(mock_obj, "_spec_name"):
            name = mock_obj._spec_name

        if not name:
            raise RuntimeError(f"Name not be found for {mock_obj}")

        setattr(self, name, mock_obj)
        setattr(self.mocks, name, mock_obj)

        return mock_obj

    def reset_mocks(self) -> None:
        """Reset all MagicMock objects in the mocks namespace.

        This iterates over all attributes in self.mocks and calls reset_mock()
        on each MagicMock instance. Useful in fixtures to clear call history
        after setup_postinit() or between test phases.

        Example:
            # In fixture after initialization
            pointer_controller._osal.reset_mocks()

            # Now all call counts are zero
            pointer_controller.move_to(10, 20)
            pointer_controller._osal.move_to.assert_called_once()

        Note:
            Only resets MagicMock instances. Any other attributes in mocks
            namespace are ignored (e.g., non-mock state variables).
        """
        for attr_name in dir(self.mocks):
            # Skip private/magic attributes
            if attr_name.startswith("_"):
                continue

            attr = getattr(self.mocks, attr_name)

            # Only reset MagicMock instances
            if isinstance(attr, MagicMock):
                attr.reset_mock()

        self.mocks.reset_mock()


__all__ = ["MockOSALBase"]
