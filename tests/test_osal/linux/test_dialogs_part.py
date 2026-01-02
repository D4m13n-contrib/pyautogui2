"""Tests for LinuxDialogsPart."""






class TestLinuxDialogsAlert:
    """Tests for alert() function."""

    def test_alert(self, linux_dialogs):
        """Call alert() method."""
        linux_dialogs.alert("Alert", "Title", "Ok", None, None)
        linux_dialogs._pymsgbox.alert.assert_called_once_with("Alert", "Title", "Ok", None, None)


class TestLinuxDialogsConfirm:
    """Tests for confirm() function."""

    def test_confirm(self, linux_dialogs):
        """Call confirm() method."""
        linux_dialogs.confirm("Confirm", "Title", "Ok", None, None)
        linux_dialogs._pymsgbox.confirm.assert_called_once_with("Confirm", "Title", "Ok", None, None)


class TestLinuxDialogsPrompt:
    """Tests for prompt() function."""

    def test_prompt(self, linux_dialogs):
        """Call prompt() method."""
        linux_dialogs.prompt("Prompt", "Title", "Default", None, None)
        linux_dialogs._pymsgbox.prompt.assert_called_once_with("Prompt", "Title", "Default", None, None)


class TestLinuxDialogsPassword:
    """Tests for password() function."""

    def test_password(self, linux_dialogs):
        """Call password() method."""
        linux_dialogs.password("Password", "Title", "Default", "*", None, None)
        linux_dialogs._pymsgbox.password.assert_called_once_with("Password", "Title", "Default", "*", None, None)
