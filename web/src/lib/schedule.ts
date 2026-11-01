// The planner form: state, defaults, plain-word validation and the API request body.
// Field names follow the schedule model in zeitgeber/schedule.py.

export const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
] as const;

export const COMMUTE_MODES = {
  walk: "Walking",
  jeepney_bus: "Jeepney or bus",
  train: "Train",
  car_driver: "Driving a car",
  car_passenger: "Riding in a car",
  motorcycle: "Motorcycle",
} as const;
export type CommuteMode = keyof typeof COMMUTE_MODES;

export const REST_DAY_MODES = {
  flip_to_days: "Sleep at night like a day worker",
  keep_nights: "Keep my work-day sleep times",
} as const;
export type RestDayMode = keyof typeof REST_DAY_MODES;

export interface DayShift {
  works: boolean;
  start: string; // "HH:MM"
  end: string;
}

export interface CommuteForm {
  minutes: number;
  outdoorPercent: number;
  mode: CommuteMode;
}

export interface ScheduleForm {
  startDate: string; // "YYYY-MM-DD", the first day of the plan
  days: DayShift[]; // Monday to Sunday
  toWork: CommuteForm;
  home: CommuteForm;
  sleepAfterShift: { start: string; end: string };
  restDaySleep: { start: string; end: string };
  restDayMode: RestDayMode;
}

export type FieldErrors = Record<string, string>;

/** The next Monday on or after ``today``, as YYYY-MM-DD (plans start on a Monday). */
export function nextMonday(today: Date): string {
  const d = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
  const add = (8 - d.getUTCDay()) % 7;
  d.setUTCDate(d.getUTCDate() + add);
  return d.toISOString().slice(0, 10);
}

/** A 10 PM to 7 AM schedule, Monday to Friday, with a one-hour commute each way. */
export function defaultForm(today: Date = new Date()): ScheduleForm {
  return {
    startDate: nextMonday(today),
    days: WEEKDAYS.map((_, i) => ({ works: i < 5, start: "22:00", end: "07:00" })),
    toWork: { minutes: 60, outdoorPercent: 30, mode: "jeepney_bus" },
    home: { minutes: 60, outdoorPercent: 30, mode: "jeepney_bus" },
    sleepAfterShift: { start: "08:30", end: "15:30" },
    restDaySleep: { start: "23:00", end: "07:00" },
    restDayMode: "flip_to_days",
  };
}

const TIME = /^([01]\d|2[0-3]):[0-5]\d$/;

export function minutesOf(hhmm: string): number {
  const [h, m] = hhmm.split(":").map(Number);
  return (h ?? 0) * 60 + (m ?? 0);
}

/** Length of a clock window in hours; an end at or before the start ends the next day. */
export function spanHours(start: string, end: string): number {
  const span = (minutesOf(end) - minutesOf(start) + 1440) % 1440;
  return (span || 1440) / 60;
}

function hours(h: number): string {
  if (h === 1) return "1 hour";
  return Number.isInteger(h) ? `${h} hours` : `${h.toFixed(1)} hours`;
}

/** Problems a person can fix in the form, keyed by field id, in plain words. */
export function validate(form: ScheduleForm): FieldErrors {
  const errors: FieldErrors = {};
  if (!/^\d{4}-\d{2}-\d{2}$/.test(form.startDate)) {
    errors.startDate = "Pick the date your plan should start.";
  }
  if (!form.days.some((d) => d.works)) {
    errors.days = "Tick at least one day that you work.";
  }
  form.days.forEach((d, i) => {
    if (!d.works) return;
    const name = WEEKDAYS[i];
    if (!TIME.test(d.start) || !TIME.test(d.end)) {
      errors[`day-${i}`] = `Enter a start and end time for ${name}.`;
      return;
    }
    const h = spanHours(d.start, d.end);
    if (h < 4 || h > 14) {
      errors[`day-${i}`] = `The ${name} shift lasts ${hours(h)}. Shifts need to be 4 to 14 hours.`;
    }
  });
  for (const [key, label, c] of [
    ["toWork", "to work", form.toWork],
    ["home", "home", form.home],
  ] as const) {
    if (!Number.isFinite(c.minutes) || c.minutes < 0 || c.minutes > 300) {
      errors[`${key}-minutes`] = `Enter your commute ${label} in minutes, from 0 to 300.`;
    }
    if (!Number.isFinite(c.outdoorPercent) || c.outdoorPercent < 0 || c.outdoorPercent > 100) {
      errors[`${key}-outdoor`] = "Enter a share from 0 to 100 percent.";
    }
  }
  for (const [key, label, w] of [
    ["sleepAfterShift", "after work", form.sleepAfterShift],
    ["restDaySleep", "on rest days", form.restDaySleep],
  ] as const) {
    if (!TIME.test(w.start) || !TIME.test(w.end)) {
      errors[key] = `Enter when you fall asleep and wake up ${label}.`;
      continue;
    }
    const h = spanHours(w.start, w.end);
    if (h < 3 || h > 12) {
      errors[key] = `Your sleep ${label} lasts ${hours(h)}. Enter a window of 3 to 12 hours.`;
    }
  }
  return errors;
}

/** The request body for POST /v1/plan. */
export function toRequest(form: ScheduleForm) {
  const commute = (c: CommuteForm) => ({
    duration_min: Math.round(c.minutes),
    outdoor_share: Math.round(c.outdoorPercent) / 100,
    mode: c.mode,
  });
  return {
    schedule: {
      anchor_date: form.startDate,
      plan_days: 14,
      shifts: form.days.flatMap((d, i) =>
        d.works ? [{ weekday: i, start: d.start, end: d.end }] : [],
      ),
      commute_to_work: commute(form.toWork),
      commute_home: commute(form.home),
      sleep: { after_shift: form.sleepAfterShift, rest_day: form.restDaySleep },
      rest_days: { mode: form.restDayMode },
    },
  };
}

export interface ProblemError {
  location: (string | number)[];
  message: string;
}

/** Map server validation errors to form fields; anything unmatched goes under "form". */
export function fieldErrorsFromProblem(errors: ProblemError[]): FieldErrors {
  const out: FieldErrors = {};
  const add = (key: string, message: string) => {
    out[key] = out[key] ? `${out[key]} ${message}` : message;
  };
  for (const e of errors) {
    const message = sentence(e.message);
    const path = e.location.join(".");
    const shift = /^schedule\.shifts\.(\d+)/.exec(path);
    if (path.startsWith("schedule.anchor_date")) add("startDate", message);
    else if (shift) add("days", message);
    else if (path.startsWith("schedule.commute_to_work")) add("toWork-minutes", message);
    else if (path.startsWith("schedule.commute_home")) add("home-minutes", message);
    else if (path.startsWith("schedule.sleep.after_shift")) add("sleepAfterShift", message);
    else if (path.startsWith("schedule.sleep.rest_day")) add("restDaySleep", message);
    else add("form", message);
  }
  return out;
}

function sentence(message: string): string {
  const text = message.replace(/^schedule conflicts: /, "");
  const first = text.charAt(0).toUpperCase() + text.slice(1);
  return /[.!?]$/.test(first) ? first : `${first}.`;
}
