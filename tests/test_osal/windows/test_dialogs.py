"""Unit tests for WindowsDialogs."""


class TestWindowsDialogs:
    """Dialog wrapper tests."""

    def test_alert_forwards_to_pymsgbox(self, windows_dialogs):
        _ = windows_dialogs.alert("hello", title="T", button="OK")
        windows_dialogs._pymsgbox.alert.assert_called_once_with("hello", "T", "OK", None, None)

    def test_confirm_forwards(self, windows_dialogs):
        _ = windows_dialogs.confirm("are you?", title="Q", buttons=("Yes","No"))
        windows_dialogs._pymsgbox.confirm.assert_called_once_with("are you?", "Q", ("Yes","No"), None, None)

    def test_prompt_forwards(self, windows_dialogs):
        _ = windows_dialogs.prompt("who?", title="Ask", default="me")
        windows_dialogs._pymsgbox.prompt.assert_called_once_with("who?", "Ask", "me", None, None)

    def test_password_forwards(self, windows_dialogs):
        _ = windows_dialogs.password("pwd?", title="P", default="EmptyPassword", mask="#")
        windows_dialogs._pymsgbox.password.assert_called_once_with("pwd?", "P", "EmptyPassword", "#", None, None)
