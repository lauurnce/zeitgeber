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
