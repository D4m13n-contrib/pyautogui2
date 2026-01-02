"""Tests for abstract base classes and decorator system."""

from abc import abstractmethod

import pytest

from pyautogui2.utils.abstract_cls import (
    AbstractController,
    AbstractOSAL,
    _AbstractBase,
    _make_wrapper,
    _merge_doc,
    _normalize_decorator_id,
    _resolve_decorator,
)


class TestNormalizeDecoratorId:
    """Test _normalize_decorator_id function."""

    def test_normalize_string(self):
        """String input returns unchanged."""
        assert _normalize_decorator_id("pause_decorator") == "pause_decorator"

    def test_normalize_function(self):
        """Function input returns __name__."""
        def my_decorator():
            pass

        assert _normalize_decorator_id(my_decorator) == "my_decorator"

    def test_normalize_invalid_type(self):
        """Invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported decorator type"):
            _normalize_decorator_id(123)

        with pytest.raises(TypeError, match="Unsupported decorator type"):
            _normalize_decorator_id([])


class TestResolveDecorator:
    """Test _resolve_decorator function."""

    def test_resolve_function_passthrough(self):
        """Function input returns unchanged."""
        def my_decorator():
            pass

        result = _resolve_decorator(my_decorator)
        assert result is my_decorator

    def test_resolve_string_valid(self):
        """Valid string imports decorator from package."""
        # Should import pause_decorator
        result = _resolve_decorator("pause_decorator")

        assert callable(result)
        assert result.__name__ == "pause_decorator"

    def test_resolve_string_invalid(self):
        """Invalid decorator name raises ImportError."""
        with pytest.raises(ImportError, match="Decorator 'nonexistent_decorator' not found"):
            _resolve_decorator("nonexistent_decorator")

    def test_resolve_invalid_type(self):
        """Invalid type raises TypeError."""
        with pytest.raises(TypeError, match="Unsupported decorator reference"):
            _resolve_decorator(123)


class TestMergeDoc:
    """Test _merge_doc function."""

    def test_merge_both_present(self):
        """Both docs merge with separator."""
        impl = "Implementation doc"
        base = "Base doc"

        result = _merge_doc(impl, base)

        assert result == "Base doc\n---\nImplementation doc"

    def test_merge_only_impl(self):
        """Only impl doc returns impl."""
        result = _merge_doc("Implementation doc", None)
        assert result == "Implementation doc"

    def test_merge_only_base(self):
        """Only base doc returns base."""
        result = _merge_doc(None, "Base doc")
        assert result == "Base doc"

    def test_merge_both_none(self):
        """Both None returns None."""
        result = _merge_doc(None, None)
        assert result is None


class TestMakeWrapper:
    """Test _make_wrapper function."""

    def test_wrapper_preserves_signature(self):
        """Wrapper gets signature from reference function."""
        def ref_func(a: int, b: str = "default") -> str:
            return f"{a}{b}"

        def method(a, b="override"):
            return f"wrapped: {a}{b}"

        wrapper = _make_wrapper(method, ref_func)

        # Check signature preserved
        import inspect
        sig = inspect.signature(wrapper)
        params = list(sig.parameters.keys())

        assert params == ['a', 'b']
        assert sig.parameters['b'].default == "default"

    def test_wrapper_calls_original_method(self):
        """Wrapper calls the original method."""
        def ref_func(x):
            pass

        def method(x):
            return x * 2

        wrapper = _make_wrapper(method, ref_func)

        assert wrapper(5) == 10


class TestAbstractBase:
    """Test _AbstractBase metaclass behavior."""

    def test_abstract_method_gets_decorated(self):
        """Abstract methods get default decorators applied."""
        class MyBase(_AbstractBase):
            @abstractmethod
            def action(self, *_a, **_kw):
                """Base doc."""
                pass

        class MyImpl(MyBase):
            def action(self, *_a, **_kw):
                """Impl doc."""
                return "result"

        obj = MyImpl()
        # Should have decorators applied (pause_decorator by default)
        # Check it's callable and works
        result = obj.action(_pause=False)  # Disable pause for test
        assert result == "result"

    def test_docstring_merging(self):
        """Implementation docstring merges with base."""
        class MyBase(_AbstractBase):
            @abstractmethod
            def action(self):
                """Base documentation."""
                pass

        class MyImpl(MyBase):
            def action(self):
                """Implementation documentation."""
                return "result"

        expected_doc = "Base documentation.\n---\nImplementation documentation."
        assert MyImpl.action.__doc__ == expected_doc

    def test_remove_decorators(self):
        """__abstractmethod_remove_decorators__ removes defaults."""
        class MyBase(_AbstractBase):
            @abstractmethod
            def action(self):
                pass

        class MyImpl(MyBase):
            __abstractmethod_remove_decorators__ = {
                "action": ["pause_decorator"]
            }

            def action(self):
                return "no_pause"

        obj = MyImpl()
        # Without pause_decorator, no _pause kwarg should be handled
        result = obj.action()
        assert result == "no_pause"

    def test_extra_decorators(self):
        """__abstractmethod_decorators__ adds extra decorators."""
        custom_decorator_called = []

        def custom_decorator(func):
            def wrapper(*args, **kwargs):
                custom_decorator_called.append(True)
                return func(*args, **kwargs)
            return wrapper

        class MyBase(_AbstractBase):
            @abstractmethod
            def action(self, *_a, **_kw):
                pass

        class MyImpl(MyBase):
            __abstractmethod_decorators__ = {
                "action": [custom_decorator]
            }

            def action(self, *_a, **_kw):
                return "custom"

        obj = MyImpl()
        obj.action(_pause=False)

        assert len(custom_decorator_called) == 1

    def test_special_methods_no_decorators(self):
        """Special methods (__init__, setup_postinit) don't get decorators."""
        class MyBase(_AbstractBase):
            def __init__(self):
                """Base init doc."""
                self.value = "base"

        class MyImpl(MyBase):
            def __init__(self):
                """Impl init doc."""
                super().__init__()
                self.value = "impl"

        obj = MyImpl()

        # Check docstring merged but no decorators
        assert "Base init doc" in MyImpl.__init__.__doc__
        assert "Impl init doc" in MyImpl.__init__.__doc__
        assert obj.value == "impl"

    def test_for_loop_completes_without_break(self):
        """For loop over MRO completes without break.

        Happens when no base has the method marked as abstract,
        so the loop exhausts the MRO.
        """
        class MyBase(_AbstractBase):
            pass

        class MyImpl(MyBase):
            def action(self):
                """Impl doc."""
                return "result"

        # MRO: MyImpl -> MyBase -> _AbstractBase
        obj = MyImpl()
        assert obj.action() == "result"

    def test_intermediate_base_missing_method(self):
        """Candidate is None for an intermediate base.

        Happens when a class in the MRO doesn't define the method at all.
        """
        class MyBase(_AbstractBase):
            @abstractmethod
            def action(self):
                """Base doc."""

        class Mixin:  # No 'action' method -> candidate will be None
            pass

        class MyImpl(Mixin, MyBase):
            def action(self):
                """Impl doc."""
                return "result"

        # MRO: MyImpl -> Mixin -> MyBase -> _AbstractBase
        # When iterating: Mixin has no 'action' -> candidate is None -> next iteration
        obj = MyImpl()
        assert obj.action() == "result"


class TestAbstractController:
    """Test AbstractController class."""

    def test_can_instantiate(self):
        """Can create AbstractController instance."""
        controller = AbstractController()
        assert isinstance(controller, AbstractController)

    def test_setup_postinit_exists(self):
        """setup_postinit method exists and is callable."""
        controller = AbstractController()

        # Should not raise
        controller.setup_postinit(some_arg="test")

    def test_subclass_behavior(self):
        """Subclass works correctly."""
        class MyController(AbstractController):
            def __init__(self):
                super().__init__()
                self.initialized = True

        controller = MyController()
        assert controller.initialized is True


class TestAbstractOSAL:
    """Test AbstractOSAL class."""

    def test_can_instantiate(self):
        """Can create AbstractOSAL instance."""
        osal = AbstractOSAL()
        assert isinstance(osal, AbstractOSAL)

    def test_setup_postinit_exists(self):
        """setup_postinit method exists and is callable."""
        osal = AbstractOSAL()

        # Should not raise
        osal.setup_postinit(context_key="value")

    def test_subclass_behavior(self):
        """Subclass works correctly."""
        class MyOSAL(AbstractOSAL):
            def __init__(self):
                super().__init__()
                self.initialized = True

        osal = MyOSAL()
        assert osal.initialized is True


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_multiple_inheritance_levels(self):
        """Docstring merging works through multiple levels."""
        class Level1(_AbstractBase):
            @abstractmethod
            def action(self):
                """Level 1 doc."""
                pass

        class Level2(Level1):
            @abstractmethod
            def action(self):
                """Level 2 doc."""
                pass

        class Level3(Level2):
            def action(self):
                """Level 3 doc."""
                return "result"

        # Should merge with immediate parent (Level2)
        doc = Level3.action.__doc__
        assert "Level 2 doc" in doc
        assert "Level 3 doc" in doc

    def test_no_abstract_methods(self):
        """Class with no abstract methods doesn't crash."""
        class NoAbstract(_AbstractBase):
            def regular_method(self):
                return "regular"

        obj = NoAbstract()
        assert obj.regular_method() == "regular"
