"""Schedule input models and validation.

Will hold Location, Shift, Commute, SleepHabits, RestDayPolicy, Schedule and Interval
(docs/ARCHITECTURE.md 2.1). ``Schedule.materialize`` is the only place where local wall-clock
times become timezone-aware UTC intervals, so shifts that cross midnight are handled once.
"""
