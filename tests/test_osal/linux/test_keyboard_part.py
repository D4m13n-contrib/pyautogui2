"""Tests for LinuxKeyboardPart."""




class TestLinuxKeyboardCodepointCtx:
    """Tests for codepoint_ctx() function."""

    def test_codepoint_ctx(self, linux_keyboard):
        """Call codepoint_ctx() delegates to mouseinfo library."""
        with linux_keyboard.codepoint_ctx() as ctx:
            ctx.type_codepoint_value("1234")
