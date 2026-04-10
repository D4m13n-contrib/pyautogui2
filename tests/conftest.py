"""Root pytest configuration - ensures src/ is visible AND loads global fixtures."""

import pytest


# Load common fixtures from tests/fixtures/
pytest_plugins = [
    "tests.fixtures.common",
    "tests.fixtures.core",
    "tests.fixtures.lib",
]

def pytest_collection_modifyitems(items):
    """Automatically mark all tests named 'test_*_real.py' as 'real'."""
    for item in items:
        if item.location[0].endswith("_real.py"):
            item.add_marker(pytest.mark.real)

def pytest_configure(config: pytest.Config) -> None:
    """Prevent pytest-retry from crashing under execnet/SSH (--tx ssh=...).

    With --tx, xdist workers have workerinput but pytest-retry never starts
    its ReportServer (which only runs when -n/numprocesses is used). The
    worker then crashes with KeyError on server_port.

    Fix: inject a fake server_port and replace ClientReporter with a no-op
    before pytest-retry's pytest_configure runs. Retry still works — only
    the inter-process result reporting to the controller is skipped.
    """
    if not hasattr(config, "workerinput"):
        return
    if "server_port" in config.workerinput:
        return

    # Inject a dummy port so pytest-retry does not raise KeyError
    config.workerinput["server_port"] = 0

    # Patch ClientReporter before pytest-retry uses it
    try:
        import pytest_retry.retry_plugin as _retry_plugin

        class _NoOpReporter:
            def __init__(self, port: int) -> None:
                pass

        _retry_plugin.ClientReporter = _NoOpReporter  # type: ignore[attr-defined]
    except (ImportError, AttributeError):
        pass

# ==== Debug =====
# Uncomment belows to show fixtures time duration

#import time
#@pytest.hookimpl(hookwrapper=True)
#def pytest_fixture_setup(fixturedef, request):
#    start = time.perf_counter()
#    yield
#    duration = time.perf_counter() - start
#    if duration > 0.05:
#        print(f"\n  ⏱ {fixturedef.argname}: {duration:.3f}s")
