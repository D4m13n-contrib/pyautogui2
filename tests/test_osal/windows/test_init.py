"""Unit tests for pyautogui2.osal.windows.__init__."""


class TestGetOsal:
    """Tests for get_osal()."""

    def test_get_osal_returns_osal_instance(self, isolated_windows):
        from pyautogui2.osal.abstract_cls import OSAL
        from pyautogui2.osal.windows import get_osal

        result = get_osal()

        assert isinstance(result, OSAL)
        assert result.pointer is not None
        assert result.keyboard is not None
        assert result.screen is not None
        assert result.dialogs is not None
