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
