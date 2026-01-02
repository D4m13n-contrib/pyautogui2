"""Tests for DialogsController."""
from unittest.mock import MagicMock

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException


class TestDialogsAlert:
    def test_alert_forwards_to_osal(self, dialogs_controller):
        result = dialogs_controller.alert("hello", title="t")
        assert result == "Alert Ok"
        dialogs_controller._osal.alert.assert_called_once()


class TestDialogsConfirm:
    def test_confirm_forwards_and_returns(self, dialogs_controller):
        res = dialogs_controller.confirm("sure?", title="Confirm", buttons=("Yes", "No"))
        assert res == "Confirmed"
        dialogs_controller._osal.confirm.assert_called_once()


class TestDialogsPrompt:
    def test_prompt_forwards_and_returns(self, dialogs_controller):
        res = dialogs_controller.prompt("enter name:", title="Name", default="John")
        assert res == "User Input"
        dialogs_controller._osal.prompt.assert_called_once()


class TestDialogsPassword:
    def test_password_forwards_and_returns(self, dialogs_controller):
        res = dialogs_controller.password("enter pass:", title="Login", default="x", mask="#")
        assert res == "P4ssw0rd"
        dialogs_controller._osal.password.assert_called_once()


class TestDialogsControllerInitialization:
    """Test DialogsController initialization."""

    def test_init_with_bad_backend_raises(self):
        """Test initialization with bad backend should raises."""
        from pyautogui2.controllers.dialogs import DialogsController

        mock_backend = MagicMock()  # not AbstractDialogs subclass
        with pytest.raises(PyAutoGUIException):
            DialogsController(osal=mock_backend)

    def test_init_with_explicit_backends(self):
        """Test initialization with explicit dialogs backends."""
        from pyautogui2.controllers.dialogs import DialogsController
        from pyautogui2.osal.abstract_cls import AbstractDialogs

        mock_backend = MagicMock(spec_set=AbstractDialogs)
        pc = DialogsController(osal=mock_backend)
        assert pc._osal is mock_backend


class TestDialogsRepresentation:
    """Test string representations for debugging."""

    def test_repr_contains_class_name(self, dialogs_controller):
        """Test that __repr__ contains class name."""
        rep = repr(dialogs_controller)
        assert "DialogsController" in rep

    def test_str_is_readable(self, dialogs_controller):
        """Test that __str__ provides readable output."""
        string = str(dialogs_controller)
        assert len(string) > 0
        # Should mention dialogs or controller
        assert "dialogs" in string.lower() or "controller" in string.lower()
