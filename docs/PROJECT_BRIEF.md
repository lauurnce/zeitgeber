# Zeitgeber: project brief

Zeitgeber is a body-clock planner for night-shift workers. It estimates where a worker's circadian clock sits, scores how far that is from the work and sleep schedule, and plans light, sleep, nap and caffeine timing to close the gap.

## Problem

The human circadian clock is set mainly by light. Night work puts light at the wrong times. Bright daylight on the commute home signals morning to the body right before the worker tries to sleep, and the dim office at night withholds the signal that would help the clock adapt. Generic sleep advice ignores the exact shift, the commute, and the way rest days pull the schedule back toward daytime. The result is a clock that is misaligned with both work and sleep for most of the week.

## Users

Primary: Filipino BPO and IT-BPM agents on night or rotating shifts, most of them serving US time zones. The industry ended 2025 with about 1.9 million workers [1][2].

Secondary: BPO wellness and HR teams who want a planning tool they can offer to agents.

## Scope of v0.1

1. Schedule input: shift times per weekday, commute length and the share of it spent outdoors, rest-day habits, current sleep times, and location (Metro Manila by default).
2. Light-exposure profile: lux over time for 14 days, built from the schedule and from sunrise and sunset for the location and date.
3. Circadian simulation: peer-reviewed models through the open-source circadian package by Arcascope (Forger99, Jewett99, Hannay19), with estimates of the core body temperature minimum and, where the model supports it, dim-light melatonin onset.
4. Misalignment score: how far the simulated clock sits from the work and sleep schedule.
5. Plan: light-seeking windows, light avoidance (dark sunglasses on the commute home), a sleep window, a pre-shift nap and a caffeine cutoff, chosen to reduce misalignment within constraints from published shift-work strategies.
6. Output: a 14-day plan with a daily timeline, a calendar export (.ics) with reminders, and short nudges in English and Taglish. Nudges come from templates. Optional language-model wording may rephrase a template but cannot add numbers or claims that are not in the plan.
7. A web planner and a landing page.

## Non-goals for v0.1

- Diagnosing sleep disorders.
- Melatonin or medication advice.
- Wearable integration.
- User accounts.
- Keeping anyone's schedule on a server longer than one request.

## Success criteria

- The simulator reproduces the published shape of the human light phase response curve: light before the core body temperature minimum delays the clock, light after it advances the clock.
- Every recommendation explains itself: which model output it changes, and by how much.
- A pilot protocol for 10 to 15 agents, using the Karolinska Sleepiness Scale and a sleep diary, is ready to run.
- The landing page and README hold up for a chronobiologist and read clearly for an agent on a night shift.

## Framing

Zeitgeber is a wellness planning tool, not medical advice. People with sleep disorders, pregnancy or other health conditions should talk to a doctor. Schedules are processed for one request and are not stored.

## The name

Zeitgeber is German for "time giver": an external cue, sunlight above all, that sets the body clock. The physiologist Jürgen Aschoff used the word in the title of a 1954 paper in Naturwissenschaften [3] and brought it into the English-language literature in 1960 [4]. Aschoff and Rütger Wever of the Max Planck Institute for Behavioral Physiology then ran isolation experiments in a windowless bunker in Andechs, Bavaria, with Aschoff as the first subject [5]. Cut off from time cues, people's rhythms drifted to a period of about 25 hours [6][7]. Later forced-desynchrony work put the intrinsic human period closer to 24.2 hours [8]. Night-shift workers live with their Zeitgebers at the wrong times.

## Sources

1. Philstar, 1 January 2026. IT-BPM sector on track to hit $40 billion revenue goal. https://www.philstar.com/business/2026/01/01/2498004/it-bpm-sector-track-hit-40-billion-revenue-goal
2. Philstar, 29 January 2026. IT-BPM revenues breach $40 billion mark. https://www.philstar.com/business/2026/01/29/2504140/it-bpm-revenues-breach-40-billion-mark
3. Aschoff J (1954). Zeitgeber der tierischen Tagesperiodik. Naturwissenschaften 41: 49-56.
4. Aschoff J (1960). Exogenous and endogenous components in circadian rhythms. Cold Spring Harbor Symposia on Quantitative Biology 25: 11-28.
5. Wikipedia, "Jürgen Aschoff" and "Bunker experiment", accessed 9 November 2026. UNVERIFIED against a primary source. To be replaced with the Max Planck Society obituary or Wever's book when docs/SCIENCE.md is written.
6. Aschoff J (1965). Circadian rhythms in man. Science 148: 1427-1432.
7. Wever RA (1979). The Circadian System of Man: Results of Experiments Under Temporal Isolation. Springer.
8. Czeisler CA et al. (1999). Stability, precision, and near-24-hour period of the human circadian pacemaker. Science 284: 2177-2181.
