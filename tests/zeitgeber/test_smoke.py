"""Smoke test: the package imports and the pinned circadian dependency runs."""

import importlib
from importlib import metadata

import numpy as np

import zeitgeber

MODULES = ["schedule", "grid", "light", "sim", "score", "plan", "output", "settings"]


def test_package_and_dependency_smoke() -> None:
    assert zeitgeber.__version__ == metadata.version("zeitgeber-core")
    for name in MODULES:
        importlib.import_module(f"zeitgeber.{name}")

    assert metadata.version("circadian") == "1.0.3"
    from circadian.models import Forger99

    hours = np.arange(0.0, 24.0, 0.1)
    lux = np.full_like(hours, 100.0)
    trajectory = Forger99().integrate(hours, input=lux)
    assert trajectory.states.shape == (hours.size, 3)
    assert np.all(np.isfinite(trajectory.states))
