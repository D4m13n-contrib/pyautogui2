"""Tests for LogScreenshotManager and @log_screenshot decorator."""

import pathlib

from collections import deque
from unittest.mock import MagicMock, patch

import pytest

from pyautogui2.utils.decorators.log_screenshot import LogScreenshotManager, log_screenshot


class TestManagerInitialization:
    """Test LogScreenshotManager singleton and initialization."""

    def test_singleton_same_instance(self, log_screenshot_manager_mocked):
        """Multiple instantiations return same singleton object."""
        mgr1 = log_screenshot_manager_mocked
        mgr2 = LogScreenshotManager()

        assert mgr1 is mgr2

    def test_initial_state_from_settings(self, log_screenshot_manager_mocked, isolated_settings):
        """Manager initializes with LOG_SCREENSHOTS setting value."""
        isolated_settings.LOG_SCREENSHOTS = True
        log_screenshot_manager_mocked.reset_to_defaults()

        assert log_screenshot_manager_mocked._enabled is None
        assert log_screenshot_manager_mocked.enabled is True

        isolated_settings.LOG_SCREENSHOTS = False
        log_screenshot_manager_mocked.reset_to_defaults()

        assert log_screenshot_manager_mocked._enabled is None
        assert log_screenshot_manager_mocked.enabled is False

    def test_reset_clears_screenshot_func(self, log_screenshot_manager_mocked):
        """reset_to_defaults() clears screenshot function."""
        log_screenshot_manager_mocked.set_screenshot_func(MagicMock())
        assert log_screenshot_manager_mocked._screenshot_func is not None

        log_screenshot_manager_mocked.reset_to_defaults()

        assert log_screenshot_manager_mocked._screenshot_func is None

    def test_reset_clears_filename_queue(self, log_screenshot_manager_mocked):
        """reset_to_defaults() creates fresh empty deque."""
        log_screenshot_manager_mocked._screenshot_filenames = deque([pathlib.Path("fake.png")])

        log_screenshot_manager_mocked.reset_to_defaults()

        assert log_screenshot_manager_mocked._screenshot_filenames == deque([])
        assert len(log_screenshot_manager_mocked._screenshot_filenames) == 0


class TestScreenshotFunctionManagement:
    """Test set_screenshot_func and function registration."""

    def test_set_screenshot_func_stores_callable(self, log_screenshot_manager_mocked):
        """set_screenshot_func() registers the provided function."""
        mock_screenshot_func = MagicMock()
        log_screenshot_manager_mocked.set_screenshot_func(mock_screenshot_func)

        assert log_screenshot_manager_mocked._screenshot_func is mock_screenshot_func

    def test_set_screenshot_func_replaces_previous(self, log_screenshot_manager_mocked):
        """Subsequent calls replace previous function."""
        func1 = MagicMock()
        func2 = MagicMock()

        log_screenshot_manager_mocked.set_screenshot_func(func1)
        assert log_screenshot_manager_mocked._screenshot_func is func1

        log_screenshot_manager_mocked.set_screenshot_func(func2)
        assert log_screenshot_manager_mocked._screenshot_func is func2


class TestLogScreenshotBasic:
    """Test log_screenshot() core functionality."""

    def test_skips_when_disabled(self, log_screenshot_manager_mocked):
        """No screenshot when enabled=False and no override."""
        log_screenshot_manager_mocked.enabled = False

        def dummy_func():
            pass

        log_screenshot_manager_mocked.log_screenshot(dummy_func, 100, 200)

        log_screenshot_manager_mocked._screenshot_func.assert_not_called()

    def test_skips_with_explicit_false_kwarg(self, log_screenshot_manager_mocked):
        """_log_screenshot=False prevents capture even when enabled."""
        log_screenshot_manager_mocked.enabled = True

        def dummy_func():
            pass

        log_screenshot_manager_mocked.log_screenshot(dummy_func, _log_screenshot=False)

        log_screenshot_manager_mocked._screenshot_func.assert_not_called()

    def test_logs_error_when_no_screenshot_func(self, log_screenshot_manager_mocked, caplog):
        """Logs error and returns early if screenshot function not set."""
        log_screenshot_manager_mocked.set_screenshot_func(None)
        log_screenshot_manager_mocked.enabled = True

        def dummy_func():
            pass

        with caplog.at_level("ERROR"):
            log_screenshot_manager_mocked.log_screenshot(dummy_func)

        assert "No screenshot function set" in caplog.text

    def test_captures_when_enabled(self, log_screenshot_manager_mocked):
        """Screenshot captured when _enabled=True."""
        log_screenshot_manager_mocked.enabled = True

        def dummy_func():
            pass

        log_screenshot_manager_mocked.log_screenshot(dummy_func)

        log_screenshot_manager_mocked._screenshot_func.assert_called_once()
        # Verify filepath argument contains function name
        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        assert "dummy_func" in call_args

    def test_explicit_true_overrides_disabled(self, log_screenshot_manager_mocked):
        """_log_screenshot=True forces capture when globally disabled."""
        log_screenshot_manager_mocked.enabled = False

        def dummy_func():
            pass

        log_screenshot_manager_mocked.log_screenshot(dummy_func, _log_screenshot=True)

        log_screenshot_manager_mocked._screenshot_func.assert_called_once()


class TestFilenameGeneration:
    """Test filename format and argument truncation."""

    def test_filename_contains_timestamp(self, log_screenshot_manager_mocked):
        """Filename includes date and time with milliseconds."""
        log_screenshot_manager_mocked.enabled = True

        def test_action():
            pass

        with patch("datetime.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.year = 2026
            mock_now.month = 3
            mock_now.day = 15
            mock_now.hour = 14
            mock_now.minute = 30
            mock_now.second = 45
            mock_now.microsecond = 123456  # First 3 digits = 123
            mock_dt.now.return_value = mock_now

            log_screenshot_manager_mocked.log_screenshot(test_action)

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        assert "2026-03-15_14-30-45-123" in call_args

    def test_filename_contains_function_name(self, log_screenshot_manager_mocked):
        """Filename includes decorated function name."""
        log_screenshot_manager_mocked.enabled = True

        def my_custom_action():
            pass

        log_screenshot_manager_mocked.log_screenshot(my_custom_action)

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        assert "my_custom_action" in call_args

    def test_filename_includes_args(self, log_screenshot_manager_mocked):
        """Positional arguments appear in filename."""
        log_screenshot_manager_mocked.enabled = True

        def click():
            pass

        log_screenshot_manager_mocked.log_screenshot(click, 100, 200)

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        assert "100,200" in call_args

    def test_filename_includes_kwargs(self, log_screenshot_manager_mocked):
        """Keyword arguments appear in filename (excluding _log_screenshot)."""
        log_screenshot_manager_mocked.enabled = True

        def press():
            pass

        log_screenshot_manager_mocked.log_screenshot(press, button=1, duration=0.5)

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        # Should contain "press_button:1,duration:0.5" (or truncated version)
        assert "press" in call_args
        assert "button:1" in call_args or "butt" in call_args

    def test_args_truncated_to_12_chars(self, log_screenshot_manager_mocked):
        """Long argument strings truncated to prevent huge filenames."""
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Args that would create >12 char string
        log_screenshot_manager_mocked.log_screenshot(action, "very_long_argument", extra="more_data")

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        # Extract args portion between function name and .png
        # Format: ..._funcname_ARGS.png
        args_part = call_args.split("_action_")[1].replace(".png", "")

        assert len(args_part) <= 24

    def test_empty_args_handled(self, log_screenshot_manager_mocked):
        """No arguments creates filename without args section."""
        log_screenshot_manager_mocked.enabled = True

        def simple_action():
            pass

        log_screenshot_manager_mocked.log_screenshot(simple_action)

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        # Should end with funcname_.png (empty args)
        assert "simple_action_.png" in call_args


class TestFolderCreation:
    """Test automatic screenshot folder creation."""

    def test_creates_folder_if_missing(self, log_screenshot_manager_mocked):
        """LOG_SCREENSHOTS_FOLDER created if doesn't exist."""
        # Ensure folder doesn't exist
        temp_screenshot_folder = log_screenshot_manager_mocked._mocks["log_screenshots_path"]
        assert not temp_screenshot_folder.exists()

        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        log_screenshot_manager_mocked.log_screenshot(action)

        assert temp_screenshot_folder.exists()
        assert temp_screenshot_folder.is_dir()

    def test_reuses_existing_folder(self, log_screenshot_manager_mocked):
        """Existing folder reused without error."""
        temp_screenshot_folder = log_screenshot_manager_mocked._mocks["log_screenshots_path"]
        temp_screenshot_folder.mkdir(parents=True)

        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Should not raise
        log_screenshot_manager_mocked.log_screenshot(action)


class TestRetentionLimits:
    """Test automatic old file deletion when limit reached."""

    def test_no_deletion_when_limit_none(self, log_screenshot_manager_mocked, isolated_settings):
        """Files never deleted if LOG_SCREENSHOTS_LIMIT=None."""
        isolated_settings.LOG_SCREENSHOTS_LIMIT = None

        log_screenshot_manager_mocked.reset_to_defaults()
        log_screenshot_manager_mocked.set_screenshot_func(MagicMock())
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Call multiple times
        for _ in range(5):
            log_screenshot_manager_mocked.log_screenshot(action)

        # Queue should be empty (not tracking files)
        assert len(log_screenshot_manager_mocked._screenshot_filenames) == 0

    def test_files_tracked_when_limit_set(self, log_screenshot_manager_mocked, isolated_settings):
        """Filenames added to queue when limit configured."""
        isolated_settings.LOG_SCREENSHOTS_LIMIT = 10

        log_screenshot_manager_mocked.reset_to_defaults()
        log_screenshot_manager_mocked.set_screenshot_func(MagicMock())
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        log_screenshot_manager_mocked.log_screenshot(action, "test")

        assert len(log_screenshot_manager_mocked._screenshot_filenames) == 1
        assert isinstance(log_screenshot_manager_mocked._screenshot_filenames[0], pathlib.Path)

    def test_oldest_file_deleted_when_limit_reached(self, log_screenshot_manager_mocked, isolated_settings):
        """Oldest screenshot deleted when count >= limit."""
        isolated_settings.LOG_SCREENSHOTS_LIMIT = 3
        log_screenshot_manager_mocked.reset_to_defaults()

        # Use real file creation to test deletion
        created_files = []

        def real_screenshot(filepath):
            path = pathlib.Path(filepath)
            path.write_text("fake screenshot")
            created_files.append(path)

        log_screenshot_manager_mocked.set_screenshot_func(real_screenshot)
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Create 3 files (at limit)
        for i in range(3):
            log_screenshot_manager_mocked.log_screenshot(action, i)

        assert len(created_files) == 3
        assert all(f.exists() for f in created_files)

        # 4th file should trigger deletion of oldest (first)
        log_screenshot_manager_mocked.log_screenshot(action, 3)

        assert len(created_files) == 4
        # First file should be deleted
        assert not created_files[0].exists()
        # Others should remain
        assert all(f.exists() for f in created_files[1:])

    def test_fifo_order_maintained(self, log_screenshot_manager_mocked, isolated_settings):
        """Newest files at front, oldest at back of deque."""
        isolated_settings.LOG_SCREENSHOTS_LIMIT = 5
        log_screenshot_manager_mocked.reset_to_defaults()

        created_files = []

        def track_screenshot(filepath):
            created_files.append(pathlib.Path(filepath))

        log_screenshot_manager_mocked.set_screenshot_func(track_screenshot)
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        for i in range(3):
            log_screenshot_manager_mocked.log_screenshot(action, i)

        # Queue should be [file2, file1, file0] (newest first)
        assert log_screenshot_manager_mocked._screenshot_filenames[0] == created_files[2]
        assert log_screenshot_manager_mocked._screenshot_filenames[-1] == created_files[0]


class TestLogScreenshotDecorator:
    """Test @log_screenshot decorator integration."""

    def test_decorator_calls_log_screenshot_manager_mocked(self, log_screenshot_manager_mocked):
        """Decorator invokes LogScreenshotManager.log_screenshot()."""
        log_screenshot_manager_mocked.enabled = True

        @log_screenshot
        def my_action(self, x, y):
            return x + y

        class DummyController:
            pass

        obj = DummyController()
        result = my_action(obj, 10, 20)

        # Decorator should call log_screenshot_manager_mocked
        log_screenshot_manager_mocked._screenshot_func.assert_called_once()
        # Original function should execute
        assert result == 30

    def test_decorator_preserves_function_signature(self):
        """Decorated function retains original name and docstring."""
        @log_screenshot
        def test_func(self, arg1, arg2):
            """Test docstring."""
            pass

        assert test_func.__name__ == "test_func"
        assert test_func.__doc__ == "Test docstring."

    def test_decorator_passes_args_to_log_screenshot_manager_mocked(self, log_screenshot_manager_mocked):
        """Decorator forwards positional and keyword args to log_screenshot_manager_mocked."""
        log_screenshot_manager_mocked.enabled = True

        @log_screenshot
        def click_action(self, x, y, button=1):
            pass

        class DummyController:
            pass

        obj = DummyController()
        click_action(obj, 100, 200, button=2)

        # Check log_screenshot_manager_mocked received correct args
        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        assert "100,200" in call_args
        assert "button:2" in call_args or "butt" in call_args   # Can be truncated

    def test_decorator_respects_log_screenshot_kwarg(self, log_screenshot_manager_mocked):
        """_log_screenshot kwarg controls decorator behavior."""
        log_screenshot_manager_mocked.enabled = True

        @log_screenshot
        def action(self, value, *_a, **_kw):
            pass

        class DummyController:
            pass

        obj = DummyController()

        # Should capture (enabled globally)
        action(obj, 1)
        assert log_screenshot_manager_mocked._screenshot_func.call_count == 1

        # Should skip (explicit False)
        action(obj, 2, _log_screenshot=False)
        assert log_screenshot_manager_mocked._screenshot_func.call_count == 1  # Still 1

    def test_decorator_with_exception_in_function(self, log_screenshot_manager_mocked):
        """Screenshot captured even if decorated function raises."""
        log_screenshot_manager_mocked.enabled = True

        @log_screenshot
        def failing_action(self):
            raise ValueError("Test error")

        class DummyController:
            pass

        obj = DummyController()

        with pytest.raises(ValueError, match="Test error"):
            failing_action(obj)

        # Screenshot should still have been taken
        log_screenshot_manager_mocked._screenshot_func.assert_called_once()


class TestEdgeCases:
    """Test unusual inputs and error conditions."""

    def test_log_screenshot_with_none_args(self, log_screenshot_manager_mocked):
        """None values in args handled gracefully."""
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        log_screenshot_manager_mocked.log_screenshot(action, None, None)

        call_args = log_screenshot_manager_mocked._screenshot_func.call_args[0][0]
        assert "None,None" in call_args

    def test_log_screenshot_enabled_not_bool_raise(self, log_screenshot_manager_mocked):
        """Not bool values for enabled should raise TypeError."""
        with pytest.raises(TypeError, match="Enabled must be boolean"):
            log_screenshot_manager_mocked.enabled = "Not boolean"

        with pytest.raises(TypeError, match="Enabled must be boolean"):
            log_screenshot_manager_mocked.enabled = 0.0

        with pytest.raises(TypeError, match="Enabled must be boolean"):
            log_screenshot_manager_mocked.enabled = 42

    def test_log_screenshot_with_unicode_args(self, log_screenshot_manager_mocked):
        """Unicode characters in args don't break filename."""
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Should not raise
        log_screenshot_manager_mocked.log_screenshot(action, "hello", emoji="🎉")

        log_screenshot_manager_mocked._screenshot_func.assert_called_once()

    def test_handles_filename_collisions(self, log_screenshot_manager_mocked, isolated_settings):
        """Appends counter suffix when filename already exists.

        Tests collision handling for rapid-fire screenshots in same millisecond.
        Ensures no file overwrites another.
        """
        isolated_settings.LOG_SCREENSHOTS_LIMIT = None
        log_screenshot_manager_mocked.reset_to_defaults()

        files_created = []

        def create_real_file(filepath):
            """Create actual file to trigger collision detection."""
            path = pathlib.Path(filepath)
            path.write_text(f"screenshot {len(files_created)}")
            files_created.append(path)

        log_screenshot_manager_mocked.set_screenshot_func(create_real_file)
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Mock datetime to freeze timestamp (force collisions)
        with patch("datetime.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.year = 2026
            mock_now.month = 1
            mock_now.day = 2
            mock_now.hour = 11
            mock_now.minute = 22
            mock_now.second = 33
            mock_now.microsecond = 444000   # 444ms
            mock_dt.now.return_value = mock_now

            # Create 5 screenshots with identical timestamp
            for _ in range(5):
                log_screenshot_manager_mocked.log_screenshot(action, 100, 200)

        # Verify all files created with unique names
        assert len(files_created) == 5
        assert len(set(files_created)) == 5  # All unique

        # Verify filenames follow pattern
        filenames = [f.name for f in files_created]
        assert "2026-01-02_11-22-33-444_action_100,200.png" in filenames
        assert "2026-01-02_11-22-33-444_action_100,200_1.png" in filenames
        assert "2026-01-02_11-22-33-444_action_100,200_2.png" in filenames
        assert "2026-01-02_11-22-33-444_action_100,200_3.png" in filenames
        assert "2026-01-02_11-22-33-444_action_100,200_4.png" in filenames

        # Verify all files exist on disk
        assert all(f.exists() for f in files_created)

    def test_collision_counter_safety_limit(self, log_screenshot_manager_mocked, isolated_settings, caplog):
        """Logs error and aborts after 10000 collision attempts.

        Prevents infinite loop if filesystem is corrupted or inaccessible.
        """

        def always_exists_mock(filepath):
            """Simulate filesystem where all files mysteriously exist."""
            pass

        log_screenshot_manager_mocked.set_screenshot_func(always_exists_mock)
        log_screenshot_manager_mocked.enabled = True

        # Pre-create files to simulate extreme collision scenario
        folder = pathlib.Path(isolated_settings.LOG_SCREENSHOTS_FOLDER)
        folder.mkdir(parents=True, exist_ok=True)

        # Mock Path.exists to always return True
        with patch("pathlib.Path.exists", return_value=True), caplog.at_level("ERROR"):
            def action():
                pass

            log_screenshot_manager_mocked.log_screenshot(action)

        # Should log error about failing to generate unique name
        assert "Failed to generate unique filename after 10000 attempts" in caplog.text

    def test_rapid_sequential_calls_create_unique_files(self, log_screenshot_manager_mocked):
        """Rapid calls create unique files even if timestamps collide.

        Replaces flaky timing-dependent test with deterministic collision test.
        """
        files_created = []

        def track_file(filepath):
            # Create real file to enable collision detection
            path = pathlib.Path(filepath)
            path.write_text("fake")
            files_created.append(path)

        log_screenshot_manager_mocked.set_screenshot_func(track_file)
        log_screenshot_manager_mocked.enabled = True

        def action():
            pass

        # Freeze time to guarantee collisions
        with patch("datetime.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.year = 2026
            mock_now.month = 3
            mock_now.day = 15
            mock_now.hour = 10
            mock_now.minute = 20
            mock_now.second = 30
            mock_now.microsecond = 500000  # 500ms
            mock_dt.now.return_value = mock_now

            # All calls get same timestamp
            for _ in range(3):
                log_screenshot_manager_mocked.log_screenshot(action, 0)

        # All files should exist with unique names
        assert len(files_created) == 3
        assert all(f.exists() for f in files_created)

        filenames = [f.name for f in files_created]
        # First has no suffix
        assert any("_action_0.png" in name and "_0_" not in name for name in filenames)
        # Others have _1, _2 suffixes
        assert any("_action_0_1.png" in name for name in filenames)
        assert any("_action_0_2.png" in name for name in filenames)
