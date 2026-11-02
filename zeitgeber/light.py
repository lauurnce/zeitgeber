"""Solar times and the lux profile builder.

Will hold LuxConstants (docs/SCIENCE.md 3.5), solar_times and sun_up (astral, SCIENCE 9),
LightProfile, build_light_profile and build_light_batch (docs/ARCHITECTURE.md 2.3).
Interventions such as sunglasses, light seeking, naps and sleep windows are applied here so the
baseline and every candidate plan come from the same code.
"""
