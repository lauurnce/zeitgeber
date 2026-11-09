# Zeitgeber science specification

This document is the source of truth for every model, constant, light level and recommendation rule in Zeitgeber. Each section states its purpose, the equations, a parameter table with sources, valid ranges, limitations and references. Anything that could not be checked against a primary source is marked UNVERIFIED. Values marked "design" are Zeitgeber's own choices, not published findings.

Conventions:

- Time is in hours. Internal times are UTC; display times are Asia/Manila (UTC+8, no daylight saving time).
- Light is photopic illuminance at the eye in lux unless stated otherwise. The models in this document were fit to photopic lux and do not represent spectrum (see 3.4).
- CBTmin is the core body temperature minimum. DLMO is dim-light melatonin onset. Tmin is the Eastman group's name for the estimated CBTmin.
- Phase shifts are signed: negative is a delay (later), positive is an advance (earlier).
- "Package" means the Arcascope `circadian` package, version 1.0.3 (section 2). Where a paper is paywalled, the equations below were read from the package source code, which is open, and the paper is cited alongside.

## 1. Circadian pacemaker models

### 1.1 Purpose

Zeitgeber needs a model that takes a light history in lux and returns the phase of the human circadian pacemaker over time, so that CBTmin and DLMO can be predicted for a worker's schedule and for each candidate change to it. Three published light-driven models are candidates: Forger99, Jewett99 and Hannay19. All three are implemented in the package.

### 1.2 Common structure

All three models follow Kronauer, Forger and Jewett (1999) [1.4]: a light-processing stage ("Process L") converts illuminance into a drive on an oscillator ("Process P"). Process L has a state $n$, the fraction of photoreceptor elements that are "used", so that the drive saturates during long exposures and recovers in darkness:

$$
\dot{n} = 60\left[\alpha(I)\,(1-n) - \beta\, n\right]
$$

where $I$ is illuminance in lux, $\alpha(I)$ is the rate of activation (per minute; the factor 60 converts to per hour) and $\beta$ the recovery rate. The drive on the oscillator is

$$
\hat{B} = G\,\alpha(I)\,(1-n)\times m(\text{state})
$$

where $G$ is a gain and $m$ a model-specific modulation by the oscillator state that makes the response depend on circadian phase. Kronauer et al. report two time constants in Process L: 5 to 10 min for a bright pulse to reach full effect and 30 to 80 min of darkness tolerated between pulses without a large penalty [1.4]. This is why intermittent bright light works in the shift-work protocols of section 5.

### 1.3 Forger99 (Forger, Jewett and Kronauer 1999)

Equations as implemented in the package (`circadian/models.py`, class `Forger99`); the paper is paywalled and the equations were not checked against it (UNVERIFIED against the original text).

$$
\alpha(I) = \alpha_0 \left(\frac{I}{I_0}\right)^{p}, \qquad
\hat{B} = G\,\alpha(I)\,(1-n)\,(1-0.4x)\,(1-0.4x_c)
$$

$$
\dot{x} = \frac{\pi}{12}\left(x_c + \hat{B}\right)
$$

$$
\dot{x}_c = \frac{\pi}{12}\left[\mu\left(x_c - \tfrac{4}{3}x_c^{3}\right) - x\left(\left(\frac{24}{0.99669\,\tau_x}\right)^{2} + k\hat{B}\right)\right]
$$

$$
\dot{n} = 60\left[\alpha(I)(1-n) - \beta n\right]
$$

State: $x$, $x_c$ (oscillator), $n$ (Process L). Output: phase $\arg(x - i x_c)$, amplitude $\sqrt{x^2 + x_c^2}$.

| Symbol | Value | Unit | Source |
|---|---|---|---|
| $\tau_x$ | 24.2 | h | package default; Forger 1999 [1.1] |
| $\mu$ | 0.23 | 1 | package default; Forger 1999 [1.1] |
| $G$ | 33.75 | 1 | package default; Forger 1999 [1.1] |
| $\alpha_0$ | 0.05 | 1/min | package default; Forger 1999 [1.1] |
| $\beta$ | 0.0075 | 1/min | package default; Forger 1999 [1.1] |
| $p$ | 0.5 | 1 | package default; Forger 1999 [1.1] |
| $I_0$ | 9500 | lux | package default; Forger 1999 [1.1] |
| $k$ | 0.55 | 1 | package default; Forger 1999 [1.1] |
| period correction | 0.99669 | 1 | package code (the Jewett99 class uses 0.99729; which constant each paper uses is UNVERIFIED) |
| CBTmin | time of the minimum of $x$ | h | package convention (`cbt()`); the paper's convention is UNVERIFIED |
| DLMO | CBTmin minus 7.0 | h | package default `cbt_to_dlmo`; matches the 7 h used by Crowley et al. 2003 to estimate Tmin from DLMO [5.3] |

### 1.4 Jewett99 (Jewett, Forger and Kronauer 1999)

Equations as implemented in the package (class `Jewett99`); paper paywalled (UNVERIFIED against the original text). The abstract confirms three features that the code reproduces: a higher-order limit cycle, peak light sensitivity about 4 h before CBTmin, and CBTmin defined 0.8 h after the minimum of $x$ [1.2].

$$
\alpha(I) = \alpha_0 \left(\frac{I}{I_0}\right)^{p}, \qquad
\hat{B} = G\,\alpha(I)\,(1-n)\,(1-0.4x)\,(1-0.4x_c)
$$

$$
\dot{x} = \frac{\pi}{12}\left[x_c + \mu\left(\tfrac{1}{3}x + \tfrac{4}{3}x^{3} - \tfrac{256}{105}x^{7}\right) + \hat{B}\right]
$$

$$
\dot{x}_c = \frac{\pi}{12}\left[q\,\hat{B}\,x_c - x\left(\left(\frac{24}{0.99729\,\tau_x}\right)^{2} + k\hat{B}\right)\right]
$$

$$
\dot{n} = 60\left[\alpha(I)(1-n) - \beta n\right]
$$

| Symbol | Value | Unit | Source |
|---|---|---|---|
| $\tau_x$ | 24.2 | h | package default; Jewett 1999 [1.2] |
| $\mu$ | 0.13 | 1 | package default |
| $G$ | 19.875 | 1 | package default |
| $\beta$ | 0.013 | 1/min | package default |
| $k$ | 0.55 | 1 | package default |
| $q$ | 1/3 | 1 | package default |
| $I_0$ | 9500 | lux | package default |
| $p$ | 0.6 | 1 | package default |
| $\alpha_0$ | 0.16 | 1/min | package default |
| $\phi_{ref}$ | 0.8 | h | CBTmin = time of min $x$ + 0.8 h; package default, confirmed by the abstract [1.2] |
| DLMO | CBTmin minus 7.0 | h | package default |

### 1.5 Hannay19 (Hannay, Booth and Forger 2019)

A macroscopic model derived from a population of coupled oscillators. The state is the collective amplitude $R$ (0 = desynchronized, 1 = fully synchronized) and collective phase $\psi$, plus $n$. Equations as implemented in the package (class `Hannay19`); the paper is paywalled (UNVERIFIED against the original text). The derivation method for this model family is described openly in Hannay, Forger and Booth (2020) [1.5], which treats the mammalian case; the human parameter values below come from the package, which cites the 2019 paper.

$$
\alpha(I) = \alpha_0 \frac{I^{p}}{I^{p} + I_0}, \qquad \hat{B} = G\,\alpha(I)\,(1-n)
$$

$$
\dot{R} = -\gamma R + \frac{K}{2}\cos(\beta_1)\,R\,(1-R^{4})
+ \hat{B}\left[\frac{A_1}{2}(1-R^{4})\cos(\psi+\beta_{L1}) + \frac{A_2}{2}R\,(1-R^{8})\cos(2\psi+\beta_{L2})\right]
$$

$$
\dot{\psi} = \frac{2\pi}{\tau} + \frac{K}{2}\sin(\beta_1)\,(1+R^{4})
+ \hat{B}\left[\sigma - \frac{A_1}{2}\left(R^{3}+\frac{1}{R}\right)\sin(\psi+\beta_{L1}) - \frac{A_2}{2}(1+R^{8})\sin(2\psi+\beta_{L2})\right]
$$

$$
\dot{n} = 60\left[\alpha(I)(1-n) - \delta n\right]
$$

| Symbol | Value | Unit | Source |
|---|---|---|---|
| $\tau$ | 23.84 | h | package default; Hannay 2019 [1.3]. This is the period of the uncoupled population; the coupling term shifts the observed period (interpretation, UNVERIFIED) |
| $K$ | 0.06358 | 1/h | package default |
| $\gamma$ | 0.024 | 1/h | package default |
| $\beta_1$ | -0.09318 | rad | package default |
| $A_1$ | 0.3855 | 1 | package default |
| $A_2$ | 0.1977 | 1 | package default |
| $\beta_{L1}$ | -0.0026 | rad | package default |
| $\beta_{L2}$ | -0.957756 | rad | package default |
| $\sigma$ | 0.0400692 | 1 | package default |
| $G$ | 33.75 | 1 | package default |
| $\alpha_0$ | 0.05 | 1/min | package default |
| $\delta$ | 0.0075 | 1/min | package default |
| $p$ | 1.5 | 1 | package default |
| $I_0$ | 9325 | lux | package default |
| CBTmin | time when $\psi \equiv \pi \pmod{2\pi}$ | h | package convention (`cbt()`) |
| DLMO | CBTmin minus 7.0 | h | package default; the paper's own DLMO phase definition is UNVERIFIED |

The package also implements a two-population version, `Hannay19TP` (ventral and dorsal populations, 5 states, parameters $\tau_V$ 24.25, $\tau_D$ 24.0, couplings $K_{vv}$ 0.05, $K_{dd}$ 0.04, $K_{vd}$ 0.05, $K_{dv}$ 0.01). Zeitgeber does not use it in v0.1.

### 1.6 Getting CBTmin and DLMO from each model

| Model | CBTmin | DLMO | Notes |
|---|---|---|---|
| Forger99 | minimum of $x$ | CBTmin - 7 h | package convention; no reference-phase offset |
| Jewett99 | minimum of $x$ + 0.8 h | CBTmin - 7 h | offset confirmed by the paper's abstract [1.2] |
| Hannay19 | $\psi = \pi$ | CBTmin - 7 h | package convention |

The 7 h DLMO-to-CBTmin interval is the estimate the Eastman laboratory uses to derive Tmin from measured DLMO [5.3]. Because every DLMO here is CBTmin shifted by a constant, the two markers carry the same information in v0.1; DLMO is reported for readability, not as an independent estimate.

### 1.7 Valid ranges

- Illuminance: 0 to about 10,000 lux. The models were fit to the photopic range [1.4]; above $I_0$ the drive saturates, so values beyond 10,000 lux add little. Zeitgeber caps model input at 10,000 lux (design).
- Time step: the package integrates with fixed-step fourth-order Runge-Kutta and assumes constant light within a step. Zeitgeber uses 0.1 h (6 min) for planning and 1/60 h for verification (design; the package's own PRC code uses 0.10 h).
- $n \in [0, 1]$; $R \in (0, 1]$. The Hannay19 phase equation contains $1/R$ and is undefined at $R = 0$; Zeitgeber guards against $R$ below 0.05 (design).
- Burn-in: the package's `equilibrate` loops the schedule until the last DLMO moves by less than 0.001 h between loops, with a default of 10 loops. Zeitgeber uses at least 14 days of the current schedule as burn-in (design).

### 1.8 Limitations

- All three models were fit to laboratory data from healthy, mostly young adults under controlled light. None has been validated on Filipino shift workers or on self-reported light exposure.
- Input is photopic lux. Spectrum, and therefore melanopic effectiveness, is not represented (see 3.4).
- No chronotype, age or sleep-homeostatic effects. The Hilaire07 model in the package adds a non-photic (sleep-wake) input [1.6]; it is not used in v0.1.
- The CBTmin convention differs between Forger99 (no offset) and Jewett99 (0.8 h). A wrong convention shifts every recommendation by the same amount. Zeitgeber follows the package conventions and tests the entrainment relation in section 4.
- The DLMO is not independently modeled; it is CBTmin minus 7 h.

### 1.9 Recommendation

Default model: Forger99. Reasons: it has the fewest parameters, the original paper shows it predicts a three-pulse PRC experiment and an amplitude-reduction study as well as or better than the higher-order models [1.1], it is the model the package's PRC tools were built around, and its light stage is shared with Jewett99. Hannay19 runs alongside as a second opinion because it was fit to a larger library of experiments and its variables have a physiological reading [1.3]; when the two disagree by more than 1 h on CBTmin, the plan shows a range. Jewett99 stays available in the adapter for comparison.

### 1.10 References

- [1.1] Forger DB, Jewett ME, Kronauer RE (1999). A simpler model of the human circadian pacemaker. Journal of Biological Rhythms 14(6): 532-537. https://doi.org/10.1177/074873099129000867 (paywalled; equations read from the package code)
- [1.2] Jewett ME, Forger DB, Kronauer RE (1999). Revised limit cycle oscillator model of human circadian pacemaker. Journal of Biological Rhythms 14(6): 493-499. https://doi.org/10.1177/074873049901400608 (paywalled; abstract checked)
- [1.3] Hannay KM, Booth V, Forger DB (2019). Macroscopic models for human circadian rhythms. Journal of Biological Rhythms 34(6): 658-671. https://doi.org/10.1177/0748730419878298 (paywalled; equations read from the package code)
- [1.4] Kronauer RE, Forger DB, Jewett ME (1999). Quantifying human circadian pacemaker response to brief, extended, and repeated light stimuli over the phototopic range. Journal of Biological Rhythms 14(6): 500-515. https://doi.org/10.1177/074873099129001073 (paywalled; abstract checked)
- [1.5] Hannay KM, Forger DB, Booth V (2020). Seasonality and light phase-resetting in the mammalian circadian rhythm. Scientific Reports 10: 19506. https://doi.org/10.1038/s41598-020-74002-2 (open access)
- [1.6] St Hilaire MA, Klerman EB, Khalsa SBS, Wright KP, Czeisler CA, Kronauer RE (2007). Addition of a non-photic component to a light-based mathematical model of the human circadian pacemaker. Journal of Theoretical Biology 247(4): 583-599. https://doi.org/10.1016/j.jtbi.2007.04.001 (author manuscript PMC3123888)
- [1.7] Arcascope (2025). circadian, version 1.0.3, file circadian/models.py. https://github.com/Arcascope/circadian (open source; see section 2)

## 2. The circadian package

### 2.1 Purpose

Zeitgeber does not re-implement the models. It uses the open-source `circadian` package by Arcascope behind an adapter, so that the equations in section 1 run as published code and can be swapped or vendored later.

### 2.2 Identity and pin

| Item | Value | Source |
|---|---|---|
| Distribution name | `circadian` | PyPI JSON for 1.0.3 |
| Version pinned | 1.0.3 | released 2025-08-18 (sdist and wheel upload times on PyPI) |
| Requires Python | >= 3.7; classifiers list 3.7 to 3.10 only | PyPI metadata. Python 3.12 is untested by the authors; Zeitgeber runs an install and smoke test in Z4 |
| Dependencies | fastcore, pandas, numpy, scipy, matplotlib | PyPI `requires_dist` and `settings.ini` in the sdist |
| Repository | https://github.com/Arcascope/circadian, tag v1.0.3 | GitHub tags API |
| Software citation | Tavella F, Hannay K, Walch O (2023). Arcascope/circadian: Refactoring of readers and metrics modules. Zenodo, v1.0.2. https://doi.org/10.5281/zenodo.8206871 | package README |

Pin form: `circadian==1.0.3` with the lock file's hash. The adapter is the only module allowed to import it.

### 2.3 License

The release contradicts itself. The LICENSE file shipped inside the 1.0.3 sdist is the MIT License with the line "Copyright (c) [2023] [Kevin Hannay]" (brackets as in the file). The package metadata in the same sdist (PKG-INFO and settings.ini) declares "Apache Software License 2.0", and PyPI shows the Apache classifier. The GitHub repository sidebar reads MIT. Both licenses are permissive and compatible with Zeitgeber's MIT license. Zeitgeber's third-party notices will reproduce the MIT text from the LICENSE file and state that the metadata declares Apache 2.0. If the package is ever vendored, the same notice travels with the copied code. Resolving the contradiction with the maintainers is recorded as an open question in docs/DECISIONS.md.

### 2.4 Units and time step

- Time: hours, as a one-dimensional numpy array. The difference between consecutive entries is the integration step. `cbt()` reads the step from the first difference only, so the time grid must be uniform.
- Light: photopic lux, one value per time point, passed as the `input` array aligned to the time array. The integrator holds light constant within a step.
- Solver: fixed-step fourth-order Runge-Kutta (`step_rk4`). No adaptive stepping, no error control.
- Phase: radians from `np.angle`; amplitude dimensionless.
- Markers: times in the same hour units as the input time array. CBTmin candidates must be at least 13 h apart (`_min_marker_distance_in_hours`), and a warning is raised if two markers fall within 6 h.

### 2.5 API that Zeitgeber uses

Light schedules (`circadian.lights`):

- `LightSchedule(light, period=None)`: wraps a function from time in hours to lux, or a constant. `schedule(time_array)` returns a lux array.
- `LightSchedule.from_pulse(lux, start, duration, period=None, baseline=0.0)`: one pulse, optionally repeated.
- `LightSchedule.Regular(lux, lights_on, lights_off)`: a 24 h light-dark cycle.
- `LightSchedule.ShiftWork(lux, days_on, days_off, lights_on_workday, lights_off_workday, lights_on_day_off, lights_off_day_off)`: a built-in shift pattern with its own sleep assumptions. Zeitgeber does not use it; the light profile of section 3 is built as a function of time and wrapped in `LightSchedule`.
- Schedules support `+`, `-` and `concatenate_at(other, timepoint)`.

Models (`circadian.models`): `Forger99()`, `Jewett99()`, `Hannay19()`, `Hannay19TP()`, `Hilaire07()`, `Breslow13()`. Each accepts a `params` dict to override defaults. Methods:

- `model.integrate(time, initial_condition=None, input=light_array)` returns a `DynamicalTrajectory` with `.time` and `.states`; `model(time, ic, light)` is the same call.
- `model.equilibrate(time, input, num_loops=10)` integrates the schedule repeatedly, carrying the final state forward, and returns the final state. It warns if the last DLMO moved by more than 0.001 h between the last two loops.
- `model.cbt(trajectory=None)` returns CBTmin times; `model.dlmos(trajectory=None)` returns CBTmin minus `cbt_to_dlmo`.
- `model.phase(trajectory, time)` and `model.amplitude(trajectory, time)`.

Phase response tools (`circadian.prc`): `PhaseResponseCurveLight.light_khalsa(t, CR)` builds the light profile of the Khalsa et al. 2003 protocol as the package authors encoded it: 15 lux background and a 9985 lux pulse from CR + 12.65 h to CR + 19.35 h, that is 6.7 h long. `PRCFinder` contains the Type 0 protocol used for model fitting. Zeitgeber reuses `light_khalsa` for the tests in section 4.

### 2.6 Behavior to note

- `equilibrate` judges convergence by the last DLMO only. Zeitgeber additionally checks that the full set of daily CBTmin times changed by less than 0.05 h between the last two loops (design).
- Default initial conditions correspond to midnight on a 16 h light, 8 h dark schedule. Zeitgeber always equilibrates on the worker's current schedule before planning.
- Negative lux values produce a warning rather than an error; Zeitgeber validates inputs before calling the package.

### 2.7 Limitations

- Maintenance is thin: three releases in 2023, one in 2025, open issues and pull requests at the time of writing, and no Python 3.11 or later in the classifiers.
- No adaptive solver, so step size must be chosen by testing (section 1.7).
- Documentation and code disagree in places (the README refers to a `Light` class; the code has `LightSchedule`).

### 2.8 References

- [2.1] PyPI project page and JSON API for circadian 1.0.3. https://pypi.org/project/circadian/1.0.3/
- [2.2] Arcascope/circadian repository, tag v1.0.3. https://github.com/Arcascope/circadian
- [2.3] circadian-1.0.3.tar.gz: files LICENSE, PKG-INFO, settings.ini, circadian/models.py, circadian/lights.py, circadian/prc.py (read directly from the sdist)
