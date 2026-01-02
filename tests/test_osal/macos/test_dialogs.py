"""Unit tests for MacOSDialogs."""


class TestMacOSDialogs:
    """Dialog wrapper tests."""

    def test_alert_forwards_to_pymsgbox(self, macos_dialogs):
        _ = macos_dialogs.alert("hello", title="T", button="OK")
        macos_dialogs._pymsgbox.alert.assert_called_once_with("hello", "T", "OK", None, None)

    def test_confirm_forwards(self, macos_dialogs):
        _ = macos_dialogs.confirm("are you?", title="Q", buttons=("Yes","No"))
        macos_dialogs._pymsgbox.confirm.assert_called_once_with("are you?", "Q", ("Yes","No"), None, None)

    def test_prompt_forwards(self, macos_dialogs):
        _ = macos_dialogs.prompt("who?", title="Ask", default="me")
        macos_dialogs._pymsgbox.prompt.assert_called_once_with("who?", "Ask", "me", None, None)

    def test_password_forwards(self, macos_dialogs):
        _ = macos_dialogs.password("pwd?", title="P", default="EmptyPassword", mask="#")
        macos_dialogs._pymsgbox.password.assert_called_once_with("pwd?", "P", "EmptyPassword", "#", None, None)
