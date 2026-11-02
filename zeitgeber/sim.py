"""Adapter over the Arcascope circadian package (pinned 1.0.3) and phase markers.

Will hold the ClockModel protocol, adapters for Forger99, Jewett99 and Hannay19, a batched
fixed-step RK4 integrate, equilibrate and markers (docs/ARCHITECTURE.md 2.4, docs/SCIENCE.md 1
and 2). This is the only module allowed to import the circadian package.
"""
