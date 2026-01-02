"""Tests for pyautogui2.utils.singleton."""
import threading


class TestSingletonBasic:
    """Test basic Singleton behavior."""

    def test_same_instance_returned_on_second_call(self, isolated_singleton):
        """Verify that calling a Singleton class twice returns the same instance."""
        from pyautogui2.utils.singleton import Singleton

        class MyService(metaclass=Singleton):
            pass

        instance_1 = MyService()
        instance_2 = MyService()

        assert instance_1 is instance_2

    def test_different_classes_have_different_instances(self, isolated_singleton):
        """Verify that two different Singleton classes produce independent instances."""
        from pyautogui2.utils.singleton import Singleton

        class ServiceA(metaclass=Singleton):
            pass

        class ServiceB(metaclass=Singleton):
            pass

        assert ServiceA() is not ServiceB()

    def test_instance_stored_by_class_name(self, isolated_singleton):
        """Verify that the instance is stored under the class name key."""
        from pyautogui2.utils.singleton import Singleton

        class MyService(metaclass=Singleton):
            pass

        MyService()

        assert "MyService" in Singleton._instances


class TestSingletonRemoveInstance:
    """Test remove_instance() behavior."""

    def test_remove_existing_instance(self, isolated_singleton):
        """Verify that remove_instance() deletes an existing entry."""
        from pyautogui2.utils.singleton import Singleton

        class MyService(metaclass=Singleton):
            pass

        MyService()
        assert "MyService" in Singleton._instances

        Singleton.remove_instance("MyService")

        assert "MyService" not in Singleton._instances

    def test_remove_nonexistent_instance_does_not_raise(self, isolated_singleton):
        """Verify that remove_instance() is a no-op for unknown names."""
        from pyautogui2.utils.singleton import Singleton

        # Should not raise
        Singleton.remove_instance("DoesNotExist")

    def test_remove_allows_new_instance_creation(self, isolated_singleton):
        """Verify that after removal, a fresh instance can be created."""
        from pyautogui2.utils.singleton import Singleton

        class MyService(metaclass=Singleton):
            pass

        instance_1 = MyService()
        Singleton.remove_instance("MyService")
        instance_2 = MyService()

        assert instance_1 is not instance_2


class TestSingletonThreadSafety:
    """Test thread-safe double-checked locking behavior."""

    def test_concurrent_instantiation_returns_same_instance(self, isolated_singleton):
        """Verify that concurrent calls from multiple threads return the same instance.

        This exercises the RLock path: multiple threads reach the first check
        simultaneously, only one creates the instance, the others reuse it.
        """
        from pyautogui2.utils.singleton import Singleton

        class MyService(metaclass=Singleton):
            pass

        results: list[MyService] = []
        barrier = threading.Barrier(10)  # Synchronize all threads at the same point

        def create_instance():
            barrier.wait()  # All threads start at the same time
            results.append(MyService())

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(instance is results[0] for instance in results)

    def test_second_check_skipped_when_instance_already_present(self, isolated_singleton):
        """Cover the second check evaluates to False.

        Simulates the race condition where another thread creates the instance
        between the first check (outside lock) and the second check (inside lock).
        """
        from unittest.mock import patch

        from pyautogui2.utils.singleton import Singleton

        class MyService(metaclass=Singleton):
            pass

        sentinel = MyService.__new__(MyService)

        class InjectingLock:
            """Injects the instance into _instances when the lock is acquired,
            simulating another thread that created the instance just before us.
            """

            def __enter__(self):
                # Simulate: another thread created the instance between the two checks
                Singleton._instances["MyService"] = sentinel
                return self

            def __exit__(self, *args):
                pass

        with patch.object(Singleton, "_lock", InjectingLock()):
            result = MyService()

        assert result is sentinel
