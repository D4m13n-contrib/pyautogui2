"""Controller-specific fixtures.
Loaded automatically when running tests in tests/test_controllers.
"""

pytest_plugins = [
    "tests.fixtures.controller.manager",
    "tests.fixtures.controller.pointer",
    "tests.fixtures.controller.keyboard",
    "tests.fixtures.controller.screen",
    "tests.fixtures.controller.dialogs",
]
