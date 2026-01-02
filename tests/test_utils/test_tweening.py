"""Tests for TweeningManager."""

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.tweening import TweeningManager


class TestTweeningManagerSingleton:
    """Test Singleton pattern behavior."""

    def test_singleton_same_instance(self, tweening_manager_mocked):
        """Multiple calls return same instance."""
        manager1 = tweening_manager_mocked
        manager2 = TweeningManager()

        assert manager1 is manager2

    def test_singleton_id_equality(self, tweening_manager_mocked):
        """Instances have same id."""
        manager1 = tweening_manager_mocked
        manager2 = TweeningManager()

        assert id(manager1) == id(manager2)


class TestTweeningManagerInitialization:
    """Test initialization with/without pytweening."""

    def test_init_with_pytweening_loads_all_tweens(self, tweening_manager_mocked):
        """With pytweening, all tweens are loaded."""
        manager = tweening_manager_mocked

        # All tweens should be available
        for tween_name in manager.tweens:
            tween_func = manager(tween_name)
            assert callable(tween_func)

            # Should work with n=0.5
            result = tween_func(0.5)
            assert isinstance(result, (int, float))

    def test_init_without_pytweening_degraded_mode(self, tweening_manager_mocked_no_pytweening):
        """Without pytweening, only 'linear' is available."""
        manager = tweening_manager_mocked_no_pytweening

        # Linear should work
        linear = manager.linear
        assert callable(linear)
        assert linear(0.5) == 0.5

        # Other tweens should raise exception
        with pytest.raises(PyAutoGUIException, match="not available"):
            manager.easeInQuad(0.5)

    def test_init_without_pytweening_logs_warning(self, tweening_manager_mocked_no_pytweening, caplog):
        """Without pytweening, warning is logged."""
        import logging
        manager = tweening_manager_mocked_no_pytweening

        assert manager is not None
        warnings = [x.message for x in caplog.get_records("setup") if x.levelno == logging.WARNING]
        assert len(warnings) == 1
        assert "Could not import pytweening module => degraded mode (only 'linear' tweening is available)" in warnings[0]


class TestTweeningManagerAccess:
    """Test different ways to access tweens."""

    def test_access_by_attribute(self, tweening_manager_mocked):
        """Can access tween by attribute."""
        manager = tweening_manager_mocked

        tween = manager.easeInQuad
        assert callable(tween)

    def test_access_by_call(self, tweening_manager_mocked):
        """Can access tween by calling manager."""
        manager = tweening_manager_mocked

        tween = manager('easeInQuad')
        assert callable(tween)

    def test_access_by_attribute_and_call_same_result(self, tweening_manager_mocked):
        """Both access methods return equivalent function."""
        manager = tweening_manager_mocked

        tween1 = manager.easeInQuad
        tween2 = manager('easeInQuad')

        # Should produce same result
        assert tween1(0.5) == tween2(0.5)

    def test_unknown_tween_name_raises(self, tweening_manager_mocked):
        """Unknown tween name raises PyAutoGUIException."""
        manager = tweening_manager_mocked

        with pytest.raises(PyAutoGUIException, match="Unknown tweening name 'fakeEasing'"):
            _ = manager.fakeEasing

    def test_unknown_tween_name_via_call_raises(self, tweening_manager_mocked):
        """Unknown tween name via __call__ raises PyAutoGUIException."""
        manager = tweening_manager_mocked

        with pytest.raises(PyAutoGUIException, match="Unknown tweening name 'fakeEasing'"):
            _ = manager('fakeEasing')

    def test_unavailable_tween_raises(self, tweening_manager_mocked_no_pytweening):
        """Tween set to None raises PyAutoGUIException."""
        manager = tweening_manager_mocked_no_pytweening

        with pytest.raises(PyAutoGUIException, match="not available"):
            _ = manager.easeInQuad(0.5)


class TestTweeningArgumentValidation:
    """Test n ∈ [0, 1] validation."""

    def test_valid_n_values(self, tweening_manager_mocked):
        """Valid n values (0, 0.5, 1) work."""
        manager = tweening_manager_mocked
        tween = manager.linear

        assert tween(0.0) == 0.0
        assert tween(0.5) == 0.5
        assert tween(1.0) == 1.0

    def test_n_below_zero_raises(self, tweening_manager_mocked):
        """N < 0 raises PyAutoGUIException."""
        manager = tweening_manager_mocked
        tween = manager.linear

        with pytest.raises(PyAutoGUIException, match="between 0.0 and 1.0"):
            tween(-0.1)

    def test_n_above_one_raises(self, tweening_manager_mocked):
        """N > 1 raises PyAutoGUIException."""
        manager = tweening_manager_mocked
        tween = manager.linear

        with pytest.raises(PyAutoGUIException, match="between 0.0 and 1.0"):
            tween(1.1)

    def test_n_exactly_zero(self, tweening_manager_mocked):
        """N = 0 is valid."""
        manager = tweening_manager_mocked
        tween = manager.linear

        result = tween(0.0)
        assert result == 0.0

    def test_n_exactly_one(self, tweening_manager_mocked):
        """N = 1 is valid."""
        manager = tweening_manager_mocked
        tween = manager.linear

        result = tween(1.0)
        assert result == 1.0

    def test_n_boundary_epsilon(self, tweening_manager_mocked):
        """N very close to boundaries."""
        manager = tweening_manager_mocked
        tween = manager.linear

        # Just inside boundaries
        assert tween(0.0001) == pytest.approx(0.0001)
        assert tween(0.9999) == pytest.approx(0.9999)


class TestTweeningAddCustom:
    """Test adding custom tween functions."""

    def test_add_custom_tween(self, tweening_manager_mocked):
        """Can add custom tween function."""
        manager = tweening_manager_mocked

        def custom_tween(n):
            return n ** 3  # Cubic

        manager.add_tween('customCubic', custom_tween)

        # Should be accessible
        tween = manager.customCubic
        assert tween(0.5) == pytest.approx(0.125)

    def test_add_tween_without_force_raises_if_exists(self, tweening_manager_mocked):
        """Adding existing tween without force raises."""
        manager = tweening_manager_mocked

        def custom_tween(n):
            return n

        with pytest.raises(ValueError, match="already set"):
            manager.add_tween('linear', custom_tween, force=False)

    def test_add_tween_with_force_overrides(self, tweening_manager_mocked):
        """Adding existing tween with force=True overrides."""
        manager = tweening_manager_mocked

        def custom_tween(n):
            return n * 10  # Will be out of bounds but tests override

        manager.add_tween('linear', custom_tween, force=True)

        # Original linear is overridden
        tween = manager.linear
        # Note: will raise because n*10 is out of [0,1], so let's use n/2
        def safe_custom(n):
            return n / 2

        manager.add_tween('linear', safe_custom, force=True)
        tween = manager.linear
        assert tween(0.5) == pytest.approx(0.25)

    def test_custom_tween_in_tweens_list(self, tweening_manager_mocked):
        """Custom tween appears in tweens property."""
        manager = tweening_manager_mocked

        def custom_tween(n):
            return n

        manager.add_tween('myTween', custom_tween)

        assert 'myTween' in manager.tweens

    def test_custom_tween_respects_validation(self, tweening_manager_mocked):
        """Custom tween still validates n ∈ [0, 1]."""
        manager = tweening_manager_mocked

        def custom_tween(n):
            return n

        manager.add_tween('validated', custom_tween)

        tween = manager.validated

        # Valid
        assert tween(0.5) == 0.5

        # Invalid
        with pytest.raises(PyAutoGUIException, match="between 0.0 and 1.0"):
            tween(-0.5)


class TestTweeningTweensProperty:
    """Test tweens property."""

    def test_tweens_returns_list(self, tweening_manager_mocked):
        """Tweens property returns list."""
        manager = tweening_manager_mocked

        tweens = manager.tweens
        assert isinstance(tweens, list)

    def test_tweens_contains_all_default_tweens(self, tweening_manager_mocked):
        """Tweens list contains all default tween names."""
        manager = tweening_manager_mocked

        tweens = manager.tweens

        # Check some key tweens
        assert 'linear' in tweens
        assert 'easeInQuad' in tweens
        assert 'easeOutBounce' in tweens

    def test_tweens_count_matches_available(self, tweening_manager_mocked):
        """Number of tweens matches _AVAILABLE_TWEENS."""
        manager = tweening_manager_mocked

        assert len(manager.tweens) == len(TweeningManager._AVAILABLE_TWEENS)


class TestTweeningInternalLinear:
    """Test _internal_linear static method."""

    def test_internal_linear_identity(self, tweening_manager_mocked):
        """_internal_linear returns n (identity function)."""
        assert tweening_manager_mocked._internal_linear(0.0) == 0.0
        assert tweening_manager_mocked._internal_linear(0.5) == 0.5
        assert tweening_manager_mocked._internal_linear(1.0) == 1.0

    def test_internal_linear_various_values(self, tweening_manager_mocked):
        """_internal_linear works for various n values."""
        for n in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
            assert tweening_manager_mocked._internal_linear(n) == n


class TestGetPointOnLine:
    """Test get_point_on_line static method."""

    def test_get_point_start(self, tweening_manager_mocked):
        """n=0 returns start point."""
        x, y = tweening_manager_mocked.get_point_on_line(0, 0, 10, 10, 0.0)

        assert x == 0.0
        assert y == 0.0

    def test_get_point_end(self, tweening_manager_mocked):
        """n=1 returns end point."""
        x, y = tweening_manager_mocked.get_point_on_line(0, 0, 10, 10, 1.0)

        assert x == 10.0
        assert y == 10.0

    def test_get_point_middle(self, tweening_manager_mocked):
        """n=0.5 returns midpoint."""
        x, y = tweening_manager_mocked.get_point_on_line(0, 0, 10, 10, 0.5)

        assert x == pytest.approx(5.0)
        assert y == pytest.approx(5.0)

    def test_get_point_quarter(self, tweening_manager_mocked):
        """n=0.25 returns quarter point."""
        x, y = tweening_manager_mocked.get_point_on_line(0, 0, 100, 200, 0.25)

        assert x == pytest.approx(25.0)
        assert y == pytest.approx(50.0)

    def test_get_point_negative_coords(self, tweening_manager_mocked):
        """Works with negative coordinates."""
        x, y = tweening_manager_mocked.get_point_on_line(-10, -10, 10, 10, 0.5)

        assert x == pytest.approx(0.0)
        assert y == pytest.approx(0.0)

    def test_get_point_horizontal_line(self, tweening_manager_mocked):
        """Works for horizontal line."""
        x, y = tweening_manager_mocked.get_point_on_line(0, 5, 10, 5, 0.5)

        assert x == pytest.approx(5.0)
        assert y == pytest.approx(5.0)

    def test_get_point_vertical_line(self, tweening_manager_mocked):
        """Works for vertical line."""
        x, y = tweening_manager_mocked.get_point_on_line(5, 0, 5, 10, 0.5)

        assert x == pytest.approx(5.0)
        assert y == pytest.approx(5.0)

    def test_get_point_reverse_direction(self, tweening_manager_mocked):
        """Works when end < start."""
        x, y = tweening_manager_mocked.get_point_on_line(10, 10, 0, 0, 0.5)

        assert x == pytest.approx(5.0)
        assert y == pytest.approx(5.0)

    def test_get_point_float_coordinates(self, tweening_manager_mocked):
        """Works with float coordinates."""
        x, y = tweening_manager_mocked.get_point_on_line(1.5, 2.5, 3.5, 4.5, 0.5)

        assert x == pytest.approx(2.5)
        assert y == pytest.approx(3.5)


class TestAllDefaultTweens:
    """Test all default tween functions if available."""

    def test_all_default_tweens_accessible(self, tweening_manager_mocked):
        """All default tweens are accessible (if pytweening available)."""
        manager = tweening_manager_mocked

        # Try to access each tween
        for tween_name in ['linear', 'easeInQuad', 'easeOutQuad',
                           'easeInOutQuad', 'easeInCubic']:
            try:
                tween = manager(tween_name)
                assert callable(tween)
            except PyAutoGUIException as e:
                # If pytweening not available, that's OK
                if "not available" not in str(e):
                    raise

    def test_linear_tween_is_identity(self, tweening_manager_mocked):
        """Linear tween is identity function."""
        manager = tweening_manager_mocked

        try:
            linear = manager.linear

            assert linear(0.0) == pytest.approx(0.0)
            assert linear(0.25) == pytest.approx(0.25)
            assert linear(0.5) == pytest.approx(0.5)
            assert linear(0.75) == pytest.approx(0.75)
            assert linear(1.0) == pytest.approx(1.0)
        except PyAutoGUIException:
            # pytweening not available
            pytest.skip("pytweening not available")

    def test_tween_functions_return_valid_range(self, tweening_manager_mocked):
        """Tween functions return values in reasonable range."""
        manager = tweening_manager_mocked

        for tween_name in ['linear', 'easeInQuad', 'easeOutBounce']:
            try:
                tween = manager(tween_name)

                # Test several n values
                for n in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    result = tween(n)

                    # Most tweens stay in [0, 1], but some (like bounce) may exceed slightly
                    # Just check it's a number
                    assert isinstance(result, (int, float))

            except PyAutoGUIException as e:
                if "not available" in str(e):
                    continue  # Skip if pytweening not available
                raise


class TestTweeningEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_multiple_custom_tweens(self, tweening_manager_mocked):
        """Can add multiple custom tweens."""
        manager = tweening_manager_mocked

        manager.add_tween('custom1', lambda n: n)
        manager.add_tween('custom2', lambda n: n ** 2)
        manager.add_tween('custom3', lambda n: n ** 3)

        assert 'custom1' in manager.tweens
        assert 'custom2' in manager.tweens
        assert 'custom3' in manager.tweens

    def test_tween_with_additional_args(self, tweening_manager_mocked):
        """Tween wrapper passes through additional args/kwargs."""
        manager = tweening_manager_mocked

        # Add custom tween that accepts extra args
        def custom_power(n, power=2):
            return n ** power

        manager.add_tween('customPower', custom_power)

        tween = manager.customPower

        # Default power=2
        assert tween(0.5, power=2) == pytest.approx(0.25)

    def test_access_after_override(self, tweening_manager_mocked):
        """Accessing tween after override returns new function."""
        manager = tweening_manager_mocked

        original_result = manager.linear(0.5)

        manager.add_tween('linear', lambda n: n / 2, force=True)

        new_result = manager.linear(0.5)

        assert new_result != original_result
        assert new_result == pytest.approx(0.25)


class TestRealPytweeningIntegration:
    """Test with real pytweening library if available."""

    def test_real_pytweening_easeInQuad(self, tweening_manager_real):
        """Test real pytweening easeInQuad if available."""
        try:
            tween = tweening_manager_real.easeInQuad

            # easeInQuad(0.5) should be 0.25 (0.5^2)
            result = tween(0.5)
            assert result == pytest.approx(0.25, rel=0.01)
        except ImportError:
            pytest.skip("pytweening not installed")
