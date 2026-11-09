"""Benchmark 14-day circadian simulations for the Zeitgeber runtime decision.

Measures, on this machine, how long it takes to simulate one schedule and
200 candidate plans with the Arcascope circadian package (pinned 1.0.3):

1. the package's own ``integrate`` loop, one candidate at a time;
2. a batched fourth-order Runge-Kutta loop that calls the package's ``derv``
   for all candidates at once (the equations stay in the package).

Run without installing anything into the project:

    uv run --no-project --with "circadian==1.0.3" python scripts/bench_sim.py

The light profile here is a deliberately simple stand-in for the real
builder (docs/SCIENCE.md section 3): a 22:00 to 07:00 shift Monday to Friday,
a 90 min commute home with 40 min outdoors, day sleep, and weekend sleep.
"""

from __future__ import annotations

import argparse
import platform
import sys
import time

import numpy as np

HOURS_PER_DAY = 24.0


def light_profile(
    dt: float,
    days: int,
    sleep_start: float = 9.0,
    sleep_len: float = 6.0,
    sunglasses: float = 1.0,
    light_seek: bool = False,
    rest_sleep_start: float = 23.0,
) -> np.ndarray:
    """Lux over a uniform grid in hours, starting Monday 00:00 (day 0)."""
    t = np.arange(0.0, days * HOURS_PER_DAY, dt)
    hod = np.mod(t, HOURS_PER_DAY)
    dow = np.mod(np.floor(t / HOURS_PER_DAY), 7)  # 0 = Monday
    lux = np.full(t.shape, 100.0)  # home, lights on
    shift_eve = (hod >= 22.0) & (dow <= 4)  # Mon to Fri evenings
    shift_morn = (hod < 7.0) & (dow >= 1) & (dow <= 5)  # Tue to Sat mornings
    lux[shift_eve | shift_morn] = 500.0
    if light_seek:  # one hour of 1000 lux early in the shift
        lux[shift_eve & (hod >= 23.0)] = 1000.0
    after_shift = (dow >= 1) & (dow <= 5)
    lux[after_shift & (hod >= 7.0) & (hod < 7.0 + 40.0 / 60.0)] = 10000.0 * sunglasses
    lux[after_shift & (hod >= 7.0 + 40.0 / 60.0) & (hod < 8.5)] = 1000.0 * sunglasses
    lux[after_shift & (hod >= sleep_start) & (hod < sleep_start + sleep_len)] = 1.0
    rest_night = (dow == 5) | (dow == 6)
    rest_len = 8.0
    end = rest_sleep_start + rest_len
    if end <= HOURS_PER_DAY:
        lux[rest_night & (hod >= rest_sleep_start) & (hod < end)] = 1.0
    else:
        lux[rest_night & (hod >= rest_sleep_start)] = 1.0
        next_morning = (dow == 6) | (dow == 0)
        lux[next_morning & (hod < end - HOURS_PER_DAY)] = 1.0
    return lux


def candidates(n: int) -> list[dict]:
    out: list[dict] = []
    for rest in (23.0, 1.0, 3.0):
        for glasses in (1.0, 0.15, 0.02):
            for seek in (False, True):
                for start in (8.5, 9.0, 9.5, 10.0):
                    for length in (6.0, 7.0, 8.0):
                        out.append(
                            dict(
                                sleep_start=start,
                                sleep_len=length,
                                sunglasses=glasses,
                                light_seek=seek,
                                rest_sleep_start=rest,
                            )
                        )
    return out[:n]


def rk4_batch(model, time_h: np.ndarray, state0: np.ndarray, light: np.ndarray) -> np.ndarray:
    """Fixed-step RK4 over a batch. state0: (n_states, n_batch); light: (n_time, n_batch)."""
    sol = np.empty((len(time_h), *state0.shape))
    sol[0] = state0
    state = state0
    for idx in range(1, len(time_h)):
        dt = time_h[idx] - time_h[idx - 1]
        state = model.step_rk4(time_h[idx], state, light[idx], dt)
        sol[idx] = state
    return sol


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=int, default=200)
    parser.add_argument("--minute-candidates", type=int, default=10,
                        help="candidates to run one at a time at the 1 min step (extrapolated)")
    args = parser.parse_args()

    t0 = time.perf_counter()
    from circadian.models import Forger99, Hannay19  # noqa: E402

    import_s = time.perf_counter() - t0

    print(f"python {sys.version.split()[0]} on {platform.machine()} {platform.platform()}")
    print(f"import circadian.models: {import_s:.2f} s")
    print()
    print("| model | step (h) | what | wall time | per candidate |")
    print("|---|---|---|---|---|")

    cands = candidates(args.candidates)
    n = len(cands)
    results: dict[str, float] = {}

    for model_name, Model in (("Forger99", Forger99), ("Hannay19", Hannay19)):
        model = Model()
        for dt in (0.1, 1.0 / 60.0):
            label = "0.1" if dt == 0.1 else "1/60"
            time_burn = np.arange(0.0, 14 * HOURS_PER_DAY, dt)
            base = light_profile(dt, 14)

            # one schedule: equilibrate 14 days, then simulate 14 days
            t0 = time.perf_counter()
            state = model.equilibrate(time_burn, base, num_loops=3)
            traj = model.integrate(time_burn, state, base)
            cbt = model.cbt(traj)
            one_s = time.perf_counter() - t0
            print(f"| {model_name} | {label} | one schedule: 3 burn-in loops + 14 days + markers | {one_s:.2f} s | |")

            # candidates one at a time with the package loop
            k = n if dt == 0.1 else min(args.minute_candidates, n)
            t0 = time.perf_counter()
            for c in cands[:k]:
                lux = light_profile(dt, 14, **c)
                tr = model.integrate(time_burn, state, lux)
                model.cbt(tr)
            loop_s = time.perf_counter() - t0
            per = loop_s / k
            note = "" if k == n else f" (measured {k}, extrapolated to {n})"
            print(f"| {model_name} | {label} | {n} candidates, package integrate loop{note} | {per * n:.1f} s | {per * 1000:.0f} ms |")
            results[f"{model_name} {label} loop"] = per * n

            # all candidates in one batched RK4 pass
            lux_batch = np.stack([light_profile(dt, 14, **c) for c in cands], axis=1)
            state_batch = np.repeat(state[:, None], n, axis=1)
            t0 = time.perf_counter()
            sol = rk4_batch(model, time_burn, state_batch, lux_batch)
            batch_s = time.perf_counter() - t0
            t0 = time.perf_counter()
            from scipy.signal import find_peaks  # noqa: E402

            x_idx = 0 if model_name == "Forger99" else 1
            for j in range(n):
                series = sol[:, x_idx, j] if model_name == "Forger99" else np.cos(sol[:, x_idx, j])
                find_peaks(-series, distance=int(np.ceil(13.0 / dt)))
            markers_s = time.perf_counter() - t0
            print(f"| {model_name} | {label} | {n} candidates, batched RK4 on package derv | {batch_s:.2f} s | {batch_s / n * 1000:.1f} ms |")
            print(f"| {model_name} | {label} | {n} candidates, marker extraction | {markers_s:.2f} s | {markers_s / n * 1000:.1f} ms |")
            results[f"{model_name} {label} batch"] = batch_s

            # parity between the two loops on the first candidate
            lux0 = light_profile(dt, 14, **cands[0])
            ref = model.integrate(time_burn, state, lux0).states
            diff = float(np.max(np.abs(ref - sol[:, :, 0])))
            print(f"| {model_name} | {label} | max abs state difference, package loop vs batched | {diff:.1e} | |")

    print()
    print("steps per 14 days: 0.1 h step = 3360; 1 min step = 20160")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
