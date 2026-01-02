"""Tests for LazyImportDescriptor and LazyObjectDescriptor."""

import sys

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from pyautogui2.utils.exceptions import PyAutoGUIException
from pyautogui2.utils.lazy_import import (
    LazyImportDescriptor,
    LazyObjectDescriptor,
    lazy_import,
    lazy_load_object,
)


@contextmanager
def fake_module(module_name: str, mock_obj=None):
    """Context manager to inject fake module into sys.modules.

    Args:
        module_name: Name of the fake module
        mock_obj: Optional MagicMock to use (creates one if None)

    Yields:
        The mock module object

    Cleanup:
        Automatically removes module from sys.modules on exit
    """
    if mock_obj is None:
        mock_obj = MagicMock()
        mock_obj.__name__ = module_name

    original = sys.modules.get(module_name)
    sys.modules[module_name] = mock_obj

    try:
        yield mock_obj
    finally:
        if original is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = original


class TestLazyImportBasic:
    """Test basic lazy import functionality."""

    def test_lazy_import_real_module(self):
        """Lazy import successfully imports real module."""
        class TestClass:
            _json = lazy_import("json")

        obj = TestClass()

        # Module not loaded until accessed
        assert not hasattr(obj, "_lazy_json")

        # Access loads module
        json_module = obj._json

        assert json_module.__name__ == "json"
        assert hasattr(json_module, "dumps")
        assert hasattr(obj, "_lazy_json")  # Cached

    def test_lazy_import_caches_on_instance(self):
        """Lazy import caches module on instance, not descriptor."""
        class TestClass:
            _json = lazy_import("json")

        obj1 = TestClass()
        obj2 = TestClass()

        # Load on obj1
        module1 = obj1._json
        assert hasattr(obj1, "_lazy_json")
        assert not hasattr(obj2, "_lazy_json")

        # Load on obj2
        module2 = obj2._json
        assert hasattr(obj2, "_lazy_json")

        # Both get same module (from sys.modules)
        assert module1 is module2

    def test_lazy_import_repeated_access(self):
        """Repeated access returns cached module."""
        class TestClass:
            _json = lazy_import("json")

        obj = TestClass()

        module1 = obj._json
        module2 = obj._json
        module3 = obj._json

        assert module1 is module2 is module3


class TestLazyImportClassAccess:
    """Test class-level access behavior."""

    def test_class_level_access_returns_module(self):
        """Accessing from class returns fresh module without caching."""
        class TestClass:
            _json = lazy_import("json")

        # Access from class (not instance)
        module = TestClass._json

        assert module.__name__ == "json"

        # No cache on class
        assert not hasattr(TestClass, "_lazy_json")

    def test_class_level_access_always_fresh(self):
        """Class-level access doesn't cache between calls."""
        class TestClass:
            _json = lazy_import("json")

        module1 = TestClass._json
        module2 = TestClass._json

        # Same module from sys.modules
        assert module1 is module2

        # But no cache stored
        assert not hasattr(TestClass, "_lazy_json")


class TestLazyImportErrors:
    """Test error cases and exception handling."""

    def test_import_nonexistent_module_raises_pyautoguiexception(self):
        """Importing nonexistent module raises PyAutoGUIException."""
        class TestClass:
            _fake = lazy_import("nonexistent_module_xyz_12345")

        obj = TestClass()

        with pytest.raises(PyAutoGUIException) as exc_info:
            _ = obj._fake

        assert "nonexistent_module_xyz_12345" in str(exc_info.value)
        assert "not installed" in str(exc_info.value)
        assert "pip install" in str(exc_info.value)

    def test_import_error_preserves_original_exception(self):
        """PyAutoGUIException chains original ImportError."""
        class TestClass:
            _fake = lazy_import("fake_module_does_not_exist")

        obj = TestClass()

        with pytest.raises(PyAutoGUIException) as exc_info:
            _ = obj._fake

        # Check that original exception is chained
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, ImportError)


class TestLazyImportDescriptorProtocol:
    """Test descriptor protocol implementation."""

    def test_set_name_called_automatically(self):
        """__set_name__ is called automatically by Python."""
        class TestClass:
            _json = lazy_import("json")
            _os = lazy_import("os")

        # Descriptors should have correct attr_name set
        json_desc = TestClass.__dict__['_json']
        os_desc = TestClass.__dict__['_os']

        assert json_desc.attr_name == "_lazy_json"
        assert os_desc.attr_name == "_lazy_os"

    def test_cache_attribute_uses_lazy_prefix(self):
        """Cache uses _lazy_ prefix based on descriptor name."""
        class TestClass:
            _json = lazy_import("json")

        obj = TestClass()
        _ = obj._json

        # Cache stored with _lazy_ prefix
        assert hasattr(obj, "_lazy_json")
        assert not hasattr(obj, "json")  # Not without prefix

    def test_manual_override_via_set(self):
        """Can manually override cached module."""
        class TestClass:
            _json = lazy_import("json")

        obj = TestClass()

        # Load real module
        real_json = obj._json
        assert real_json.__name__ == "json"

        # Override with mock
        mock_json = MagicMock()
        obj._json = mock_json

        # Should return mock now
        assert obj._json is mock_json
        assert obj._json is not real_json

    def test_manual_delete_via_delete(self):
        """Can delete cached module."""
        class TestClass:
            _json = lazy_import("json")

        obj = TestClass()

        # Load module
        _ = obj._json
        assert hasattr(obj, "_lazy_json")

        # Delete cache
        del obj._json

        # Cache gone
        assert not hasattr(obj, "_lazy_json")

        # Next access re-imports
        module = obj._json
        assert module.__name__ == "json"
        assert hasattr(obj, "_lazy_json")

    def test_delete_nonexistent_cache_silent(self):
        """Deleting non-existent cache doesn't raise error."""
        class TestClass:
            _json = lazy_import("json")

        obj = TestClass()

        # Never accessed, no cache
        assert not hasattr(obj, "_lazy_json")

        # Delete shouldn't raise
        del obj._json  # Should not raise AttributeError


class TestLazyImportSubmodules:
    """Test importing submodules."""

    def test_submodule_import(self):
        """Can import submodules with dots."""
        class TestClass:
            _urllib_parse = lazy_import("urllib.parse")

        obj = TestClass()
        module = obj._urllib_parse

        assert module.__name__ == "urllib.parse"
        assert hasattr(module, "urlparse")

    def test_nested_submodule_import(self):
        """Can import deeply nested submodules."""
        class TestClass:
            _email_mime_text = lazy_import("email.mime.text")

        obj = TestClass()
        module = obj._email_mime_text

        assert "email.mime.text" in module.__name__

    def test_submodule_attr_name_handles_dots(self):
        """Submodule names with dots get proper cache names."""
        class TestClass:
            _urllib_parse = lazy_import("urllib.parse")

        obj = TestClass()
        _ = obj._urllib_parse

        # Dots in module name should be handled in cache name
        assert hasattr(obj, "_lazy_urllib_parse")


class TestLazyImportSysModules:
    """Test integration with sys.modules."""

    def test_uses_existing_sys_modules_entry(self):
        """Uses existing sys.modules entry if present."""
        with fake_module("fake_existing") as mock_mod:
            class TestClass:
                _fake = lazy_import("fake_existing")

            obj = TestClass()
            loaded = obj._fake

            assert loaded is mock_mod

    def test_respects_sys_modules_for_mocking(self):
        """Respects sys.modules for easy mocking."""
        mock_module = MagicMock()
        mock_module.__name__ = "mock_module"
        mock_module.special_value = 42

        with fake_module("mock_module", mock_module):
            class TestClass:
                _mod = lazy_import("mock_module")

            obj = TestClass()
            loaded = obj._mod

            assert loaded.special_value == 42


class TestLazyObjectBasic:
    """Test basic lazy object creation functionality."""

    def test_lazy_object_creation(self):
        """Lazy object calls factory on first access."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"value": 42}

        class TestClass:
            _config = lazy_load_object("config", factory)

        obj = TestClass()

        # Not created yet
        assert call_count == 0
        assert not hasattr(obj, "_lazy_config")

        # First access creates object
        config = obj._config

        assert call_count == 1
        assert config == {"value": 42}
        assert hasattr(obj, "_lazy_config")

        # Second access uses cache
        config2 = obj._config

        assert call_count == 1  # Not called again
        assert config2 is config

    def test_lazy_object_caches_on_instance(self):
        """Lazy object caches on instance, not descriptor."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        class TestClass:
            _obj = lazy_load_object("obj", factory)

        obj1 = TestClass()
        obj2 = TestClass()

        # Create on obj1
        result1 = obj1._obj
        assert call_count == 1
        assert result1["count"] == 1
        assert hasattr(obj1, "_lazy_obj")
        assert not hasattr(obj2, "_lazy_obj")

        # Create on obj2
        result2 = obj2._obj
        assert call_count == 2
        assert result2["count"] == 2
        assert hasattr(obj2, "_lazy_obj")


class TestLazyObjectClassAccess:
    """Test class-level access behavior for lazy objects."""

    def test_class_level_access_creates_fresh(self):
        """Class-level access creates fresh object without caching."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        class TestClass:
            _obj = lazy_load_object("obj", factory)

        # Access from class
        obj1 = TestClass._obj
        assert call_count == 1
        assert obj1["count"] == 1

        # Access again - creates new
        obj2 = TestClass._obj
        assert call_count == 2
        assert obj2["count"] == 2

        # No cache on class
        assert not hasattr(TestClass, "_lazy_obj")


class TestLazyObjectDescriptorProtocol:
    """Test descriptor protocol for lazy objects."""

    def test_set_name_called_automatically(self):
        """__set_name__ is called automatically."""
        class TestClass:
            _config = lazy_load_object("config", lambda: {})
            _data = lazy_load_object("data", lambda: [])

        config_desc = TestClass.__dict__['_config']
        data_desc = TestClass.__dict__['_data']

        assert config_desc.attr_name == "_lazy_config"
        assert data_desc.attr_name == "_lazy_data"

    def test_manual_override_via_set(self):
        """Can manually override cached object."""
        class TestClass:
            _obj = lazy_load_object("obj", lambda: {"original": True})

        obj = TestClass()

        # Load original
        original = obj._obj
        assert original == {"original": True}

        # Override
        obj._obj = {"overridden": True}

        # Should return override
        assert obj._obj == {"overridden": True}

    def test_manual_delete_via_delete(self):
        """Can delete cached object."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"count": call_count}

        class TestClass:
            _obj = lazy_load_object("obj", factory)

        obj = TestClass()

        # Create
        _ = obj._obj
        assert call_count == 1
        assert hasattr(obj, "_lazy_obj")

        # Delete
        del obj._obj
        assert not hasattr(obj, "_lazy_obj")

        # Re-create
        result = obj._obj
        assert call_count == 2
        assert result["count"] == 2

    def test_delete_nonexistent_cache_silent(self):
        """Deleting non-existent cache doesn't raise error."""
        class TestClass:
            _obj = lazy_load_object("obj", lambda: {})

        obj = TestClass()

        # Never accessed, no cache
        assert not hasattr(obj, "_lazy_obj")

        # Delete shouldn't raise
        del obj._obj  # Should not raise AttributeError


class TestLazyObjectFactoryErrors:
    """Test error handling in factory functions."""

    def test_factory_exception_propagates(self):
        """Exceptions from factory propagate to caller."""
        def failing_factory():
            raise ValueError("Factory failed!")

        class TestClass:
            _obj = lazy_load_object("obj", failing_factory)

        obj = TestClass()

        with pytest.raises(ValueError, match="Factory failed!"):
            _ = obj._obj

    def test_factory_exception_no_cache(self):
        """Failed factory doesn't cache anything."""
        call_count = 0

        def sometimes_fails():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return {"count": call_count}

        class TestClass:
            _obj = lazy_load_object("obj", sometimes_fails)

        obj = TestClass()

        # First call fails
        with pytest.raises(ValueError):
            _ = obj._obj

        # No cache created
        assert not hasattr(obj, "_lazy_obj")

        # Second call succeeds
        result = obj._obj
        assert result["count"] == 2
        assert hasattr(obj, "_lazy_obj")


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_multiple_descriptors_same_class(self):
        """Multiple lazy descriptors in same class work independently."""
        class TestClass:
            _json = lazy_import("json")
            _os = lazy_import("os")
            _config = lazy_load_object("config", lambda: {"key": "value"})

        obj = TestClass()

        # Load all
        json_mod = obj._json
        os_mod = obj._os
        config = obj._config

        # Correct objects loaded
        assert json_mod.__name__ == "json"
        assert os_mod.__name__ == "os"
        assert config == {"key": "value"}

        # Independent caches
        assert hasattr(obj, "_lazy_json")
        assert hasattr(obj, "_lazy_os")
        assert hasattr(obj, "_lazy_config")

    def test_descriptor_with_leading_underscores_stripped(self):
        """Leading underscores properly stripped in cache name."""
        class TestClass:
            _private = lazy_import("json")  # Single underscore
            __protected = lazy_import("os") # Double underscore

        obj = TestClass()

        # Access both
        _ = obj._private
        _ = obj._TestClass__protected

        # Cache names should strip leading underscores
        assert hasattr(obj, "_lazy_private")
        assert hasattr(obj, "_lazy_TestClass__protected")


class TestRealWorldUsage:
    """Test realistic usage patterns."""

    def test_controller_pattern_mixed_descriptors(self):
        """Simulates usage in Controller classes with mixed descriptors."""
        class MockController:
            _json = lazy_import("json")
            _config = lazy_load_object("config", lambda: {"debug": False})

            def serialize(self, data):
                return self._json.dumps(data)

            def get_debug(self):
                return self._config["debug"]

        ctrl = MockController()

        # json not loaded
        assert not hasattr(ctrl, "_lazy_json")

        # config not loaded
        assert not hasattr(ctrl, "_lazy_config")

        # Use json
        result = ctrl.serialize({"test": "value"})
        assert "test" in result
        assert hasattr(ctrl, "_lazy_json")

        # Use config
        debug = ctrl.get_debug()
        assert debug is False
        assert hasattr(ctrl, "_lazy_config")

    def test_conditional_loading_pattern(self):
        """Lazy descriptors enable conditional loading."""
        class ConditionalUser:
            _json = lazy_import("json")
            _xml = lazy_import("xml.etree.ElementTree")

            def export(self, data, format="json"):
                if format == "json":
                    return self._json.dumps(data)
                else:
                    # Simplified XML export
                    return str(data)

        obj = ConditionalUser()

        # Export as JSON
        result = obj.export({"key": "value"}, format="json")
        assert "key" in result
        assert hasattr(obj, "_lazy_json")
        assert not hasattr(obj, "_lazy_xml")  # XML not loaded

    def test_multiple_instances_independent(self):
        """Multiple instances have independent caches."""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"id": call_count}

        class Service:
            _config = lazy_load_object("config", factory)

        s1 = Service()
        s2 = Service()
        s3 = Service()

        # Load only on s2
        config2 = s2._config
        assert call_count == 1
        assert config2["id"] == 1

        assert not hasattr(s1, "_lazy_config")
        assert hasattr(s2, "_lazy_config")
        assert not hasattr(s3, "_lazy_config")

        # Load on s1
        config1 = s1._config
        assert call_count == 2
        assert config1["id"] == 2


class TestDescriptorDefaultAttrName:
    """Test fallback behavior when __set_name__ not called."""

    def test_import_descriptor_default_attr_name(self):
        """LazyImportDescriptor has default attr_name."""
        desc = LazyImportDescriptor("json")

        # Default attr_name set in __init__
        assert desc.attr_name == "_lazy_json"

    def test_object_descriptor_default_attr_name(self):
        """LazyObjectDescriptor has default attr_name."""
        desc = LazyObjectDescriptor("config", lambda: {})

        # Default attr_name set in __init__
        assert desc.attr_name == "_lazy_config"

    def test_module_name_with_dots_in_default(self):
        """Module names with dots handled in default attr_name."""
        desc = LazyImportDescriptor("urllib.parse")

        # Dots replaced with underscores
        assert desc.attr_name == "_lazy_urllib_parse"

