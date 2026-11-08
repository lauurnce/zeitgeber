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

## Scaffold

### D26. The scaffold is its own step; schedule and grid code moves to Z6
Decision: Z5 builds only the empty skeleton (package with docstring modules, API health route, web placeholder, fixtures, tooling, CI). The `schedule` and `grid` implementations move into Z6 alongside the light builder. The API health route is `/v1/health`, as in docs/ARCHITECTURE.md 2.8.
Reason: the scaffold step was scoped as "no algorithm code"; keeping it free of models lets CI, tooling and fixtures settle before the first real module.
Alternatives: implement the schedule models in the scaffold step.

## Schedule model and light profile

### D27. Schedule schema as built
Decision: commutes take an outdoor share (0 to 1) instead of outdoor minutes; `SleepHabits` becomes `SleepWindows` with an after-shift window, per-weekday overrides for rotations, a rest-day window and an optional second rest-day window; `RestDayPolicy` has three modes (`keep_nights`, `flip_to_days`, `split`); `Location` defaults to Manila. The after-shift sleep is placed after each shift and rest-day sleep fills rest days where it overlaps nothing.
Reason: the phase brief asked for an outdoor share and the three rest-day modes. Rotating schedules need a different sleep after each shift type, which one workday window cannot express. Placing sleep relative to shifts lets night workers and day workers share one rule.
Alternatives: one workday sleep window keyed to calendar days; free-form lists of sleep intervals.

### D28. Light builder placement rules
Decision: a commute's outdoor minutes sit half at the start and half at the end; daylight lux applies only between sunrise and sunset, so civil twilight counts as dark; transit after dark uses the 10 lux night value; sunglasses scale the whole commute home while the sun is up; phone-in-bed minutes dim home light only. Building many candidate profiles in one batch (`build_light_batch`) moves to the planner step, where it is first needed.
Reason: walking to and from transport is where outdoor exposure happens on a jeepney or train commute; treating twilight as dark is the conservative choice for the delaying side of the clock; all values stay on the cited constants in docs/SCIENCE.md 3.5.
Alternatives: outdoor minutes spread across the commute; a twilight lux ramp; sunglasses only on outdoor minutes.

## Simulator

### D29. Simulator conventions as built
Decision: light sample `i` acts over `[t_i, t_i + step)` and the trajectory carries `n + 1` rows so a run can be continued from its last state; CBTmin is found as the deepest local minimum within 13 h (as in the package) and refined by a parabola through three samples; the warm-up loops a whole-day baseline from the package's default state until every CBTmin moves less than 0.05 h, up to 40 loops, and reports non-convergence instead of raising; the baseline defaults to the profile itself, which is the worker's current schedule. The phase response protocol lives in `zeitgeber/prc.py` with a paired control run per pulse. The F1 test reads "before" and "after" CBTmin as pulse centers 2 to 8 h either side.
Reason: the package applies `light[i]` over the step that ends at `t_i`, which shifts light by one step relative to the grid's meaning; sub-step marker times keep 0.1 h runs within 0.03 h of 1 min runs; paired controls cancel free-running drift without fitting a period; near 12 h from CBTmin any Type 1 curve crosses zero again, so the literal F1 wording cannot hold there.
Alternatives: call the package's `integrate` and `equilibrate` directly; markers on grid points only; read shifts against a fitted free-running period; a fixed number of warm-up loops.

### D30. Example worker result differs from the Z3 prediction
Decision: keep the model's result as the reference for the Z3 worker (CBTmin near 15:00, inside the end of the workday day sleep and outside rest-day sleep) and record the difference from the Z3 prediction in docs/SCIENCE.md 5.7. Treat rest-day light and office lux as first-order inputs in the Z8 sensitivity harness, and ask for rest-day light in the pilot.
Reason: the model shows the clock moving about 3 h later in the first week and settling on the night schedule, because the v0.1 profile gives rest days no daylight and gives shifts nine hours at 500 lux. Field studies found less adaptation. The inputs are UNVERIFIED, so the gap is a question for the light constants, not grounds to change the equations.
Alternatives: change rest-day defaults now to add outdoor time; tune lux constants until the model matches the field studies (rejected: fitting constants to one expectation without measurements).

## Score and planner

### D31. Morning rest-day sleep belongs to the night after the rest day
Decision: a rest-day window that starts before 12:00 is placed on the calendar day after the rest day.
Reason: rule R4's late window (03:00 to 11:00) started on the first rest day collides with the last night shift and was silently dropped, and `keep_nights` left the worker awake from Sunday afternoon to Tuesday morning. Evening windows are unchanged, so the Z7 results do not move.
Alternatives: a separate "night of" field on each window; reject windows that collide instead of skipping them.

### D32. Score as built
Decision: each main sleep episode of 4 h or more wholly inside the plan window is a scored day. `S` follows SCIENCE 7.3 exactly. Reported beside it and not part of it: mean phase angle term, mean work in the circadian low, the share of sleep inside the biological night (CBTmin - 6 h to CBTmin + 2 h), the social-jetlag analogue, and the Crowley category per day with an added "past" category when CBTmin falls after wake.
Reason: scoring per episode keeps both sleeps of a day such as Saturday after a Friday night shift; clipped episodes at the window edges would score against partial sleeps.
Alternatives: one scored day per calendar date; add the biological-night share into `S`.

### D33. Planner as built
Decision: sleep timing (R3), the light brake (R5) and the pre-shift nap (N1) act around night shifts only (shifts that cross midnight); bright light in the shift (R1) and sunglasses (R2) apply to every shift; rest-day options are "as now" or the late R4 windows from 01:00 to 04:00, never a switch to night hours; R3's 7 h minimum and R1's 2 h margin are soft penalties (1.0 h and 0.5 h); search uses 4 passes and 4 seeded restarts; the light brake sits 30 min after waking.
Reason: R3, R5 and N1 come from permanent-night protocols. With `keep_nights` on offer the planner chose full adaptation (score 0.09 h), which D1 ruled out. A brake placed 1 h after a 17:00 wake would fall after sunset in November.
Alternatives: apply sleep timing to every shift type; hard 7 h minimum; offer keep_nights.

### D34. Plans that cannot beat the current schedule are reported, not forced
Decision: the "plan beats the current schedule" test is strict for the permanent nights worker and an expected failure, with the reason, for the rotating worker and the day worker. Separate tests pin what the planner does for those two: nothing for the day worker; for the rotating worker, 7 h sleep after nights at a cost under 0.05 h of score.
Reason: an exhaustive check of 360 candidates found no plan with at least 7 h after night shifts that lowers the rotating worker's score; the modelled clock stays day-oriented through two nights a week. The day worker is a control. Loosening R3 or the score to pass the test would hide that.
Alternatives: relax R3 for short runs of nights; score rotations against a day-oriented target.

## Outputs

### D35. Plan document and calendar as built
Decision: the plan document (schema 1.0, docs/schema/plan-1.0.json) carries every text in English and Taglish and includes the nudges. An event is marked as a recommendation when the plan adds it (sunglasses, light blocks, nap, caffeine window) or moves a sleep compared with the worker's current schedule. Sunglasses events cover commutes home with the sun up at any point. Reminder lead times: 30 min before sleep and rest-day sleep, 10 min before a nap, at the start of light blocks and the commute home, and 30 min before the end of the caffeine window. The calendar uses `TZID=Asia/Manila` with a fixed-offset VTIMEZONE, falls back to UTC times for a zone whose offset changes during the plan, marks plan blocks as free time, and keeps UIDs stable for a given plan.
Reason: one document serves the web, the API and the calendar without a second request per language. Marking sleeps by comparison avoids calling an unchanged sleep "new". Lead times are design values (UNVERIFIED as behavior aids). Stable UIDs let a re-import update events instead of duplicating them.
Alternatives: one document per language; mark every sleep as new when any sleep parameter changes; reminders for shifts and commutes; a full VTIMEZONE built from the tz database.

### D36. Grounding check for optional rewording
Decision: a rewording is accepted only when (1) every time and number in it, written as digits, 12 h or 24 h clock, or as an English, Tagalog or Spanish-derived number word including the Tagalog linker form, also appears in the filled template it rewrites; (2) it contains no term from the blocklist (English medical terms and Tagalog equivalents, docs/COPY_REVIEW.md); (3) it is at most 1.6 times the template length plus 40 characters. Any failure or provider error keeps the template. Each distinct text is sent once, in parallel. The provider sees one filled template and the language, never the schedule. Rewording is off unless `ZEITGEBER_LLM_WORDING` is set; the default model is `claude-opus-5-5` at low effort, and a refusal keeps the template rather than retrying on a second model.
Reason: comparing against the nudge's own template rejects a correct time from the wrong day; number words would otherwise let a rewording add a quantity ("dalawang tasa"). The length cap limits added claims, which a word list cannot catch.
Alternatives: allow any time or number found anywhere in the plan; a second model call to judge claims; server-side fallback models for refusals.

### D37. One string catalog with a generated review document
Decision: every user-facing string in the outputs lives in `zeitgeber/output/copy.toml` with English and Taglish side by side and a note on where it appears. docs/COPY_REVIEW.md is generated from it, and tests fail when the two differ, when a pair uses different placeholders, when a string contains a blocked term or a non-ASCII character, or when a nudge template contains a number of its own. Nudge templates follow the voice examples given for Z10; the Taglish is a draft for review by a native speaker.
Reason: the reviewer edits one file, and no number in a nudge can come from anywhere but the plan.
Alternatives: gettext catalogs; strings inline in code; a hand-maintained review document.

### D38. Nudges only for events that ask something of the worker
Decision: nudges are written for sleep, rest-day sleep in a planned late window, nap, light blocks, sunglasses and the caffeine window. Shifts, commutes and unchanged rest-day sleep get none. Day sleep uses the "lowest body clock" wording only when the predicted CBTmin falls inside that sleep. Changes that raise the score on their own are explained as trade-offs (the 7 h sleep floor, or the plan as a whole).
Reason: a nudge for an unchanged 22:00 rest-day sleep would claim a "late night" that is not there; the sleep wording should not state a body-clock fact the model does not show for that day.
Alternatives: a nudge for every event; one sleep wording for all days.

## API and deployment

### D39. API as built
Decision: routes live under `/v1` (`/v1/health`, `/v1/plan`, `/v1/plan.ics`, `/v1/simulate`). Request bodies reject unknown fields. Validation errors return `422` problem details with a location, a plain message and a type per problem, without echoing the submitted values. A valid schedule with no feasible plan also returns `422`. Every response carries `Cache-Control: no-store`. Unhandled exceptions are turned into a plain `500` inside the app and logged by exception type and path only, so neither the response nor the log carries schedule details. The rate limit runs as a route dependency, so invalid requests count too.
Reason: a version prefix lets the plan schema change without breaking clients; the default error path in the framework re-raises to the server log with the exception message, which can contain schedule times.
Alternatives: unversioned `/plan` as written in the Z11 prompt; FastAPI's default error bodies; logging requests for debugging (rejected: privacy rule).

### D40. Deployment on Vercel from the repository root
Decision: the API is the Vercel project `zeitgeber` (production `https://zeitgeber-five.vercel.app`), a Python function from `api/index.py` in region `sin1` with a 60 s limit. Dependencies come from `requirements.txt`, exported from `uv.lock` (`make requirements`, checked in CI). `.vercelignore` is an allowlist (`api/`, `zeitgeber/`, the requirements and licence files). The project is connected to the GitHub repository, so pushes to `main` deploy to production. No secrets are needed; a provider key for optional wording would be set with `vercel env add`, never in git. The web app joins the same project in the web phase.
Reason: Z4 chose a Vercel Python function. Singapore is the closest region to Manila. The allowlist keeps local-only files out of the upload. The bundle is 286 MB, under the 500 MB Python limit.
Alternatives: AWS Lambda container with SAM (the Z4 fallback); a separate API project; `iad1`.

### D41. Rate limiting per function instance
Decision: an in-memory sliding window of 20 requests per minute per client on the compute routes, keyed by a salted hash of the first forwarded address. Each instance keeps its own counts.
Reason: there is no store to share counts in (privacy rule), and a burst spread over instances only costs compute. A platform firewall rule can add a global limit later without code.
Alternatives: Vercel Firewall rate-limit rule; a Redis counter (rejected: storage).

### D42. The plan route does not meet the 6 s budget yet
Decision: record the measured latency (about 22 s warm on Vercel with the cross-check, 17 s without; 6.4 s and 5.2 s on the development Mac) and keep the latency test as a strict expected failure until a fix is chosen. Running restart descents in lockstep (same plans, same seeds) is already in; it halved the time.
Reason: the time is set by the number of sequential coordinate-descent steps, each a full 14-day integration through the package's derivative, and the function's CPU is about three times slower per call than the development Mac. The remaining options change the science path or the search, so they need a decision: (a) search at a 0.2 h step and re-score the chosen plan and ablations at 0.1 h (about half the time, needs a check that rankings hold); (b) a compiled copy of the model derivatives tested against the package (about ten times faster, but a second implementation of the equations, which Z4 avoided); (c) fewer passes or options (changes plans); (d) make the Hannay19 cross-check opt-in (saves about 5 s on the function); (e) accept about 20 s with a progress view in the web app.
Alternatives: loosen the budget or the test to pass (rejected).
