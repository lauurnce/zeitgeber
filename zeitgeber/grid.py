"""Uniform time grid shared by the light builder and the simulator.

Will hold TimeGrid (docs/ARCHITECTURE.md 2.2): a UTC start, a step in hours (0.1 for requests,
1/60 in tests) and a length. Light arrays, trajectories and markers carry their grid so arrays
from different grids cannot be mixed.
"""
