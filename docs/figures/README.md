# Figures

## z3_worker_light_3day.png

Lux at the eye for the permanent nights worker from Z3 (`tests/fixtures/schedules/permanent_nights.json`), Monday 16 to Thursday 19 November 2026 in Manila, at the 0.1 h request step. Regenerate with `MPLBACKEND=Agg uv run python scripts/plot_light_profile.py`. The y axis is logarithmic; shaded columns are hours with the sun down.

What it shows:

- Sleep is at 1 lux: Sunday night into Monday until 07:00, then 09:00 to 15:00 after each shift.
- Awake time at home is 100 lux. The 30 minutes before each day sleep are 30 lux (phone in bed).
- The commute to work runs 20:30 to 22:00 after sunset, so all of it is 10 lux.
- Each shift from 22:00 to 07:00 is 500 lux, office light.
- The commute home runs 07:00 to 08:30, after sunrise (about 05:58 in mid November). It holds the two brightest blocks of the day: 20 minutes outdoors at 10,000 lux at each end and 50 minutes in transit at 1,000 lux.

This is the pattern docs/SCIENCE.md section 5 identifies as the main obstacle for night workers: bright light comes right after the shift, which falls after the body clock's low point and pushes the clock earlier. Dark sunglasses (rule R2) scale both commute-home blocks by 0.15 or 0.02.

All constants come from docs/SCIENCE.md 3.5. The placement of outdoor minutes at both ends of the commute and twilight counted as dark are design choices recorded in docs/DECISIONS.md D28.
