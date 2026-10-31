# Progress

Build plan for v0.1 as a checklist. Day numbers are planned build days, one per real day. Each step closes with a Gate Report and a push. Scope and days may shift; changes are recorded in docs/DECISIONS.md. Details per step, including the tests that prove it and the expected commit range, are in docs/ARCHITECTURE.md section 8.

- [x] Z1, Day 1: understand the project: restatement, hard parts, assumptions, risks, open questions.
- [x] Z2, Day 1: repository setup: license, ignore rules, project brief, decision log, progress plan, README stub.
- [x] Z3, Day 1: science specification (docs/SCIENCE.md).
- [x] Z4, Day 1: architecture, runtime benchmark and build plan (docs/ARCHITECTURE.md, scripts/bench_sim.py, scripts/bench_sim.mjs).
- [x] Z5, Day 2: scaffold: uv project on Python 3.12 with circadian 1.0.3 pinned, docstring-only modules, ruff and mypy, smoke test; FastAPI health route and test; Next.js placeholder with strict TypeScript, Tailwind, eslint, prettier and vitest; three fixture schedules; pre-commit, Makefile and CI.
- [x] Z6, Day 3: `schedule`, `grid` and `light` modules: schedule models and validation, time grid, solar times checked against USNO, lux constants from SCIENCE 3.5, light profile builder with sunglasses, 3-day figure (docs/figures/). Batch builder moves to Z9.
- [x] Z7, Day 4: `sim` module: model adapters, batched integration, equilibration, markers; PRC reproduction (docs/figures/prc.png).
- [ ] Z8, Day 5: science validation: F1 to F9, sensitivity harness.
- [x] Z9, Day 6: `score` and `plan` modules: score, constraints, seeded search, explanations (golden plans pinned by tests; Z8 validation still open).
- [x] Z10, Day 7: `output` module: plan document (schema 1.0), timeline, .ics, nudges in English and Taglish, grounding check with template fallback, docs/COPY_REVIEW.md (Taglish awaiting review).
- [ ] Z11, Day 8: `api/`: FastAPI app, Vercel function, latency measurement. Built and deployed (https://zeitgeber-five.vercel.app, docs/API.md); open until `/v1/plan` meets the 6 s budget (D42).
- [x] Z12, Day 9: `web/`: planner UI (/plan), vitest component tests, Playwright end to end, screenshots in docs/figures.
- [ ] Z13, Day 10: landing page, pilot protocol, README, SCIENCE.md review, v0.1 tag. Landing page and web deploy done (https://zeitgeber-web.vercel.app); pilot protocol, README, SCIENCE.md review and the v0.1 tag remain.
