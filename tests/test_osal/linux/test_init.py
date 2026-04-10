"""Tests for Linux OSAL initialization and dynamic class composition."""

from unittest.mock import MagicMock, patch

import pytest

from pyautogui2.osal.abstract_cls import AbstractPointer
from pyautogui2.osal.linux import _compose_linux_class, _make_class, get_osal
from pyautogui2.utils.exceptions import PyAutoGUIException
from tests.mocks.osal.linux.mock_parts import (
    MockBasePointerPart,
    MockDEPointerPart,
    MockDSPointerPart,
)


class TestComposeLinuxClass:
    """Tests for _compose_linux_class() function."""

    def test_compose_creates_class_with_correct_name(self, isolated_linux):
        """_compose_linux_class() creates class with correct name."""
        result = _compose_linux_class(
            "pointer",
            MockBasePointerPart,
            MockDEPointerPart,
            MockDSPointerPart
        )

        assert result.__name__ == "LinuxPointer"

    def test_compose_creates_class_with_correct_bases(self, isolated_linux):
        """_compose_linux_class() creates class with correct base classes."""
        result = _compose_linux_class(
            "pointer",
            MockBasePointerPart,
            MockDEPointerPart,
            MockDSPointerPart
        )

        assert MockBasePointerPart in result.__bases__
        assert MockDEPointerPart in result.__bases__
        assert MockDSPointerPart in result.__bases__

    def test_compose_generates_backend_id_from_all_parts(self, isolated_linux):
        """_compose_linux_class() generates BACKEND_ID from all parts."""
        result = _compose_linux_class(
            "pointer",
            MockBasePointerPart,
            MockDEPointerPart,
            MockDSPointerPart
        )

        assert result.BACKEND_ID == "MockBasePointerPart, MockDEPointerPart, MockDSPointerPart"

    def test_compose_without_de(self, isolated_linux):
        """_compose_linux_class() without DE part should success."""
        class FullBasePart(AbstractPointer):
            BACKEND_ID = "FullBasePart"

            def button_up(self): pass
            def button_down(self): pass
            def click(self): pass
            def drag_to(self): pass
            def get_pos(self): pass
            def get_primary_button(self): pass
            def mouse_info(self): pass
            def move_to(self): pass
            def scroll(self): pass

        result = _compose_linux_class(
            "pointer",
            FullBasePart,
            None,
            MockDSPointerPart
        )

        assert result.BACKEND_ID == "FullBasePart, MockDSPointerPart"

    def test_compose_without_ds(self, isolated_linux):
        """_compose_linux_class() without DS part should success."""
        class FullBasePart(AbstractPointer):
            BACKEND_ID = "FullBasePart"

            def button_up(self): pass
            def button_down(self): pass
            def click(self): pass
            def drag_to(self): pass
            def get_pos(self): pass
            def get_primary_button(self): pass
            def mouse_info(self): pass
            def move_to(self): pass
            def scroll(self): pass

        result = _compose_linux_class(
            "pointer",
            FullBasePart,
            MockDEPointerPart,
            None
        )

        assert result.BACKEND_ID == "FullBasePart, MockDEPointerPart"

    def test_compose_without_de_nor_ds(self, isolated_linux):
        """_compose_linux_class() without DE nor DS parts should success."""
        class FullBasePart(AbstractPointer):
            BACKEND_ID = "FullBasePart"

            def button_up(self): pass
            def button_down(self): pass
            def click(self): pass
            def drag_to(self): pass
            def get_pos(self): pass
            def get_primary_button(self): pass
            def mouse_info(self): pass
            def move_to(self): pass
            def scroll(self): pass

        result = _compose_linux_class(
            "pointer",
            FullBasePart,
            None,
            None
        )

        assert result.BACKEND_ID == "FullBasePart"

    def test_compose_generates_backend_id_uses_class_name_if_no_backend_id(self, isolated_linux):
        """_compose_linux_class() uses __name__ if part has no BACKEND_ID."""
        class PartWithoutBackendId:
            pass

        class PartWithBackendId:
            BACKEND_ID = "NamedPart"

        class AnotherPartWithoutId:
            pass

        result = _compose_linux_class(
            "test",
            PartWithoutBackendId,
            PartWithBackendId,
            AnotherPartWithoutId
        )

        # Should use __name__ for classes without BACKEND_ID
        assert "PartWithoutBackendId" in result.BACKEND_ID
        assert "NamedPart" in result.BACKEND_ID
        assert "AnotherPartWithoutId" in result.BACKEND_ID

    def test_compose_generates_docstring(self, isolated_linux):
        """_compose_linux_class() generates descriptive docstring."""
        result = _compose_linux_class(
            "pointer",
            MockBasePointerPart,
            MockDEPointerPart,
            MockDSPointerPart
        )

        assert "Linux Pointer implementation" in result.__doc__
        assert "MockBasePointerPart" in result.__doc__
        assert "MockDEPointerPart" in result.__doc__
        assert "MockDSPointerPart" in result.__doc__

    def test_compose_succeeds_when_all_abstract_methods_implemented(self, isolated_linux):
        """_compose_linux_class() succeeds when parts provide all implementations."""
        result = _compose_linux_class(
            "pointer",
            MockBasePointerPart,
            MockDEPointerPart,
            MockDSPointerPart
        )

        assert result.__name__ == "LinuxPointer"

        # Verify combined implementation works
        instance = result()
        instance.get_pos.return_value = (0, 0)
        instance.move_to.return_value = "move"
        instance.button_down.return_value = "button_down"

        assert instance.get_pos() == (0, 0)
        assert instance.move_to(10, 20) == "move"
        assert instance.button_down("left") == "button_down"

    def test_compose_raises_if_abstract_methods_remain_unimplemented(self, isolated_linux):
        """_compose_linux_class() raises PyAutoGUIException if methods missing."""
        # Create parts that DON'T implement all abstract methods
        class IncompleteBasePart(AbstractPointer):
            BACKEND_ID = "IncompleteBase"
            # Missing: move, click, get_position

        class IncompleteDesktopPart(AbstractPointer):
            BACKEND_ID = "IncompleteDesktop"
            # Missing: move, click, get_position

        class IncompleteDisplayPart(AbstractPointer):
            BACKEND_ID = "IncompleteDisplay"
            # Missing: move, click, get_position

        with pytest.raises(PyAutoGUIException) as exc_info:
            _compose_linux_class(
                "pointer",
                IncompleteBasePart,
                IncompleteDesktopPart,
                IncompleteDisplayPart
            )

        error_message = str(exc_info.value)
        assert "LinuxPointer" in error_message
        assert "IncompleteBase, IncompleteDesktop, IncompleteDisplay" in error_message
        # At least one of the missing methods should be mentioned
        assert any(method in error_message for method in ["move", "click", "get_position"])

    def test_compose_error_message_includes_class_name_and_missing_methods(self, isolated_linux):
        """_compose_linux_class() error message is descriptive."""
        class PartialBasePart(AbstractPointer):
            BACKEND_ID = "PartialBase"

            def get_position(self):
                return (0, 0)
            # Missing: move, click

        class EmptyDesktopPart(AbstractPointer):
            BACKEND_ID = "EmptyDesktop"
            # Missing: all methods

        class EmptyDisplayPart(AbstractPointer):
            BACKEND_ID = "EmptyDisplay"
            # Missing: all methods

        with pytest.raises(PyAutoGUIException) as exc_info:
            _compose_linux_class(
                "pointer",
                PartialBasePart,
                EmptyDesktopPart,
                EmptyDisplayPart
            )

        error_message = str(exc_info.value)
        assert "class LinuxPointer" in error_message
        assert "inherit: PartialBase, EmptyDesktop, EmptyDisplay" in error_message
        assert "needs to implement" in error_message


class TestMakeClass:
    """Tests for _make_class() function."""

    @patch("pyautogui2.osal.linux.get_display_server_osal_parts")
    @patch("pyautogui2.osal.linux.get_desktop_osal_parts")
    @patch("pyautogui2.osal.linux._compose_linux_class")
    def test_make_class_retrieves_all_parts(
        self, mock_compose, mock_get_desktop, mock_get_display
    ):
        """_make_class() retrieves base, desktop, and display parts."""
        # Setup mocks
        mock_base_pointer_part = MagicMock(name="LinuxPointerPart")
        mock_desktop_pointer_part = MagicMock(name="GnomePointerPart")
        mock_display_pointer_part = MagicMock(name="X11PointerPart")

        mock_get_desktop.return_value = {"pointer": mock_desktop_pointer_part}
        mock_get_display.return_value = {"pointer": mock_display_pointer_part}

        # Mock globals() to return base part
        with patch("pyautogui2.osal.linux.globals", return_value={
            "LinuxPointerPart": mock_base_pointer_part
        }):
            _make_class("pointer")

        mock_compose.assert_called_once_with(
            "pointer",
            mock_base_pointer_part,
            mock_desktop_pointer_part,
            mock_display_pointer_part
        )

    @patch("pyautogui2.osal.linux.get_display_server_osal_parts")
    @patch("pyautogui2.osal.linux.get_desktop_osal_parts")
    def test_make_class_raises_if_base_part_missing(
        self, mock_get_desktop, mock_get_display
    ):
        """_make_class() raises RuntimeError if base part not found."""
        mock_get_desktop.return_value = {"pointer": MagicMock()}
        mock_get_display.return_value = {"pointer": MagicMock()}

        # Mock globals() to NOT have the base part
        with patch("pyautogui2.osal.linux.globals", return_value={}), \
             pytest.raises(RuntimeError, match="Missing base part class: LinuxPointerPart"):
            _make_class("pointer")

    @patch("pyautogui2.osal.linux.get_display_server_osal_parts")
    @patch("pyautogui2.osal.linux.get_desktop_osal_parts")
    @patch("pyautogui2.osal.linux._compose_linux_class")
    def test_make_class_returns_composed_class(
        self, mock_compose, mock_get_desktop, mock_get_display
    ):
        """_make_class() returns result from _compose_linux_class()."""
        mock_composed_class = MagicMock(name="LinuxPointer")
        mock_compose.return_value = mock_composed_class

        mock_base_pointer_part = MagicMock(name="LinuxPointerPart")
        mock_get_desktop.return_value = {"pointer": MagicMock()}
        mock_get_display.return_value = {"pointer": MagicMock()}

        with patch("pyautogui2.osal.linux.globals", return_value={
            "LinuxPointerPart": mock_base_pointer_part
        }):
            result = _make_class("pointer")

        assert result is mock_composed_class


class TestGetOsal:
    """Tests for get_osal() function."""

    @patch("pyautogui2.osal.linux._make_class")
    def test_get_osal_creates_all_four_components(self, mock_make_class):
        """get_osal() creates Pointer, Keyboard, Screen, and Dialogs."""
        mock_pointer_class = MagicMock()
        mock_keyboard_class = MagicMock()
        mock_screen_class = MagicMock()
        mock_dialogs_class = MagicMock()

        def make_class_side_effect(name):
            return {
                "pointer": mock_pointer_class,
                "keyboard": mock_keyboard_class,
                "screen": mock_screen_class,
                "dialogs": mock_dialogs_class,
            }[name]

        mock_make_class.side_effect = make_class_side_effect

        _ = get_osal()

        # Verify _make_class called for each component
        assert mock_make_class.call_count == 4
        mock_make_class.assert_any_call("pointer")
        mock_make_class.assert_any_call("keyboard")
        mock_make_class.assert_any_call("screen")
        mock_make_class.assert_any_call("dialogs")

    @patch("pyautogui2.osal.linux._make_class")
    def test_get_osal_instantiates_all_components(self, mock_make_class):
        """get_osal() instantiates all component classes."""
        mock_pointer_class = MagicMock()
        mock_keyboard_class = MagicMock()
        mock_screen_class = MagicMock()
        mock_dialogs_class = MagicMock()

        def make_class_side_effect(name):
            return {
                "pointer": mock_pointer_class,
                "keyboard": mock_keyboard_class,
                "screen": mock_screen_class,
                "dialogs": mock_dialogs_class,
            }[name]

        mock_make_class.side_effect = make_class_side_effect

        _ = get_osal()

        # Verify all classes were instantiated
        mock_pointer_class.assert_called_once_with()
        mock_keyboard_class.assert_called_once_with()
        mock_screen_class.assert_called_once_with()
        mock_dialogs_class.assert_called_once_with()

    @patch("pyautogui2.osal.linux._make_class")
    def test_get_osal_returns_osal_with_all_components(self, mock_make_class):
        """get_osal() returns OSAL instance with all components."""
        mock_pointer_class = MagicMock()
        mock_keyboard_class = MagicMock()
        mock_screen_class = MagicMock()
        mock_dialogs_class = MagicMock()

        def make_class_side_effect(name):
            return {
                "pointer": mock_pointer_class,
                "keyboard": mock_keyboard_class,
                "screen": mock_screen_class,
                "dialogs": mock_dialogs_class,
            }[name]

        mock_make_class.side_effect = make_class_side_effect

        result = get_osal()

        # Verify OSAL has all components
        assert result.pointer == mock_pointer_class.return_value
        assert result.keyboard == mock_keyboard_class.return_value
        assert result.screen == mock_screen_class.return_value
        assert result.dialogs == mock_dialogs_class.return_value

    @patch("pyautogui2.osal.linux._make_class")
    def test_get_osal_uses_correct_cast_types(self, mock_make_class):
        """get_osal() casts dynamically created classes to correct types."""
        # This test verifies the type casting doesn't break at runtime
        mock_class = MagicMock()
        mock_make_class.return_value = mock_class

        result = get_osal()

        # Should not raise any type errors
        assert result is not None
        assert hasattr(result, "pointer")
        assert hasattr(result, "keyboard")
        assert hasattr(result, "screen")
        assert hasattr(result, "dialogs")
