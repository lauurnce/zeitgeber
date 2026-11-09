# Progress

Build plan for v0.1 as a checklist. Day numbers are planned build days, one per real day. Each step closes with a Gate Report and a push. Scope and days may shift; changes are recorded in docs/DECISIONS.md.

- [x] Z1, Day 1: understand the project: restatement, hard parts, assumptions, risks, open questions.
- [x] Z2, Day 1: repository setup: license, ignore rules, project brief, decision log, progress plan, README stub.
- [ ] Z3, Day 2: Python package scaffold with uv and pytest; docs/SCIENCE.md and docs/ARCHITECTURE.md skeletons with citation rules; CI.
- [ ] Z4, Day 2: schedule data model: weekly shifts, rest days, commute, sleep; UTC internals with Asia/Manila display; property tests.
- [ ] Z5, Day 3: solar times and light-exposure profile: sunrise, sunset and twilight per date; lux environments with cited values; 14-day profile with burn-in.
- [ ] Z6, Day 4: model adapter over the circadian package: Forger99, Jewett99, Hannay19; equilibration; CBTmin and DLMO extraction.
- [ ] Z7, Day 5: science validation tests: phase response curve shape, free-running period, entrainment to a 24-hour cycle; sensitivity of outputs to lux constants.
- [ ] Z8, Day 6: misalignment score and planner: compromise phase target, action space, constraints from published strategies, ablation explanations.
- [ ] Z9, Day 7: plan output: 14-day timeline, .ics export with reminders, nudge templates in English and Taglish, wording validator.
- [ ] Z10, Day 8: FastAPI service: stateless endpoints, request validation, no request logging; Vercel Python function configuration.
- [ ] Z11, Day 9: web planner: Next.js App Router, schedule form with presets, next-12-hours view, 14-day timeline, .ics download.
- [ ] Z12, Day 10: landing page and pilot protocol document: Karolinska Sleepiness Scale, sleep diary, consent, data handling.
- [ ] Z13, Day 11: README, docs completion, SCIENCE.md review, v0.1 tag.
