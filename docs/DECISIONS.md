# Decision log

Format: date, decision, reason, alternatives considered. Newest entries at the bottom.

## 2026-11-09

### D1. Planning target is the compromise phase position
Decision: plan so that the core body temperature minimum falls inside the sleep window on workdays and inside the late part of the sleep window on rest days, rather than fully adapting the clock to nights.
Reason: full adaptation is undone by every rest day spent on a day schedule. The compromise position improved mood, fatigue and performance in permanent night workers while keeping normal social hours on days off (Smith, Fogg and Eastman, 2009; full citation to follow in docs/SCIENCE.md).
Alternatives: full re-entrainment to nights; no phase target, only sleep hygiene rules.

### D2. Forger99 is the primary model, Hannay19 runs alongside
Decision: Forger99 drives the plan. Hannay19 runs on the same light profile to estimate dim-light melatonin onset and to cross-check phase. When the two disagree, the plan shows a range.
Reason: Forger99 is the most widely used light-driven model and the default in the circadian package. Hannay19 was fit to larger datasets and gives a melatonin-based marker.
Alternatives: Jewett99 as primary; Hannay19 alone; a single model with no cross-check.

### D3. The API runs as a Vercel Python function in the same project
Decision: deploy the FastAPI app as a Python function in the same Vercel project as the web app.
Reason: one deploy, one domain, no extra hosting account. Vercel supports Python 3.12 and large function bundles.
Alternatives: a container on Fly.io or Render; a separate repository for the API.
Fallback: move to a small container host if cold starts or SciPy bundle size cause problems.

### D4. One repository with three parts
Decision: zeitgeber/ (Python package), api/ (FastAPI) and web/ (Next.js App Router, TypeScript, Tailwind) live in one repository.
Reason: the science engine, API and web change together in v0.1, and one history is easier to review.
Alternatives: separate repositories; a monorepo tool such as Turborepo.

### D5. Science core before web
Decision: build and test the package (schedule model, light profile, model adapter, phase markers, phase response curve reproduction) before any API or web work.
Reason: the web planner is only as good as the engine, and the phase response curve test is the first success criterion.
Alternatives: a web demo first with a mocked engine.

### D6. License is MIT
Decision: MIT, copyright 2026 Lawrence Panes.
Reason: permissive and compatible with the circadian package. That package's repository LICENSE file is MIT; its PyPI metadata lists Apache 2.0. Both are permissive and compatible with MIT use with attribution.
Alternatives: Apache 2.0; AGPL.

### D7. Distribution name zeitgeber-core
Decision: the import name is zeitgeber; the pyproject distribution name is zeitgeber-core. No PyPI release in v0.1.
Reason: the PyPI name zeitgeber is taken.
Alternatives: rename the package; publish under another name early.

### D8. Language-model wording is off by default
Decision: nudges are templates. An optional setting enables rephrasing by a language model; the provider is a setting and anthropic is wired first. A validator rejects output that adds any number, time, duration or claim not in the plan, or that uses a banned term, and falls back to the template.
Reason: the plan must stay explainable and free of unsupported claims.
Alternatives: wording always on; templates only with no option.

### D9. Weekly repeating schedule only
Decision: v0.1 models a weekly pattern of shift start and end per weekday plus rest days.
Reason: this covers most BPO schedules and keeps the data model small.
Alternatives: arbitrary rotation calendars; a date-by-date editor.

### D10. Stateless API, no request logging
Decision: no database, no cookies holding schedule data, no analytics on planner inputs, no request-body logging. Language-model wording receives template text only, never the raw schedule.
Reason: the privacy promise is "processed per request and not stored", and that must also hold for logs and third parties.
Alternatives: optional saved plans with accounts (out of scope for v0.1).

### D11. Default location and time handling
Decision: Metro Manila is the default location. The API accepts any latitude and longitude; the web UI lists Philippine cities. Display time zone is Asia/Manila; internal times are UTC and timezone-aware.
Reason: the primary users are in the Philippines, which has no daylight saving time.
Alternatives: free-text location with geocoding.

## 2026-11-09, science specification

### D12. Forger99 is the default model; CBTmin and DLMO follow the package conventions
Decision: Forger99 drives the plan with the package's default parameters. CBTmin is the minimum of x for Forger99, the minimum of x plus 0.8 h for Jewett99, and the phase pi for Hannay19. DLMO is CBTmin minus 7 h in all three. Hannay19 runs alongside; a disagreement above 1 h on CBTmin is shown as a range.
Reason: fewest parameters, validated on PRC and amplitude experiments in the original paper, and the package's PRC tooling was built around it (docs/SCIENCE.md 1.9). The 7 h interval matches the estimate the Eastman laboratory uses.
Alternatives: Jewett99 as default; Hannay19 as default; an independent DLMO model.

### D13. Pin circadian 1.0.3 behind an adapter and carry both license notices
Decision: depend on circadian==1.0.3 with a lock hash. Only one adapter module imports it. Third-party notices reproduce the MIT text from the sdist LICENSE file and state that the package metadata declares Apache 2.0. Zeitgeber does not use the package's ShiftWork helper; it builds its own light profile and wraps it in LightSchedule.
Reason: the release contradicts itself on license (docs/SCIENCE.md 2.3); both options are permissive. The adapter isolates a thinly maintained dependency with no Python 3.11 or later in its classifiers. ShiftWork embeds sleep assumptions that do not fit a weekly schedule with commutes.
Alternatives: vendor the equations now; implement the models from scratch; use ShiftWork.
Open question: ask the maintainers to reconcile the license fields.

### D14. Light constants for v0.1 and no modeling of blue-blocking lenses
Decision: use the constants in docs/SCIENCE.md 3.5 (outdoor 10,000 lux capped at the model saturation level, shade or vehicle 1,000, office 500, home 100, phone in a dark room 30, sleep 1, night street 10), sunglasses as a transmission factor of 0.15 or 0.02, and treat blue-blocking lenses as out of scope for the model.
Reason: the models take photopic lux and cannot represent spectral filtering; orange lenses pass the same lux while blocking most of the circadian effect. The constants sit on cited measurements where they exist and are marked UNVERIFIED where they do not.
Alternatives: melanopic conversion factors per source; include blue-blockers as a fixed lux reduction.

### D15. Phase response test features and tolerances
Decision: adopt the nine features F1 to F9 in docs/SCIENCE.md 4.3 as pytest cases. F1 (sign of shift) and F2 (crossover within 1.5 h of CBTmin) block the use of a model; the rest report measured values.
Reason: they encode the published PRC shape and amplitude from Khalsa 2003 and St Hilaire 2012, the evening-light delay from Burke 2015, the intrinsic period from Czeisler 1999 and the entrained phase angle, which together cover the first success criterion.
Alternatives: compare only the sign of shifts; fit the model to the PRC points.

### D16. Planner target and rules R1 to R7
Decision: the planner optimizes for the compromise phase position computed from the worker's own windows, and uses rules R1 (bright light before predicted CBTmin, ending 2 h before it), R2 (15% sunglasses on a daylight commute; 2% only for non-drivers), R3 (dark-room sleep within 1.5 h of arriving home, at least 7 h, fixed time), R4 (late rest-day sleep, default 03:00 to 11:00), R5 (15 min outdoor light brake within 2 h of waking), R6 (no bright light in the 2 h before sleep), R7 (safety limits).
Reason: these are the Eastman laboratory interventions that produced partial re-entrainment and better mood, fatigue and performance; margins and defaults are marked as design in docs/SCIENCE.md 5.4.
Alternatives: full re-entrainment protocols; light boxes only; no eyewear rule.

### D17. Caffeine and nap rules
Decision: caffeine cutoff 6 h before the planned sleep window (8 h when slow clearance is reported), caffeine allowed in the first half of the shift, no modeling of caffeine's phase effect, a pre-shift nap opportunity of 30 to 90 min placed 2 to 4 h before the shift and ending 30 min before leaving home, in-shift naps shown only as a note, nap blocks counted as dark in the light profile.
Reason: Drake 2013 supports the 6 h cutoff directly; Burke 2015's 40 min phase effect is too small and variable to plan on; Schweitzer 2006 and Garbarino 2004 support pre-shift naps; sleep inertia of 10 to 30 min motivates the margin (docs/SCIENCE.md 6.3).
Alternatives: half-life based cutoff; no nap recommendation; planned in-shift naps.

### D18. Misalignment score
Decision: score S is the mean over planned days of the absolute difference between the predicted CBTmin offset from mid-sleep and a target of 2 h before wake, plus 0.5 times the overlap in hours between the shift and a 4 h window centered on CBTmin. The Crowley re-entrainment category and a social-jetlag analogue are reported alongside. Recommendations explain themselves by ablation on S.
Reason: it follows how the literature places CBTmin inside sleep and how the Eastman studies categorize re-entrainment, while giving the planner a continuous objective. Design parts are labeled in docs/SCIENCE.md 7.3.
Alternatives: categorical score only; fraction of sleep inside biological night; a sleep-homeostat model.

### D19. Pilot instruments
Decision: Karolinska Sleepiness Scale at shift start and every 2 h, plus once after waking; Consensus Sleep Diary core items with Zeitgeber additions (shift, sunglasses, outdoor minutes, caffeine, naps, lux readings, adherence); 2 weeks baseline then 2 weeks on plan; data on paper or offline forms, never in the app.
Reason: standard, validated, low-burden instruments that match the 2 h cadence of the source studies; the design keeps the pilot a feasibility study and keeps personal data out of the product (docs/SCIENCE.md 8).
Alternatives: actigraphy; in-app data collection; a control group.

### D20. Sun times from astral using the NOAA equations
Decision: compute sunrise, sunset and civil twilight with the astral package (version 3.2) and verify against the NOAA calculator for Manila within 2 minutes. Default coordinates 14.5995 N, 120.9842 E, Asia/Manila.
Reason: NOAA states minute-level accuracy within 72 degrees of the equator; astral implements the same Meeus-based method and is small enough to replace with a direct implementation if needed (docs/SCIENCE.md 9).
Alternatives: implement the NOAA equations directly; use an ephemeris library such as skyfield.

### D21. The science specification precedes the package scaffold
Decision: Z3 is the science specification (this document set). The package scaffold and schedule data model merge into Z4, and later steps move by one day. The plan keeps 13 steps.
Reason: every constant and rule now has a source before any code depends on it, which is the project's science-first constraint.
Alternatives: scaffold first with a skeleton SCIENCE.md, as originally planned.

## 2026-11-09, architecture

### D22. Runtime: Python core as a Vercel Python function, batched integration, 0.1 h step per request
Decision: keep decision D3. The planner runs server-side in Python as a Vercel Python function in the same project as the web app. Integration is a batched fixed-step RK4 loop over the package's own `derv`. Every request runs at the 0.1 h step; the 1 min step is used only in tests. `MPLBACKEND=Agg` and `MPLCONFIGDIR=/tmp/matplotlib` are set in the function environment.
Reason: measured on the development Mac (docs/ARCHITECTURE.md 3.3), batching cut Forger99 from 76 ms to 0.9 ms per 14-day candidate with identical states, which puts a full request at about 2.8 s of compute. Pyodide matched exactly but needs about 47 MB of downloads and about 5 s of start-up per user. A TypeScript port of Forger99 ran 200 candidates in 41 ms but would duplicate all science code. Lambda would need a container image for about 216 MB of dependencies plus a registry, URL front end, IAM and a second pipeline.
Alternatives: AWS Lambda container image behind a Function URL (kept as the fallback, the ASGI app stays portable); Pyodide in the browser; TypeScript port (revisit for an on-device mode after v0.1).
Check: p95 latency on the deployed function under 6 s, measured in Z11.

### D23. Interface changes to the module proposal
Decision: adopt the interfaces in docs/ARCHITECTURE.md section 2, which change the starting proposal in seven ways: a `Location` model and a `SleepHabits` model in `schedule`; both commutes modeled; `RestDayPolicy` reduced to which days are rest days, because the rest-day sleep window is a planner parameter; a separate `grid` module with a `TimeGrid` shared by light and sim; interventions applied inside the light builder rather than by editing lux arrays; a `ClockModel` protocol with batched integration and a stricter equilibration rule; the grounding check and the language-model rewriter as separate pieces in `output`, with the provider behind a protocol.
Reason: each removes a source of silent error (mixed time grids, two code paths for baseline and candidate light, convergence judged on one marker) or keeps a responsibility in one place (UTC conversion only in `materialize`, vendor names only in settings).
Alternatives: the original seven-module proposal without `grid`; planner-side lux edits.

### D24. Planner search: seeded coordinate descent with restarts and ablation explanations
Decision: coordinate descent over seven discrete intervention parameters in a fixed order, four passes at most, eight seeded restarts, objective score plus soft-constraint penalties plus 0.05 h per active intervention, ties broken by order. Each recommendation's effect is measured by reverting it alone and re-simulating. Hannay19 runs only on the baseline and the chosen plan.
Reason: deterministic for a given seed, at most 1,260 simulations, fits the request budget, and produces explanations from simulator output only (docs/ARCHITECTURE.md section 4).
Alternatives: exhaustive grid search (tens of thousands of candidates); gradient-based optimal control as in Serkh and Forger 2014 (continuous light schedules that workers cannot follow); random search.

### D25. Build plan from Z5 to Z13 on Days 2 to 10
Decision: Z4 is the architecture step on Day 1. The package scaffold and schedule model move to Z5 on Day 2, and Z5 to Z13 map to Days 2 to 10 as in docs/ARCHITECTURE.md section 8, one step per build day.
Reason: the architecture and benchmark had to come before any package code so that the interfaces and runtime are fixed first.
Alternatives: keep the scaffold in Z4 and push the architecture into Z5.
