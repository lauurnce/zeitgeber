// Benchmark of a plain JavaScript port of the Forger99 equations, for the
// runtime decision in docs/ARCHITECTURE.md. Same schedule stand-in and the
// same RK4 scheme as scripts/bench_sim.py. Equations follow the Arcascope
// circadian package (circadian/models.py, class Forger99), which cites
// Forger, Jewett and Kronauer (1999).
//
//     node scripts/bench_sim.mjs

const P = { taux: 24.2, mu: 0.23, G: 33.75, alpha0: 0.05, beta: 0.0075, p: 0.5, I0: 9500.0, k: 0.55 };

function derv(x, xc, n, light, out) {
  const alpha = P.alpha0 * Math.pow(light / P.I0, P.p);
  const B = P.G * (1 - n) * alpha * (1 - 0.4 * x) * (1 - 0.4 * xc);
  const tauTerm = Math.pow(24.0 / (0.99669 * P.taux), 2) + P.k * B;
  out[0] = (Math.PI / 12) * (xc + B);
  out[1] = (Math.PI / 12) * (P.mu * (xc - (4 / 3) * xc * xc * xc) - x * tauTerm);
  out[2] = 60 * (alpha * (1 - n) - P.beta * n);
}

function lightProfile(dt, days, c) {
  const nT = Math.round((days * 24) / dt);
  const lux = new Float64Array(nT);
  for (let i = 0; i < nT; i++) {
    const t = i * dt;
    const hod = t % 24;
    const dow = Math.floor(t / 24) % 7;
    let v = 100;
    if ((hod >= 22 && dow <= 4) || (hod < 7 && dow >= 1 && dow <= 5)) v = 500;
    if (c.lightSeek && hod >= 22 && hod >= 23 && dow <= 4) v = 1000;
    const afterShift = dow >= 1 && dow <= 5;
    if (afterShift && hod >= 7 && hod < 7 + 40 / 60) v = 10000 * c.sunglasses;
    if (afterShift && hod >= 7 + 40 / 60 && hod < 8.5) v = 1000 * c.sunglasses;
    if (afterShift && hod >= c.sleepStart && hod < c.sleepStart + c.sleepLen) v = 1;
    const restNight = dow === 5 || dow === 6;
    const end = c.restSleepStart + 8;
    if (end <= 24) {
      if (restNight && hod >= c.restSleepStart && hod < end) v = 1;
    } else {
      if (restNight && hod >= c.restSleepStart) v = 1;
      if ((dow === 6 || dow === 0) && hod < end - 24) v = 1;
    }
    lux[i] = v;
  }
  return lux;
}

function simulate(dt, lux, state) {
  const k1 = [0, 0, 0], k2 = [0, 0, 0], k3 = [0, 0, 0], k4 = [0, 0, 0];
  let [x, xc, n] = state;
  for (let i = 1; i < lux.length; i++) {
    const L = lux[i];
    derv(x, xc, n, L, k1);
    derv(x + k1[0] * dt / 2, xc + k1[1] * dt / 2, n + k1[2] * dt / 2, L, k2);
    derv(x + k2[0] * dt / 2, xc + k2[1] * dt / 2, n + k2[2] * dt / 2, L, k3);
    derv(x + k3[0] * dt, xc + k3[1] * dt, n + k3[2] * dt, L, k4);
    x += (dt / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);
    xc += (dt / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
    n += (dt / 6) * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]);
  }
  return [x, xc, n];
}

function candidates(nMax) {
  const out = [];
  for (const restSleepStart of [23, 1, 3])
    for (const sunglasses of [1, 0.15, 0.02])
      for (const lightSeek of [false, true])
        for (const sleepStart of [8.5, 9, 9.5, 10])
          for (const sleepLen of [6, 7, 8]) out.push({ sleepStart, sleepLen, sunglasses, lightSeek, restSleepStart });
  return out.slice(0, nMax);
}

console.log(`node ${process.version} on ${process.arch}`);
console.log("| step (h) | what | wall time | per candidate |");
console.log("|---|---|---|---|");
const init = [-0.0843259, -1.09607546, 0.45584306]; // package default initial condition
for (const dt of [0.1, 1 / 60]) {
  const label = dt === 0.1 ? "0.1" : "1/60";
  const base = lightProfile(dt, 14, { sleepStart: 9, sleepLen: 6, sunglasses: 1, lightSeek: false, restSleepStart: 23 });
  let t0 = performance.now();
  let state = init;
  for (let loop = 0; loop < 3; loop++) state = simulate(dt, base, state);
  simulate(dt, base, state);
  console.log(`| ${label} | one schedule: 3 burn-in loops + 14 days | ${((performance.now() - t0)).toFixed(0)} ms | |`);
  const cands = candidates(200);
  t0 = performance.now();
  for (const c of cands) simulate(dt, lightProfile(dt, 14, c), state);
  const ms = performance.now() - t0;
  console.log(`| ${label} | 200 candidates, 14 days each | ${ms.toFixed(0)} ms | ${(ms / 200).toFixed(2)} ms |`);
}
