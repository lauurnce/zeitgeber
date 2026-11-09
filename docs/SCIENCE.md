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

## 3. Light levels

### 3.1 Purpose

The models take lux at the eye over time. Zeitgeber estimates it from the schedule by assigning each block of the day to a light environment with a constant lux value. This section collects measured values for those environments and fixes the v0.1 constants.

### 3.2 Measured and published values

| Environment | Value | Source | Status |
|---|---|---|---|
| Direct sunlight, clear sky | about 100,000 lux | general photometric references | UNVERIFIED against a primary measurement; not measured in Manila |
| Daylight, not in direct sun (open shade) | 10,000 to 25,000 lux | general photometric references | UNVERIFIED |
| Overcast day | 1,000 to 10,000 lux; sources disagree widely | general photometric references | UNVERIFIED |
| Natural light, wrist-worn, average over waking hours (summer camping, Colorado) | 4,487 (SD 552) lux; first 2 h after waking 3,074 (SD 1,035) lux | Wright et al. 2013 [3.1] | cited |
| Electric-lit constructed environment, same subjects, average over waking hours | 979 (SD 352) lux; first 2 h after waking 934 (SD 867) lux | Wright et al. 2013 [3.1] | cited |
| Call-center floor, 53 spot measurements, horizontal at work surfaces (California, 2012) | mean 50.7 footcandles, about 546 lux (conversion 1 fc = 10.764 lux is ours) | NIOSH 2013 [3.2] | cited |
| Recommended office task lighting | ANSI/IESNA 2004: 30 to 100 fc (about 320 to 1,080 lux) for visual tasks; OSHA eTool: 20 to 73 fc (about 215 to 785 lux) for computer workstations | as quoted in NIOSH 2013 [3.2] | cited via secondary |
| "Normal room light" | about 200 to 300 lux | Smith and Eastman 2012 [3.3] | cited |
| Laboratory "room light" in the hours before bed | under 200 lux at the ceiling setting; typically 60 to 130 lux at the eye | Gooley et al. 2011 [3.4] | cited |
| Laboratory night-shift control "dim light" | about 150 lux | Crowley et al. 2003 [3.5] | cited |
| Home lighting in the 4 h before bed | maximized about 65 lux; minimized about 3 lux | Burgess and Molina 2014 [3.6] | cited |
| Light-emitting eReader at maximum brightness, 38 to 40 cm, measured at the eye | 31.73 lux; printed book in the same dim room 0.91 lux; ambient about 3 lux | Chang et al. 2015 [3.7] | cited |
| Phone screen at typical distance | not found | | UNVERIFIED; the eReader value is used as a proxy |
| Bright-light box, 3 h at habitual bedtime | about 3,000 lux (about 7 W/m2) | Burke et al. 2015 [3.8] | cited |
| Intermittent bright light during simulated night shifts | about 5,000 lux, 20 min on and 40 min off, 4 to 5 pulses per night | Crowley et al. 2003 [3.5] | cited |
| Constant routine dim light | 2 to 7 lux (Khalsa) ; under 3 lux (St Hilaire) | Khalsa et al. 2003 [4.1]; St Hilaire et al. 2012 [4.2] | cited |
| Dark bedroom for day sleep | "very dark bedroom"; no lux stated | Smith and Eastman 2012 [3.3] | design value 1 lux |
| Outdoor street at night, Metro Manila | not found | | UNVERIFIED; design value 10 lux |

### 3.3 Eyewear

| Eyewear | Transmission | Source | Status |
|---|---|---|---|
| "Normal" sunglasses used in night-shift trials | 15% visible light transmission | Crowley et al. 2003 [3.5]; Smith and Eastman 2012 [3.3] | cited |
| "Dark" sunglasses used in night-shift trials | 2% transmission | Crowley et al. 2003 [3.5] | cited |
| Sunglass filter category 3 (general purpose dark) | 8% to 18% luminous transmittance | ISO 12312-1 as summarized by secondary sources | UNVERIFIED against the standard text |
| Sunglass filter category 4 (very dark) | 3% to 8%; not suitable for driving | ISO 12312-1 as summarized by secondary sources | UNVERIFIED against the standard text |
| Blue-blocking (orange) lenses | passed the same 1,300 lux as grey control lenses in the test; grey lenses allowed 46% melatonin suppression, orange lenses 6% (not significant) | Sasseville et al. 2006 [3.9] | cited; photopic transmittance of consumer amber lenses UNVERIFIED |

### 3.4 Photopic lux versus melanopic light

The models in section 1 accept photopic lux. The circadian system is most sensitive near 480 nm [3.10], so two sources with equal lux can have different circadian effect. Orange lenses are the clearest case: they do not change lux much yet block most of the circadian effect [3.9]. Lux-based models therefore cannot represent blue-blocking lenses, and Zeitgeber v0.1 does not model them (design; see docs/DECISIONS.md). Dark sunglasses reduce light across the spectrum and are modeled as a transmission factor on outdoor lux.

### 3.5 Zeitgeber v0.1 constants (design)

| Environment | Constant | Basis |
|---|---|---|
| Outdoors, sun up, open | 10,000 lux | model saturation cap (1.7); the Khalsa stimulus level [4.1]; real daylight is higher but adds little drive |
| Outdoors, sun up, shade or inside a vehicle | 1,000 lux | order of magnitude from the shade range above; UNVERIFIED |
| Outdoors with dark sunglasses | outdoor value times 0.15 (category 3) or 0.02 (very dark) | Crowley et al. 2003 [3.5] |
| Call-center floor or office | 500 lux | NIOSH mean 546 lux [3.2]; "normal room light" 200 to 300 lux [3.3] is the lower bound |
| Home, awake, lights on | 100 lux | between Burgess and Molina's 65 lux maximum [3.6] and Gooley's 60 to 130 lux at the eye [3.4] |
| Home, awake, lights low, phone in hand | 30 lux | Chang et al. 2015 eReader at the eye [3.7] |
| Sleep in a dark room | 1 lux | design; Burgess and Molina minimized to about 3 lux [3.6] |
| Outdoors at night, street | 10 lux | UNVERIFIED |

Every constant is a named parameter. The sensitivity test in Z7 scales each by 0.3 and 3 and reports whether the plan changes.

### 3.6 Limitations

- No value in this section was measured in Metro Manila or in a Philippine call center. The pilot (section 8) includes a lux meter reading at each participant's workstation and on the commute.
- Photopic lux understates the circadian effect of daylight relative to warm indoor light and overstates it for orange-tinted light.
- Commute light depends on vehicle, seat, window tint and weather, none of which v0.1 models beyond "outdoor share of the commute".

### 3.7 References

- [3.1] Wright KP, McHill AW, Birks BR, Griffin BR, Rusterholz T, Chinoy ED (2013). Entrainment of the human circadian clock to the natural light-dark cycle. Current Biology 23(16): 1554-1558. https://doi.org/10.1016/j.cub.2013.06.039 (author manuscript PMC4020279)
- [3.2] NIOSH (2013). Lighting, Indoor Environmental Quality Concerns, and Job Stress at a Call Center, California. Health Hazard Evaluation Report 2012-0081-3169. https://doi.org/10.26616/NIOSHHETA201200813169
- [3.3] Smith MR, Eastman CI (2012). Shift work: health, performance and safety problems, traditional countermeasures, and innovative management strategies to reduce circadian misalignment. Nature and Science of Sleep 4: 111-132. https://doi.org/10.2147/NSS.S10372 (open access)
- [3.4] Gooley JJ, Chamberlain K, Smith KA, et al. (2011). Exposure to room light before bedtime suppresses melatonin onset and shortens melatonin duration in humans. Journal of Clinical Endocrinology and Metabolism 96(3): E463-E472. https://doi.org/10.1210/jc.2010-2098 (PMC3047226)
- [3.5] Crowley SJ, Lee C, Tseng CY, Fogg LF, Eastman CI (2003). Combinations of bright light, scheduled dark, sunglasses, and melatonin to facilitate circadian entrainment to night shift work. Journal of Biological Rhythms 18(6): 513-523. https://doi.org/10.1177/0748730403258422 (abstract checked)
- [3.6] Burgess HJ, Molina TA (2014). Home lighting before usual bedtime impacts circadian timing: a field study. Photochemistry and Photobiology 90(3): 723-726. https://doi.org/10.1111/php.12241 (PMC4053688)
- [3.7] Chang AM, Aeschbach D, Duffy JF, Czeisler CA (2015). Evening use of light-emitting eReaders negatively affects sleep, circadian timing, and next-morning alertness. PNAS 112(4): 1232-1237. https://doi.org/10.1073/pnas.1418490112 (PMC4313820)
- [3.8] Burke TM, Markwald RR, McHill AW, et al. (2015). Effects of caffeine on the human circadian clock in vivo and in vitro. Science Translational Medicine 7(305): 305ra146. https://doi.org/10.1126/scitranslmed.aac5125 (PMC4657156)
- [3.9] Sasseville A, Paquet N, Sevigny J, Hebert M (2006). Blue blocker glasses impede the capacity of bright light to suppress melatonin production. Journal of Pineal Research 41(1): 73-78. https://doi.org/10.1111/j.1600-079X.2006.00332.x (abstract checked)
- [3.10] Thorne HC, Jones KH, Peters SP, Archer SN, Dijk DJ (2009). Daily and seasonal variation in the spectral composition of light exposure in humans. Chronobiology International 26(5): 854-866. https://doi.org/10.1080/07420520903044315 (abstract checked)
- [3.11] ISO 12312-1, Eye and face protection, Sunglasses and related eyewear, Part 1: Sunglasses for general use. Standard text not accessed; category bands taken from secondary summaries. UNVERIFIED

## 4. Phase response to light

### 4.1 Purpose

The first success criterion is that the simulator reproduces the published shape of the human phase response curve (PRC) to bright light. This section records the published features and the tolerances Zeitgeber will test against.

### 4.2 Published findings

Khalsa et al. 2003 [4.1], read from the abstract (full text paywalled):

- 21 healthy entrained subjects; constant routines in 2 to 7 lux before and after the stimulus.
- Stimulus: 6.7 h of bright light alternating 6 min of fixed gaze at about 10,000 lux with free gaze at about 5,000 to 9,000 lux, scheduled at different circadian phases across subjects.
- Phase measured from plasma melatonin (onset, offset, midpoint).
- Result: a Type 1 PRC with peak-to-trough amplitude of 5.02 h for the melatonin midpoint. Delays when the stimulus was centered before the critical phase at CBTmin, advances when centered after it, no shift at the critical phase. No prolonged dead zone during the subjective day.
- The maximum delay and maximum advance taken separately are not in the abstract. UNVERIFIED until the full text is read.

St Hilaire et al. 2012 [4.2], abstract:

- 1 h of bright white light (about 8,000 lux), 18 subjects at 18 circadian phases, constant routines in under 3 lux.
- Result: a Type 1 PRC with fitted peak-to-trough amplitude of 2.20 h, about 40% of the 6.7 h PRC amplitude from 15% of the exposure duration. A dim-light control (under 3 lux) showed no discernible PRC.

Burke et al. 2015 [4.3], full text: 3 h of about 3,000 lux starting at habitual bedtime delayed the melatonin rhythm by about 85 min relative to a dim-light placebo.

Entrainment anchors used as checks:

- Under electric lighting, melatonin onset occurred about 2 h before sleep start; under natural light only, melatonin onset moved to near sunset and offset to before wake time just after sunrise (Wright et al. 2013 [3.1]).
- CBTmin "is usually a few hours before waking" (Smith and Eastman 2012 [3.3]); the circadian crest of REM sleep sits shortly after CBTmin and the phase relation between sleep and the pacemaker promotes consolidated sleep (Dijk and Czeisler 1995 [4.4]).
- The intrinsic period of the human pacemaker averages 24.18 h under forced desynchrony (Czeisler et al. 1999 [4.5]).

### 4.3 Features to reproduce and tolerances

Simulated protocol: equilibrate the model on a 16 h light (150 lux) and 8 h dark cycle, then run the Khalsa light profile from the package (`light_khalsa`, 15 lux background, 9,985 lux pulse of 6.7 h) with the pulse centered at each of 24 phases relative to the pre-stimulus CBTmin, and compare CBTmin (or DLMO) before and after. Tolerances are Zeitgeber's design choices unless marked otherwise.

| ID | Feature | Published value | Test tolerance | Status |
|---|---|---|---|---|
| F1 | Sign of shift | pulses centered before CBTmin delay, after CBTmin advance [4.1] | pulses centered 2 h or more before CBTmin must delay; 2 h or more after must advance; no tolerance | cited |
| F2 | Crossover | zero shift at CBTmin [4.1] | fitted zero crossing within 1.5 h of CBTmin | design tolerance |
| F3 | 6.7 h pulse amplitude | peak-to-trough 5.02 h (melatonin midpoint) [4.1] | 5.0 h, tolerance 1.5 h | design tolerance |
| F4 | 1 h pulse amplitude | peak-to-trough 2.20 h at about 8,000 lux [4.2] | 2.2 h, tolerance 1.0 h | design tolerance |
| F5 | Duration non-linearity | F4 is about 40% of F3 [4.2] | ratio between 0.25 and 0.60 | design tolerance |
| F6 | No dead zone | no prolonged insensitivity in the subjective day [4.1] | no run of 4 consecutive hourly pulse centers with shift smaller than 0.3 h | design |
| F7 | Evening 3 h at 3,000 lux | about 85 min delay [4.3] | delay between 45 and 125 min | design tolerance |
| F8 | Free-running period in under 3 lux | 24.18 h [4.5] | Forger99 and Jewett99: 24.2 h, tolerance 0.3 h; Hannay19: report value, tolerance 0.5 h | design tolerance |
| F9 | Entrained phase angle | CBTmin a few hours before wake [3.3][4.4]; DLMO about 2 h before sleep start [3.1] | on a 16L:8D 150 lux cycle: CBTmin 1 to 4 h before lights-on; DLMO 1 to 3.5 h before lights-off | design tolerance |

Each feature is one pytest case. F1 and F2 are blocking: a model that fails them is not used. F3 to F9 are reported with the measured value so that drift in the dependency is visible.

### 4.4 Limitations

- Khalsa's phase reference is the melatonin midpoint; the models report CBTmin (or DLMO as CBTmin minus 7 h). The test compares shapes and amplitudes, not absolute phases, which is why F2 carries a 1.5 h tolerance.
- The maxima of delays and advances in Khalsa 2003 are UNVERIFIED pending the full text; F3 uses the peak-to-trough value, which is in the abstract.
- PRCs were measured in dim-light constant routines. Real workers carry a light history that changes sensitivity; the model handles this only through Process L.

### 4.5 References

- [4.1] Khalsa SBS, Jewett ME, Cajochen C, Czeisler CA (2003). A phase response curve to single bright light pulses in human subjects. Journal of Physiology 549(3): 945-952. https://doi.org/10.1113/jphysiol.2003.040477 (abstract checked; full text not accessible)
- [4.2] St Hilaire MA, Gooley JJ, Khalsa SBS, Kronauer RE, Czeisler CA, Lockley SW (2012). Human phase response curve to a 1 h pulse of bright white light. Journal of Physiology 590(13): 3035-3045. https://doi.org/10.1113/jphysiol.2012.227892 (abstract checked)
- [4.3] Burke TM et al. (2015). See [3.8].
- [4.4] Dijk DJ, Czeisler CA (1995). Contribution of the circadian pacemaker and the sleep homeostat to sleep propensity, sleep structure, electroencephalographic slow waves, and sleep spindle activity in humans. Journal of Neuroscience 15(5): 3526-3538. https://doi.org/10.1523/JNEUROSCI.15-05-03526.1995 (PMC6578184)
- [4.5] Czeisler CA, Duffy JF, Shanahan TL, et al. (1999). Stability, precision, and near-24-hour period of the human circadian pacemaker. Science 284(5423): 2177-2181. https://doi.org/10.1126/science.284.5423.2177 (abstract checked)

## 5. Shift-work strategies and planner rules

### 5.1 Purpose

The planner's actions and constraints come from the Eastman laboratory's night-work protocols, which produced a "compromise" circadian phase in the laboratory and in simulated-night-shift field conditions. This section states what those studies did and turns them into explicit rules.

### 5.2 Published findings

Crowley et al. 2003 [3.5] (abstract): 67 young participants, 5 simulated night shifts 23:00 to 07:00, home sleep 08:30 to 15:30 in darkened bedrooms. Sunglasses with 15% or 2% transmission outdoors by day. Intermittent bright light during shifts (about 5,000 lux, 20 min on, 40 min off, 4 to 5 pulses per night, in a moving delaying pattern) versus about 150 lux. Tmin estimated as DLMO + 7 h. Re-entrainment categories: not re-entrained (Tmin before the day sleep period), partially (Tmin in the first half of sleep), completely (Tmin in the second half). With bright light during the shift almost all "earlier" participants reached complete re-entrainment.

Smith and Eastman 2008 [5.1] (abstract): 24 subjects, 3 night shifts, 2 days off, 4 night shifts. Experimental group: five 15-min bright-light pulses per night shift from light boxes, dark sunglasses outdoors, scheduled sleep in dark bedrooms after shifts and on days off, and 15 min of outdoor afternoon light within 2 h of wake (the "light brake"). Final DLMO about 04:30 versus 00:30 in controls; the target was a compromise position with DLMO near 03:00. Experimental subjects performed almost as well at night as at daytime baseline and slept nearly all of the allotted time.

Smith, Fogg and Eastman 2009 [5.2] (abstract): same intervention family. Partially and completely re-entrained subjects had markedly better mood, fatigue and performance than non-re-entrained subjects, and the two re-entrained groups were similar to each other. Partial re-entrainment is enough.

Smith and Eastman 2012 [3.3] (full text): the plan is to shift the clock part way so that Tmin falls within sleep both after night shifts and on days off, using a strong shifted light-dark cycle (sleep in a very dark bedroom), sunglasses of about 15% transmission on the way home, a little bright light during the night shift, and the afternoon light brake to stop the clock from delaying too far. The review notes that the longest, most efficient sleep occurs around Tmin, and that caffeine and naps give symptomatic relief without fixing misalignment.

Sasseville et al. 2006 [3.9]: dark goggles help adjustment to night work but are incompatible with driving. ISO filter category 4 (3% to 8%) is described by secondary sources as unsuitable for driving (UNVERIFIED against the standard).

### 5.3 Planner target

Compromise phase position (decision D1): the predicted Tmin must fall inside the day-sleep window after each night shift and inside the sleep window on rest days. In the Eastman studies this corresponds to a DLMO near 03:00 and Tmin near 10:00 for 23:00 to 07:00 shifts with sleep from about 08:30 [5.1][3.3]. Zeitgeber computes the target from the worker's own windows rather than fixing clock times (design).

### 5.4 Rules

| ID | Rule | Basis | Status |
|---|---|---|---|
| R1 | Bright light early in the shift: the planner may place a light-seeking window (target 1,000 lux or more, for example a light box or a brightly lit break area) in the part of the shift that precedes predicted CBTmin, ending at least 2 h before CBTmin. Intermittent exposure of 15 to 20 min blocks counts; 500 lux floor lighting alone does not. | Crowley 2003 [3.5]; Smith 2008 [5.1]; Process L time constants [1.4] | cited; the 2 h margin and 1,000 lux threshold are design |
| R2 | Dark sunglasses on the commute home whenever the sun is above the horizon, from leaving the building until indoors. Default transmission 15%. Recommend 2% lenses only when the worker is not driving or riding a motorcycle. | Crowley 2003 [3.5]; Smith 2008 [5.1]; Smith and Eastman 2012 [3.3]; driving caveat from Sasseville 2006 [3.9] | cited; driving rule is design |
| R3 | Sleep in a very dark room starting within 1.5 h of arriving home, at a fixed time on every workday, with a window of at least 7 h. | Crowley 2003 sleep 08:30 to 15:30 [3.5]; Smith and Eastman 2012 [3.3] | cited; 1.5 h and 7 h are design |
| R4 | Rest-day sleep is a late window, not a flip to a normal night: default 03:00 to 11:00, adjusted so that predicted Tmin stays inside it. | Smith 2008 "adequate late night sleep on days off" [5.1]; Smith and Eastman 2012 [3.3] | cited; default hours are design |
| R5 | Light brake: 15 min outdoors within 2 h of waking from day sleep, to stop the clock delaying past the target. | Smith 2008 [5.1]; Smith and Eastman 2012 [3.3] | cited |
| R6 | No bright light in the 2 h before the planned sleep window other than what R2 already limits; phone use in a dark room counts as 30 lux (3.5). | Gooley 2011 [3.4]; Burgess and Molina 2014 [3.6]; Chang 2015 [3.7] | cited for effect; 2 h is design |
| R7 | Never recommend looking at the sun, light above 10,000 lux, or eyewear darker than category 3 for anyone who drives. | safety; ISO category guidance (UNVERIFIED) | design |

### 5.5 Limitations

- The protocols were run on young healthy volunteers with simulated night shifts and controlled home sleep; the field conditions of Metro Manila commutes are different.
- The studies tested fixed 23:00 to 07:00 shifts and 2-day weekends. Rotations and split rest days are untested.
- Light boxes were used for R1; most call centers do not have them. The planner should mark R1 as "if available".
- Partial re-entrainment reduced impairment in the laboratory; the size of the benefit in real workplaces is not established.

### 5.6 References

- [5.1] Smith MR, Eastman CI (2008). Night shift performance is improved by a compromise circadian phase position: study 3. Circadian phase after 7 night shifts with an intervening weekend off. Sleep 31(12): 1639-1645. https://doi.org/10.1093/sleep/31.12.1639 (PMC2603486; abstract checked)
- [5.2] Smith MR, Fogg LF, Eastman CI (2009). A compromise circadian phase position for permanent night work improves mood, fatigue, and performance. Sleep 32(11): 1481-1489. https://doi.org/10.1093/sleep/32.11.1481 (PMC2768954; abstract checked)
- [5.3] Crowley SJ et al. (2003). See [3.5].
- [5.4] Smith MR, Eastman CI (2012). See [3.3].

## 6. Caffeine and naps

### 6.1 Purpose

Caffeine and naps are alertness countermeasures, not clock shifters. Zeitgeber includes a caffeine cutoff and a pre-shift nap because both protect the day-sleep window and night-shift alertness, and because workers already use them. This section fixes the numbers behind those rules.

### 6.2 Published findings

Caffeine pharmacokinetics:

- Half-life in healthy adults is commonly summarized as about 5 h with a wide range, roughly 1.5 to 9.5 h. This summary comes from secondary coverage of the Institute of Medicine 2001 report [6.1]; the primary text could not be accessed. UNVERIFIED.
- Smoking increases caffeine clearance and shortens its half-life; oral contraceptive use has the opposite effect over a wide dose range (Grzegorzewski et al. 2021, systematic analysis of 141 publications [6.2]).
- Pharmacokinetics are also affected by age, sex and hormones, liver disease, obesity and diet, with CYP1A2 metabolizing about 95% of ingested caffeine (Nehlig 2018 [6.3], abstract). Pregnancy prolongs half-life (commonly stated; UNVERIFIED here).

Caffeine and sleep (Drake et al. 2013 [6.4], abstract): 400 mg taken at bedtime, 3 h before bedtime or 6 h before bedtime each significantly disturbed sleep relative to placebo, measured by diary and a portable monitor at home. The authors conclude that caffeine should be avoided for a minimum of 6 h before bedtime. The size of the total sleep time reduction at 6 h is not in the abstract (UNVERIFIED).

Caffeine and the clock (Burke et al. 2015 [3.8], full text): 2.9 mg/kg, equivalent to 200 mg in a 69 kg person, taken 3 h before habitual bedtime in dim light delayed the melatonin rhythm by about 40 min compared with placebo; 3 h of about 3,000 lux at bedtime delayed it by about 85 min; both together by about 105 min.

Naps:

- Ruggiero and Redeker 2014 [6.5] (systematic review of 13 studies, full text): naps of 20 to 40 min between 02:00 and 03:00 during night shifts improved sleepiness, reaction time and lapses through the end of the shift; naps as short as 20 min helped; 60 and 120 min naps at 00:00 did not improve reaction time in one study; sleep inertia of about 20 to 30 min followed naps.
- Sallinen et al. 1998 [6.6] (abstract): 30 or 50 min naps at 01:00 or 04:00 improved responses in the second half of the shift; inertia lasted about 10 to 15 min; 50 min naps slightly impaired the following day sleep.
- Schweitzer et al. 2006 [6.7] (abstract): an evening nap before the first two of four night shifts plus caffeine improved alertness and performance in the laboratory and in 53 real shift workers; the combination beat either alone.
- Garbarino et al. 2004 [6.8] (abstract): in Italian shift-working police drivers, a model of accident risk versus sleep pressure estimated about 38% more accidents if prophylactic naps were omitted.
- Smith and Eastman 2012 [3.3]: naps improve alertness but do not remove the decrement at the circadian nadir.

### 6.3 Rules

| ID | Rule | Basis | Status |
|---|---|---|---|
| C1 | Caffeine cutoff: no caffeine in the 6 h before the planned sleep window. The plan prints the clock time. | Drake 2013 [6.4] | cited |
| C2 | If the worker reports oral contraceptive use or another reason to expect slow clearance, the cutoff extends to 8 h. | direction from Grzegorzewski 2021 [6.2]; the 8 h figure is design | design |
| C3 | Caffeine is allowed in the first half of the shift; pairing it with a pre-shift nap is suggested. | Schweitzer 2006 [6.7] | cited |
| C4 | Zeitgeber v0.1 does not model caffeine's effect on circadian phase. | Burke 2015 shows a 40 min delay from one evening dose [3.8]; too small and too variable to plan on | design |
| N1 | Pre-shift nap: an opportunity of 30 to 90 min, placed 2 to 4 h before the shift start and ending at least 30 min before leaving home, so that sleep inertia clears. | Schweitzer 2006 [6.7]; Garbarino 2004 [6.8]; inertia 10 to 30 min [6.5][6.6] | cited; the window and 30 min margin are design |
| N2 | In-shift nap: if the employer allows, 20 to 30 min between about 02:00 and 03:00 shift time. Shown as a note, not planned. | Ruggiero and Redeker 2014 [6.5] | cited |
| N3 | Nap blocks count as dark (1 lux) in the light profile. | eyes closed in a dark room | design |

### 6.4 Limitations

- Half-life numbers are UNVERIFIED pending the primary text; the rules rest on Drake 2013's direct 6 h finding, not on half-life arithmetic.
- Dose matters and v0.1 does not ask for it. Drake used 400 mg; a typical cup contains far less (amount UNVERIFIED here).
- Nap evidence is from small, mixed-design studies and none measured workplace safety outcomes [6.5].
- Caffeine advice must stay generic. Pregnancy and health conditions are referred to a doctor, per the wellness framing.

### 6.5 References

- [6.1] Institute of Medicine (2001). Caffeine for the Sustainment of Mental Task Performance: Formulations for Military Operations. National Academies Press. Chapter 2, Pharmacology of Caffeine. https://www.ncbi.nlm.nih.gov/books/NBK223808/ (text not accessible at the time of writing; UNVERIFIED)
- [6.2] Grzegorzewski J, Bartsch F, Koller A, Konig M (2021). Pharmacokinetics of caffeine: a systematic analysis of reported data for application in metabolic phenotyping and liver function testing. Frontiers in Pharmacology 12: 752826. https://doi.org/10.3389/fphar.2021.752826 (open access, PMC8914174)
- [6.3] Nehlig A (2018). Interindividual differences in caffeine metabolism and factors driving caffeine consumption. Pharmacological Reviews 70(2): 384-411. https://doi.org/10.1124/pr.117.014407 (abstract checked)
- [6.4] Drake C, Roehrs T, Shambroom J, Roth T (2013). Caffeine effects on sleep taken 0, 3, or 6 hours before going to bed. Journal of Clinical Sleep Medicine 9(11): 1195-1200. https://doi.org/10.5664/jcsm.3170 (PMC3805807; abstract checked)
- [6.5] Ruggiero JS, Redeker NS (2014). Effects of napping on sleepiness and sleep-related performance deficits in night-shift workers: a systematic review. Biological Research for Nursing 16(2): 134-142. https://doi.org/10.1177/1099800413476571 (PMC4079545; full text read)
- [6.6] Sallinen M, Harma M, Akerstedt T, Rosa R, Lillqvist O (1998). Promoting alertness with a short nap during a night shift. Journal of Sleep Research 7(4): 240-247. https://doi.org/10.1046/j.1365-2869.1998.00121.x (abstract checked)
- [6.7] Schweitzer PK, Randazzo AC, Stone K, Erman M, Walsh JK (2006). Laboratory and field studies of naps and caffeine as practical countermeasures for sleep-wake problems associated with night work. Sleep 29(1): 39-50. https://doi.org/10.1093/sleep/29.1.39 (abstract checked)
- [6.8] Garbarino S, Mascialino B, Penco MA, et al. (2004). Professional shift-work drivers who adopt prophylactic naps can reduce the risk of car accidents during night work. Sleep 27(7): 1295-1302. https://doi.org/10.1093/sleep/27.7.1295 (abstract checked)
