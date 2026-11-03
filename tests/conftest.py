"""Shared pytest setup.

The circadian package imports matplotlib at load time. A non-interactive backend keeps tests
headless on CI and on servers.
"""

import os

os.environ.setdefault("MPLBACKEND", "Agg")
