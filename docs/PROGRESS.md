# Progress

Build plan for v0.1 as a checklist. Day numbers are planned build days, one per real day. Each step closes with a Gate Report and a push. Scope and days may shift; changes are recorded in docs/DECISIONS.md.

- [x] Z1, Day 1: understand the project: restatement, hard parts, assumptions, risks, open questions.
- [x] Z2, Day 1: repository setup: license, ignore rules, project brief, decision log, progress plan, README stub.
- [x] Z3, Day 2: science specification: models, package audit, light levels, phase response features, shift-work rules, caffeine and nap rules, misalignment score, pilot measures, sun times (docs/SCIENCE.md).
- [ ] Z4, Day 3: Python package scaffold with uv and pytest; circadian 1.0.3 install smoke test on Python 3.12; docs/ARCHITECTURE.md; schedule data model with UTC internals and Asia/Manila display; property tests.
- [ ] Z5, Day 4: solar times and light-exposure profile: sunrise, sunset and twilight per date; lux environments from SCIENCE.md 3.5; 14-day profile with burn-in.
- [ ] Z6, Day 5: model adapter over the circadian package: Forger99, Jewett99, Hannay19; equilibration; CBTmin and DLMO extraction.
- [ ] Z7, Day 6: science validation tests F1 to F9 from SCIENCE.md 4.3; sun time check against NOAA; sensitivity of outputs to lux constants.
- [ ] Z8, Day 7: misalignment score and planner: compromise phase target, rules R1 to R7, action space, ablation explanations.
- [ ] Z9, Day 8: plan output: 14-day timeline, .ics export with reminders, nudge templates in English and Taglish, wording validator.
- [ ] Z10, Day 9: FastAPI service: stateless endpoints, request validation, no request logging; Vercel Python function configuration.
- [ ] Z11, Day 10: web planner: Next.js App Router, schedule form with presets, next-12-hours view, 14-day timeline, .ics download.
- [ ] Z12, Day 11: landing page and pilot protocol document from SCIENCE.md 8.
- [ ] Z13, Day 12: README, docs completion, SCIENCE.md review, v0.1 tag.
