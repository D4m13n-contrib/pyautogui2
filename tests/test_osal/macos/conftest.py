"""MacOS-specific test configuration.
Loaded automatically when running tests in tests/test_osal/test_macos.

We use `import *` here because:
1. pytest auto-discovers fixtures, we don't need explicit imports in tests
2. __all__ is defined in the source module for documentation
3. This is a pytest convention for conftest.py files
"""

from tests.fixtures.osal.macos.common import *  # noqa: F403, F405
