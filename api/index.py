"""Vercel Python function entry point: the same ASGI app as api.main.

matplotlib (imported by the circadian package) needs a writable config directory and a
headless backend inside the function.
"""

import os

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

from api.main import app

__all__ = ["app"]
