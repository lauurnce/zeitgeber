# Zeitgeber architecture

This document describes how the pieces of Zeitgeber fit together, the public interfaces between them, the runtime decision and the numbers behind it, the planner design, the testing strategy, tooling, risks and the build plan. Science inputs (models, constants, rules) are defined in docs/SCIENCE.md and are referenced here by section number.

Conventions: times inside the core are timezone-aware UTC `datetime` values or hours as `float` on a uniform grid; light is photopic lux; phase is radians; durations in hours unless a name says minutes.

## 1. System diagram

```mermaid
flowchart LR
  subgraph web["web/ (Next.js App Router, Vercel)"]
    FORM["Schedule form"]
    VIEW["Next 12 h view, 14-day timeline, nudges"]
    DL[".ics download"]
  end

  subgraph api["api/ (FastAPI, Vercel Python function)"]
    EP["POST /v1/plan"]
    EPICS["POST /v1/plan.ics"]
    ORCH["orchestrator: validate, run core, no body logging"]
  end

  subgraph core["zeitgeber/ (Python core library)"]
    SCHED["schedule: Schedule, Shift, Commute, SleepHabits, RestDayPolicy, Location"]
    GRID["grid: TimeGrid (UTC start, step, length)"]
    LIGHT["light: solar times + LightProfile builder"]
    SIM["sim: ClockModel adapter, batched RK4, markers"]
    SCORE["score: misalignment S, Crowley category, social jetlag"]
    PLAN["plan: intervention space, constraints, seeded search, explanations"]
    OUT["output: PlanDocument, timeline, .ics, nudges, grounding check"]
  end

  FORM --> EP
  DL --> EPICS
  EP --> ORCH
  EPICS --> ORCH
  ORCH --> SCHED
  SCHED --> GRID
  GRID --> LIGHT
  SCHED --> LIGHT
  LIGHT --> SIM
  SIM --> SCORE
  SCORE --> PLAN
  PLAN -- "candidate interventions" --> LIGHT
  PLAN --> OUT
  OUT --> ORCH
  ORCH --> VIEW
  ORCH --> DL

  CIRC[("circadian 1.0.3")] -.-> SIM
  ASTRAL[("astral 3.2")] -.-> LIGHT
  LLM[("LLM provider, optional, off by default")] -.-> OUT
```

Data flow for one request: the web form posts a `Schedule`; the API validates it and calls the core; the core builds the baseline light profile, equilibrates the model on the current habits, scores the baseline, searches the intervention space (each candidate is a new light profile simulated in a batch), explains the chosen interventions by ablation, and renders a `PlanDocument`; the API returns JSON or an .ics file; nothing is stored.

## 2. Modules and public interfaces

Package layout (distribution name `zeitgeber-core`, import name `zeitgeber`):

```
zeitgeber/
  schedule.py   # input models and validation
  grid.py       # TimeGrid shared by light and sim
  light.py      # solar times, lux constants, LightProfile builder
  sim.py        # ClockModel protocol, package adapters, batched integration, markers
  score.py      # misalignment score (SCIENCE 7)
  plan.py       # intervention space, constraints, search, explanations (SCIENCE 5, 6, 7)
  output.py     # PlanDocument, timeline, .ics, nudges, grounding check, rewriter protocol
  settings.py   # runtime settings (model, language, llm_wording, provider)
api/            # FastAPI app and Vercel function entry
web/            # Next.js planner and landing page
scripts/        # benchmarks and one-off tools
```

Changes from the starting proposal are marked "change" and explained in place.

### 2.1 zeitgeber/schedule

```python
class Location(BaseModel):                      # change: added; light depends on it
    name: str
    latitude: float                             # degrees, -72 to 72
    longitude: float                            # degrees, -180 to 180
    timezone: str = "Asia/Manila"               # IANA name

class Shift(BaseModel):
    weekday: int                                # 0 = Monday; the local day the shift starts
    start: time                                 # local wall clock
    end: time                                   # local; earlier than start means it crosses midnight

class Commute(BaseModel):
    duration_min: int                           # 0 to 300
    outdoor_min: int                            # 0 to duration_min; counted as daylight only when the sun is up
    mode: Literal["walk", "jeepney_bus", "train", "car_driver", "car_passenger", "motorcycle"]
    @property
    def drives(self) -> bool                    # car_driver or motorcycle; gates the dark-lens rule (R2)

class SleepHabits(BaseModel):                   # change: added; current behaviour defines the burn-in
    workday_sleep_start: time
    workday_sleep_end: time
    restday_sleep_start: time
    restday_sleep_end: time
    phone_in_bed_min: int = 0                   # light at 30 lux before sleep (SCIENCE 3.5)

class RestDayPolicy(BaseModel):
    weekdays: list[int]                         # rest days, 0 = Monday
    keep_night_schedule: bool = False           # True: the worker already sleeps late on rest days

class Schedule(BaseModel):
    anchor_date: date                           # local date of the first planned day
    plan_days: int = 14
    location: Location
    shifts: list[Shift]                         # at most one per weekday
    commute_to_work: Commute                    # change: both commutes modeled
    commute_home: Commute
    sleep: SleepHabits
    rest_days: RestDayPolicy

    def materialize(self) -> list[Interval]:    # absolute UTC intervals for burn-in and plan days

@dataclass(frozen=True)
class Interval:
    start: datetime                             # UTC, timezone-aware
    end: datetime
    kind: Literal["shift", "commute_to_work", "commute_home", "sleep", "rest_sleep", "nap", "light_seek", "light_brake"]
    day_index: int                              # 0-based plan day the interval belongs to
```

Validation: at most one shift per weekday; shift length 4 to 14 h; rest days are the weekdays without shifts unless listed; `outdoor_min <= duration_min`; sleep windows 3 to 12 h; latitude within 72 degrees (SCIENCE 9.5); timezone resolvable. `materialize` is the only place that turns wall-clock times into UTC, so midnight crossing is handled once.

Change: the rest-day sleep window is a planner parameter (rule R4), so `RestDayPolicy` carries only which days are rest days and whether the worker already keeps a late schedule; the current rest-day sleep times live in `SleepHabits` for the burn-in.

### 2.2 zeitgeber/grid (change: added)

```python
@dataclass(frozen=True)
class TimeGrid:
    start: datetime                             # UTC
    step_h: float                               # 0.1 for search, 1/60 for verification
    n: int
    def hours(self) -> np.ndarray               # shape (n,), hours since start
    def index(self, t: datetime) -> int
    def at(self, i: int) -> datetime
    def mask(self, interval: Interval) -> np.ndarray   # boolean (n,)
```

Light arrays, trajectories and markers all carry the grid they were computed on, so arrays cannot be mixed by accident.

### 2.3 zeitgeber/light

```python
class LuxConstants(BaseModel):                  # values from SCIENCE 3.5, all named so tests can scale them
    outdoor_sun: float = 10_000
    shade_or_vehicle: float = 1_000
    office: float = 500
    home: float = 100
    home_dim_phone: float = 30
    sleep: float = 1
    night_street: float = 10
    sunglasses: dict[str, float] = {"none": 1.0, "cat3": 0.15, "dark": 0.02}
    light_seek: float = 1_000

@dataclass(frozen=True)
class SolarTimes:
    dawn: datetime; sunrise: datetime; noon: datetime; sunset: datetime; dusk: datetime   # UTC

def solar_times(location: Location, day: date) -> SolarTimes          # astral 3.2 (SCIENCE 9)
def sun_up(location: Location, grid: TimeGrid) -> np.ndarray          # boolean (n,), cached per date

@dataclass(frozen=True)
class LightProfile:
    grid: TimeGrid
    lux: np.ndarray                             # (n,) or (n, batch)
    labels: np.ndarray                          # int8 environment codes, (n,) or (n, batch)

def build_light_profile(schedule: Schedule, grid: TimeGrid,
                        interventions: Interventions | None = None,
                        constants: LuxConstants = LuxConstants()) -> LightProfile
def build_light_batch(schedule: Schedule, grid: TimeGrid,
                      candidates: Sequence[Interventions],
                      constants: LuxConstants = LuxConstants()) -> LightProfile   # lux shape (n, len(candidates))
```

Change: interventions are applied inside the light builder. Sunglasses scale outdoor samples, a light-seeking window overrides office samples, naps and sleep windows set dark samples, and the light brake inserts an outdoor block. The planner never edits lux arrays, so baseline and candidate profiles are built by the same code and tested once. Labels record which environment produced each sample, which the explanations and timeline use.

### 2.4 zeitgeber/sim

```python
class ClockModel(Protocol):
    name: str                                   # "forger99", "jewett99", "hannay19"
    n_states: int
    def derivative(self, t_h: float, state: np.ndarray, lux: np.ndarray) -> np.ndarray   # state (n_states, batch)
    def default_state(self) -> np.ndarray
    def cbt_min_hours(self, hours: np.ndarray, states: np.ndarray) -> np.ndarray          # per batch column
    def dlmo_hours(self, hours: np.ndarray, states: np.ndarray) -> np.ndarray             # cbt minus 7 h (SCIENCE 1.6)

class ForgerAdapter: ...    # wraps circadian.models.Forger99; the only module that imports the package
class JewettAdapter: ...
class HannayAdapter: ...

@dataclass(frozen=True)
class Trajectory:
    grid: TimeGrid
    states: np.ndarray                          # (n, n_states, batch)

@dataclass(frozen=True)
class Markers:
    cbt_min: list[np.ndarray]                   # one array of UTC hours-since-grid-start per batch column
    dlmo: list[np.ndarray]

def integrate(model: ClockModel, grid: TimeGrid, lux: np.ndarray, state0: np.ndarray) -> Trajectory
def equilibrate(model: ClockModel, grid: TimeGrid, lux: np.ndarray,
                loops: int = 6, tol_h: float = 0.05) -> np.ndarray      # returns state (n_states,)
def markers(model: ClockModel, trajectory: Trajectory) -> Markers
```

Change: `integrate` is a batched fixed-step RK4 loop that calls the package's `derv` through the adapter, instead of the package's own `integrate`. The package loop handles one light array at a time and takes 76 ms per 14-day candidate on the development Mac; the batched loop takes 0.9 ms per candidate with bit-identical states (section 3). The package's `integrate` remains the reference in parity tests.

Change: `equilibrate` declares convergence when every daily CBTmin moved by less than `tol_h` between the last two loops, not when the last DLMO moved by less than 0.001 h. The package's check warned after 3 loops in the benchmark; the weekly schedule needs about 6 loops of 14 days.

### 2.5 zeitgeber/score

```python
@dataclass(frozen=True)
class DayScore:
    day_index: int
    mid_sleep_h: float; cbt_min_h: float | None
    delta_h: float; target_h: float; misalignment_h: float      # Delta_d, t_d, M_d (SCIENCE 7.3)
    shift_overlap_h: float                                       # P_d
    category: Literal["not", "partial", "complete", "no_marker"]

@dataclass(frozen=True)
class ScoreBreakdown:
    total_h: float                              # S
    days: list[DayScore]
    social_jetlag_h: float
    lam: float

def score(markers: Markers, sleep: list[Interval], shifts: list[Interval],
          lam: float = 0.5, target_before_wake_h: float = 2.0) -> ScoreBreakdown
def wrap_hours(delta_h: float) -> float          # into (-12, 12]
```

### 2.6 zeitgeber/plan

```python
class Interventions(BaseModel):                 # one candidate plan; defaults are "do nothing"
    sleep_start_offset_h: float = 0.0           # after arriving home, 0 to 1.5 step 0.5 (R3)
    sleep_len_h: float = 7.0                    # 7 to 9 step 1 (R3)
    sunglasses: Literal["none", "cat3", "dark"] = "none"    # R2; "dark" only when not driving
    light_seek_start_h: float | None = None     # hours after shift start, step 1 (R1)
    light_seek_len_h: float = 0.0               # 0, 0.5, 1.0 (R1)
    light_brake: bool = False                   # R5
    rest_sleep_start: time = time(1, 0)         # 01:00 to 04:00 step 1 h, 8 h long (R4)
    nap_len_min: int = 0                        # 0, 30, 60, 90, ending 30 min before leaving (N1)
    nap_before_shift_h: float = 3.0             # fixed in v0.1
    @property
    def caffeine_cutoff_before_sleep_h(self) -> float   # 6, or 8 when slow clearance is reported (C1, C2)

class InterventionSpace:
    def __init__(self, schedule: Schedule) -> None
    def options(self, name: str) -> list[Any]           # allowed values per parameter for this schedule
    def feasible(self, c: Interventions) -> bool         # static constraints (driving, nap fits the gap)

@dataclass(frozen=True)
class Violation:
    rule_id: str; detail: str; hard: bool

class Constraints:
    def check(self, c: Interventions, markers: Markers, schedule: Schedule) -> list[Violation]   # SCIENCE 5.4 and 6.3

@dataclass(frozen=True)
class SearchConfig:
    seed: int = 0
    passes: int = 4
    restarts: int = 8
    step_h: float = 0.1                         # request path; 1/60 only in tests (section 3.4)
    lam: float = 0.5
    burden_h: float = 0.05
    model: str = "forger99"
    cross_check: str | None = "hannay19"

@dataclass(frozen=True)
class Explanation:
    intervention: str; rule_ids: list[str]
    delta_score_h: float                        # score without it minus score with it
    delta_cbt_day7_h: float; delta_cbt_day14_h: float

@dataclass(frozen=True)
class PlanResult:
    baseline: ScoreBreakdown; chosen: Interventions; score: ScoreBreakdown
    markers_baseline: Markers; markers_plan: Markers
    cross_check: Markers | None                 # Hannay19 on the final plan only
    explanations: list[Explanation]
    evaluations: int; seed: int

def search(schedule: Schedule, config: SearchConfig = SearchConfig()) -> PlanResult
def explain(schedule: Schedule, chosen: Interventions, config: SearchConfig) -> list[Explanation]
```

Change: the request path runs at the 0.1 h step throughout; the 1 min step is used only in tests that bound the difference (section 3.4).

Change: the cross-check model runs on the baseline and the final plan only, not on every candidate. Hannay19 costs about 2.5 times Forger99 per step (section 3) and its job is a second opinion, not a search objective.

### 2.7 zeitgeber/output

```python
class PlanEvent(BaseModel):
    kind: Literal["sleep", "nap", "sunglasses", "light_seek", "light_brake", "caffeine_cutoff", "shift", "commute"]
    start_utc: datetime; end_utc: datetime
    start_local: str; end_local: str            # "HH:MM" in the schedule timezone
    rule_id: str | None
    text_en: str; text_tl: str
    numbers: dict[str, float]                   # every number that appears in the texts

class PlanDay(BaseModel):
    date: date; label: str                      # "Night of Tue to Wed"
    events: list[PlanEvent]
    cbt_min_local: str | None; category: str

class PlanDocument(BaseModel):
    version: str; generated_at: datetime; timezone: str; language: Literal["en", "tl"]
    days: list[PlanDay]
    score: ScoreBreakdown; baseline_score: ScoreBreakdown
    explanations: list[Explanation]
    cross_check_note: str | None
    disclaimers: list[str]                      # wellness framing, doctor referral

def render_timeline(doc: PlanDocument) -> list[dict]          # rows for the web timeline
def render_ics(doc: PlanDocument, alarms: bool = True) -> bytes   # one VEVENT per event, VALARM, TZID
def render_nudges(doc: PlanDocument, lang: Literal["en", "tl"]) -> list[str]

class GroundingCheck:
    banned_terms: tuple[str, ...]               # melatonin, dose, disorder, treat, cure, diagnose, and translations
    def numbers_in(self, text: str) -> set[str]
    def passes(self, text: str, allowed: set[str]) -> bool   # no new numbers or times, no banned term

class Rewriter(Protocol):
    def rewrite(self, text: str, tone: str, lang: str) -> str

class AnthropicRewriter: ...                     # provider adapter; enabled only when settings.llm_wording is true

def finalize_nudge(template_text: str, allowed_numbers: set[str],
                   rewriter: Rewriter | None, check: GroundingCheck) -> str   # falls back to the template
```

Change: the grounding check is its own class with the banned-term list, and the language-model provider sits behind a `Rewriter` protocol so the product never names a vendor outside `settings.py`.

### 2.8 api/

- `GET /v1/health` returns version and model names.
- `POST /v1/plan` takes `{schedule: Schedule, options: {model, language, llm_wording}}` and returns `PlanDocument`.
- `POST /v1/plan.ics` takes the same body and returns `text/calendar`.
- Body limit 32 KB, request timeout 25 s, CORS for the web origin only, errors as problem JSON (RFC 9457), access log without bodies or query strings, no cookies, no persistence.
- Entry point `api/index.py` for the Vercel Python runtime; the same ASGI app runs under Mangum on Lambda if hosting changes (section 3).

### 2.9 web/

- Routes: `/` landing page, `/plan` planner (form, next 12 h view, 14-day timeline, nudges, .ics download), `/science` summary with links to docs/SCIENCE.md.
- Form presets for common BPO shifts and copy-to-all weekdays; English and Taglish toggle.
- Calls `/api/v1/plan` on the same deployment; keeps the plan in memory only; no analytics on form inputs.
- Mobile-first; the next 12 h view is the default on phones.

## 3. Runtime decision

### 3.1 Question

Where should the simulator and planner run: (a) a Python API on a serverless host, (b) Python in the browser with Pyodide, or (c) a TypeScript port with parity tests? The answer depends on how long one request takes, how much has to be downloaded or deployed, and how many copies of the science code must be kept correct.

### 3.2 Method

- `scripts/bench_sim.py` simulates 14 days for one schedule (3 burn-in loops, 14 days, CBTmin markers) and for 200 candidate plans, at the planning step of 0.1 h and the verification step of 1 min (SCIENCE 1.7). Candidates vary sleep start and length, sunglasses, a light-seeking hour and rest-day sleep. It times the package's own `integrate` loop and a batched RK4 loop that calls the package's `derv` for all candidates at once, and checks that both give the same states.
- The same script runs unchanged inside Pyodide 314.0.7 under Node, with numpy, scipy and matplotlib from the Pyodide distribution and fastcore and circadian 1.0.3 from PyPI through micropip.
- `scripts/bench_sim.mjs` is a 60-line JavaScript port of the Forger99 equations with the same schedule stand-in and RK4 scheme, run in Node.
- Machine: Apple M4 Pro, 12 cores, 24 GB, macOS 26.5.2, all runs single-threaded. Python 3.13.14 with numpy 2.5.4 and scipy 1.18.1; Pyodide Python 3.14.2 with numpy 2.4.6 and scipy 1.18.0; Node 24.18.0. Measured 2026-11-09.

Commands:

```
uv run --no-project --with "circadian==1.0.3" python scripts/bench_sim.py
node scripts/bench_sim.mjs
```

### 3.3 Results

Native Python, circadian 1.0.3:

| Model | Step | Work | Wall time | Per candidate |
|---|---|---|---|---|
| Forger99 | 0.1 h | one schedule: 3 burn-in loops, 14 days, markers | 0.32 s | |
| Forger99 | 0.1 h | 200 candidates, package `integrate` loop | 15.3 s | 76 ms |
| Forger99 | 0.1 h | 200 candidates, batched RK4 on package `derv` | 0.17 s | 0.9 ms |
| Forger99 | 1 min | one schedule | 1.78 s | |
| Forger99 | 1 min | 200 candidates, package loop (10 measured, extrapolated) | 91 s | 455 ms |
| Forger99 | 1 min | 200 candidates, batched | 1.02 s | 5.1 ms |
| Hannay19 | 0.1 h | one schedule | 0.52 s | |
| Hannay19 | 0.1 h | 200 candidates, package loop | 25.9 s | 130 ms |
| Hannay19 | 0.1 h | 200 candidates, batched | 0.44 s | 2.2 ms |
| Hannay19 | 1 min | 200 candidates, batched | 2.61 s | 13.0 ms |

Batched and package loops gave identical states (maximum absolute difference 0.0) for both models at both steps. CBTmin extraction for 200 candidates took 0.02 s or less. The package's `equilibrate` warned "did not equilibrate" after 3 loops, which supports the stricter convergence rule in 2.4.

Python in the browser (Pyodide 314.0.7 under Node, second run with packages cached):

| Work | Time |
|---|---|
| start the runtime | 0.86 s |
| load numpy, scipy, matplotlib, micropip | 1.01 s |
| install fastcore and circadian with micropip | 0.61 s |
| `import circadian.models` | 2.64 s |
| Forger99, 0.1 h, one schedule | 0.63 s |
| Forger99, 0.1 h, 200 candidates batched | 0.32 s (1.6 ms each) |
| Hannay19, 0.1 h, 200 candidates batched | 0.80 s (4.0 ms each) |
| download on first use: runtime 13 MB plus wheels 34 MB (scipy 14, matplotlib 7, pandas 4.2, numpy 3.0, stdlib 2.5) | about 47 MB |

States matched the package loop exactly here too.

JavaScript port of Forger99 (Node 24):

| Step | Work | Time |
|---|---|---|
| 0.1 h | one schedule | 3 ms |
| 0.1 h | 200 candidates | 41 ms (0.21 ms each) |
| 1 min | 200 candidates | 227 ms (1.14 ms each) |

Deployment footprint of the Python path: installing circadian 1.0.3 pulls numpy (24 MB), scipy (82 MB), pandas (52 MB), matplotlib (28 MB), fontTools (14 MB), Pillow (12 MB) and smaller packages, about 216 MB on macOS. `circadian/lights.py` imports matplotlib at module load, so it cannot be dropped without vendoring. The first import in a fresh environment took 27.9 s because matplotlib built its font cache and Python compiled bytecode; warm imports took 0.5 to 1.3 s.

### 3.4 Request budget

A plan request runs: Forger99 equilibration (6 loops of 14 days), the search (at most 1,260 candidates, section 4.4), ablations (about 6 candidates), and Hannay19 equilibration plus baseline and final plan. All at the 0.1 h step. Estimated from the measurements above on the development Mac:

| Part | Estimate |
|---|---|
| Forger99 equilibration, 6 loops | about 0.5 s |
| search, 1,260 candidates batched | about 1.1 s |
| ablations, one batch | under 0.05 s |
| Hannay19 equilibration and two runs | about 1.0 s |
| light profiles, scoring, rendering | under 0.2 s |
| total compute | about 2.8 s |

Serverless vCPUs are slower than an M4 Pro core; the Z11 deployment measures the real p95. Levers if it is too slow, in order: halve the restarts, run the Hannay19 cross-check only on request, shorten equilibration by starting from the previous loop's state.

The 1 min step stays in the test suite, not the request path: golden tests assert that CBTmin at 0.1 h is within 0.1 h of CBTmin at 1 min on every golden schedule (section 5). This changes the earlier plan in SCIENCE 1.7 and section 2.6, which put 1 min verification in the request path; at 13 ms per Hannay19 candidate and about 0.8 s per single 1 min run it would roughly double request time for a difference the tests already bound.

### 3.5 Options compared

| | (a) Python API, serverless | (b) Pyodide in the browser | (c) TypeScript port |
|---|---|---|---|
| Compute per request | about 2.8 s on the Mac; server estimate 4 to 6 s | about 1.8 times native for batched search; phone speed unmeasured | about 4 times faster than batched numpy for Forger99 |
| Start-up | cold start plus 0.5 to 1.3 s import; font cache needs a writable directory | about 5.1 s on the Mac before any work, every new page load without cache | none |
| Download or deploy size | about 216 MB of Python packages on the server | about 47 MB to each user on first use | small bundle |
| Copies of the science code | one, the published package | one, the published package | two; Forger99, Jewett99, Hannay19, sun times and the planner all ported and kept in parity |
| Privacy | schedule travels to the server for one request, not stored or logged | schedule never leaves the device | schedule never leaves the device |
| Fit with the stated stack | matches (Python core, FastAPI) | Python core reused, no FastAPI | replaces the Python core in production |

Serverless hosts for (a):

| | Vercel Python function | AWS Lambda |
|---|---|---|
| Package size | up to 5 GB per function on Fluid Compute [3.1] | 250 MB unzipped for zip packages including layers; 10 GB container images [3.2] |
| Fit with 216 MB of dependencies | fits as is | zip is at or past the limit once Linux BLAS libraries are added; needs a container image |
| Timeout | 300 s default [3.1] | up to 900 s [3.2] |
| Extra pieces | none; same project and domain as the web app | ECR image, Function URL or API Gateway, IAM role, CORS, a second deploy pipeline |

### 3.6 Decision

Run the Python core as a Vercel Python function in the same project as the web app (option a, confirming decision D3).

- The measured compute fits a single request once integration is batched, and the batched loop is exactly equal to the package's own loop, so the published code stays the only implementation of the science.
- Pyodide works and matches exactly, but asks every user to download about 47 MB and wait about 5 s before the first plan on a fast laptop; on a mid-range phone on mobile data that is not acceptable for v0.1.
- The TypeScript port is the fastest and the most private option, and is worth revisiting for an on-device mode after v0.1. For now it would double the science code that has to be proven correct, which works against the science-first rule.
- Lambda is not needed for v0.1: the dependencies need a container image there, and it adds an image registry, a URL front end, IAM, CORS and a second pipeline to save nothing that Vercel does not already give. The FastAPI app stays a plain ASGI app so that moving it to a Lambda container image behind a Function URL (arm64, with Mangum) is a one-file change if the Z11 measurements fail the 6 s target.

Settings that follow: `MPLBACKEND=Agg` and `MPLCONFIGDIR=/tmp/matplotlib` in the function environment; import the package lazily inside the adapter; record cold and warm p95 in docs/DECISIONS.md in Z11.

### 3.7 References

- [3.1] Vercel changelog, "Vercel Functions can now be up to 5 GB in package size", and Vercel Functions limits documentation (default timeout 300 s). https://vercel.com/changelog/vercel-functions-can-now-be-up-to-5-gb-in-package-size
- [3.2] AWS Lambda quotas: deployment package 250 MB unzipped including layers, container image 10 GB, timeout 900 s. https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html (values as documented; check at deployment)
- [3.3] Pyodide 314.0.7, npm package `pyodide`, released 2026-09-14. https://pyodide.org
