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

## prc.png

Simulated phase response curves to bright light for Forger99 (the default model), Hannay19 (the cross-check) and Jewett99. Regenerate with `MPLBACKEND=Agg uv run python scripts/reproduce_prc.py`, which also prints the numbers as a table.

Protocol (`zeitgeber/prc.py`, docs/SCIENCE.md 4.3): each model is entrained on 16 h at 150 lux and 8 h dark, then runs the Khalsa 2003 sequence as the circadian package encodes it: a constant routine in 15 lux, 8 h dark, 16 h awake in 15 lux with the pulse centered in the middle, 8 h dark, then 15 lux. The length of the first constant routine moves the pulse through 48 phases. Each pulsed run has a control run without the pulse, and the shift is the difference between their final CBTmin times, so drift in dim light cancels. The x axis is the pulse center minus the control run's nearest CBTmin; advances are positive.

What it shows:

- Left, 6.7 h at 9,985 lux (Khalsa 2003): every model delays when the pulse is centered before CBTmin and advances after it, crossing zero within 0.5 h of CBTmin (Forger99 +0.22 h, Hannay19 -0.36 h, Jewett99 -0.48 h). The shaded band is the 1.5 h tolerance of feature F2.
- The curves are smaller than the published curve: peak to trough is 3.60 h (Forger99), 4.42 h (Hannay19) and 3.41 h (Jewett99) against 5.02 h published. Jewett99 sits just outside the 1.5 h tolerance of F3.
- Right, 1 h at 7,997 lux (St Hilaire 2012): the same shape at about a third of the size, 1.11 to 1.66 h peak to trough against 2.20 h published. Forger99 and Jewett99 fall just under the 1.0 h tolerance of F4.
- Hannay19 keeps advancing for longer after CBTmin than the other two models.

F3 and F4 are reported, not blocking (docs/SCIENCE.md 4.3); step Z8 runs the full feature set.

## planner-390.png, planner-1440.png

The planner page (`/plan`) after a plan has loaded, at 390 px and 1440 px wide, with the default 10 PM to 7 AM week, day sleep 9 AM to 3 PM and the plan starting Monday 16 November 2026. Regenerate with `pnpm -C web exec playwright test e2e/screens.spec.ts` (starts the API and a production build).

## landing-390.jpg, landing-1440.jpg

The landing page (`/`) in the default dark theme with reduced motion, so the live preview shows its first frame. Regenerate with `pnpm -C web exec playwright test e2e/landing.spec.ts`, or against the deployed site with `E2E_BASE_URL=https://zeitgeber-web.vercel.app`. JPEG at quality 70 to stay under the repository's 500 KB file limit.
