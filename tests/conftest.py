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
