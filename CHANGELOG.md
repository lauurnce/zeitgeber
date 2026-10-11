# Changelog

All notable changes to Zeitgeber. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [semantic versioning](https://semver.org/).

## [0.1.0] - 2026-10-11

First release.

### Added

- Core library `zeitgeber` (distribution `zeitgeber-core`), Python 3.12:
  - `schedule`: a weekly shift schedule with commutes, current sleep and rest-day habits, validated into plain-word errors, and turned into 14 days of UTC intervals.
  - `light`: sunrise and sunset for the worker's location (astral) and a light profile in lux every 0.1 h, with sunglasses and planner light blocks.
  - `sim`: an adapter over the circadian 1.0.3 package (Forger99, Jewett99, Hannay19) with batched RK4 integration, warm-up to a steady state, and CBTmin and DLMO markers.
  - `prc`: the phase response protocol used to check the models against Khalsa et al. 2003 and St Hilaire et al. 2012.
  - `score`: the misalignment score with its parts reported separately (phase angle, work in the circadian low, sleep inside the biological night, social-jetlag analogue).
  - `plan`: the intervention space (sunglasses, day sleep timing and length, rest-day sleep, light brake, bright light in the shift, pre-shift nap, caffeine window), hard constraints, a seeded coordinate-descent search with restarts, and an ablation explanation per change.
  - `output`: the plan document (JSON schema 1.0), a text timeline, an iCalendar export with reminders in Asia/Manila time, and nudges in English and Taglish from one string catalog, with optional rewording held to the plan by a grounding check.
- HTTP API (FastAPI, Vercel Python function): `GET /v1/health`, `POST /v1/plan`, `POST /v1/plan.ics`, `POST /v1/calendar`, `POST /v1/simulate`. Stateless, no request-body logging, problem-details errors, CORS for the web app, body size limit and per-client rate limit.
- Web app (Next.js): a landing page and the planner at `/plan` with the radial body-clock chart, a 14-day timeline, the score before and after, reasons for each change, an English and Taglish toggle, and calendar download. Keyboard use, labelled controls, text equivalents for charts, AA contrast, 360 px layouts.
- Documentation: `docs/SCIENCE.md` (every model, constant and rule with its source), `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/API.md`, `docs/COPY_REVIEW.md`, `docs/PILOT_PROTOCOL.md`, `CITATION.cff`, and an animated README header drawn from model output.
- Tests: 314 core and 27 API tests (pytest), 25 component tests (vitest) and Playwright end-to-end tests, run in CI on every push.

### Known limitations

- `POST /v1/plan` takes about 22 s on the deployed function, over the 6 s budget (docs/DECISIONS.md D42).
- The planner cannot improve on the current schedule for the rotating-shift fixture (D34).
- The science validation step Z8 (features F3 to F8 and the sensitivity runs) is still open; the models reproduce F1, F2 and F9.
- The Taglish text is a draft waiting for review by a native speaker.

[0.1.0]: https://github.com/lauurnce/zeitgeber/releases/tag/v0.1.0
