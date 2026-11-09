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
