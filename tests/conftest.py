"""Shared pytest setup.

The circadian package imports matplotlib at load time. A non-interactive backend keeps tests
headless on CI and on servers.
"""

import os

os.environ.setdefault("MPLBACKEND", "Agg")


def pytest_collection_modifyitems(config, items):  # type: ignore[no-untyped-def]
    """Runtime budget checks (marker ``perf``) run only with ZEITGEBER_PERF=1."""
    import pytest

    if os.environ.get("ZEITGEBER_PERF") == "1":
        return
    skip = pytest.mark.skip(reason="runtime budget check; set ZEITGEBER_PERF=1 to run")
    for item in items:
        if "perf" in item.keywords:
            item.add_marker(skip)
