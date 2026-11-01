"use client";

import { useId, useRef, useState, type FormEvent, type ReactNode } from "react";

import {
  COMMUTE_MODES,
  REST_DAY_MODES,
  WEEKDAYS,
  validate,
  type CommuteForm,
  type CommuteMode,
  type FieldErrors,
  type RestDayMode,
  type ScheduleForm as Form,
} from "@/lib/schedule";
import { site } from "@/lib/site";

interface Props {
  initial: Form;
  busy: boolean;
  serverErrors: FieldErrors;
  onSubmit: (form: Form) => void;
}

const input =
  "w-full min-w-0 rounded-md border border-[var(--border)] bg-[var(--surface)] px-2 py-1.5 text-base " +
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] " +
  "aria-[invalid=true]:border-[var(--error)]";

function ErrorText({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <p id={id} className="text-sm text-[var(--error)]">
      {message}
    </p>
  );
}

function Section({ title, children, hint }: { title: string; children: ReactNode; hint?: string }) {
  return (
    <fieldset className="flex flex-col gap-3 rounded-lg border border-[var(--border)] p-4">
      <legend className="px-1 text-lg font-semibold">{title}</legend>
      {hint ? <p className="text-sm text-[var(--muted)]">{hint}</p> : null}
      {children}
    </fieldset>
  );
}

export function ScheduleForm({ initial, busy, serverErrors, onSubmit }: Props) {
  const [form, setForm] = useState<Form>(initial);
  const [errors, setErrors] = useState<FieldErrors>({});
  const summary = useRef<HTMLDivElement>(null);
  const uid = useId();
  const shown: FieldErrors = { ...serverErrors, ...errors };
  const err = (key: string) => (shown[key] ? `${uid}-${key}-error` : undefined);

  const update = (patch: Partial<Form>) => setForm((f) => ({ ...f, ...patch }));
  const setDay = (i: number, patch: Partial<Form["days"][number]>) =>
    setForm((f) => ({ ...f, days: f.days.map((d, k) => (k === i ? { ...d, ...patch } : d)) }));
  const setCommute = (key: "toWork" | "home", patch: Partial<CommuteForm>) =>
    setForm((f) => ({ ...f, [key]: { ...f[key], ...patch } }));

  const copyFirstShift = () => {
    const first = form.days.find((d) => d.works);
    if (!first) return;
    setForm((f) => ({
      ...f,
      days: f.days.map((d) => (d.works ? { ...d, start: first.start, end: first.end } : d)),
    }));
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length > 0) {
      requestAnimationFrame(() => summary.current?.focus());
      return;
    }
    onSubmit(form);
  };

  const messages = Object.values(shown);

  const commute = (key: "toWork" | "home", title: string) => {
    const c = form[key];
    return (
      <Section title={title}>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1">
            <span>Minutes, one way</span>
            <input
              className={input}
              type="number"
              inputMode="numeric"
              min={0}
              max={300}
              value={Number.isFinite(c.minutes) ? c.minutes : ""}
              aria-invalid={Boolean(shown[`${key}-minutes`])}
              aria-describedby={err(`${key}-minutes`)}
              onChange={(e) => setCommute(key, { minutes: e.target.valueAsNumber })}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span>Share outdoors, percent</span>
            <input
              className={input}
              type="number"
              inputMode="numeric"
              min={0}
              max={100}
              value={Number.isFinite(c.outdoorPercent) ? c.outdoorPercent : ""}
              aria-invalid={Boolean(shown[`${key}-outdoor`])}
              aria-describedby={err(`${key}-outdoor`)}
              onChange={(e) => setCommute(key, { outdoorPercent: e.target.valueAsNumber })}
            />
          </label>
          <label className="col-span-2 flex flex-col gap-1">
            <span>How you travel</span>
            <select
              className={input}
              value={c.mode}
              onChange={(e) => setCommute(key, { mode: e.target.value as CommuteMode })}
            >
              {Object.entries(COMMUTE_MODES).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <ErrorText id={`${uid}-${key}-minutes-error`} message={shown[`${key}-minutes`]} />
        <ErrorText id={`${uid}-${key}-outdoor-error`} message={shown[`${key}-outdoor`]} />
      </Section>
    );
  };

  const sleepWindow = (key: "sleepAfterShift" | "restDaySleep", title: string, hint: string) => (
    <Section title={title} hint={hint}>
      <div className="grid grid-cols-2 gap-3">
        {(["start", "end"] as const).map((part) => (
          <label key={part} className="flex flex-col gap-1">
            <span>{part === "start" ? "Fall asleep" : "Wake up"}</span>
            <input
              className={input}
              type="time"
              value={form[key][part]}
              aria-invalid={Boolean(shown[key])}
              aria-describedby={err(key)}
              onChange={(e) => update({ [key]: { ...form[key], [part]: e.target.value } })}
            />
          </label>
        ))}
      </div>
      <ErrorText id={`${uid}-${key}-error`} message={shown[key]} />
    </Section>
  );

  return (
    <form noValidate onSubmit={submit} className="flex flex-col gap-5" aria-busy={busy}>
      <div
        ref={summary}
        tabIndex={-1}
        role={messages.length ? "alert" : undefined}
        className={
          messages.length
            ? "rounded-lg border-2 border-[var(--error)] p-4 focus-visible:outline-2"
            : "hidden"
        }
      >
        <h2 className="font-semibold">Please check these details</h2>
        <ul className="mt-2 list-disc pl-5">
          {messages.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      </div>

      <Section
        title="When you work"
        hint="Tick each day a shift starts. Times are shift start and end."
      >
        <div className="flex flex-col gap-2">
          {WEEKDAYS.map((name, i) => {
            const day = form.days[i]!;
            return (
              <div key={name} className="flex flex-col gap-1">
                <div className="grid grid-cols-2 items-center gap-2 sm:grid-cols-[7.5rem_minmax(0,1fr)_minmax(0,1fr)]">
                  <label className="col-span-2 flex items-center gap-2 sm:col-span-1">
                    <input
                      type="checkbox"
                      className="size-5 shrink-0 accent-[var(--accent)]"
                      checked={day.works}
                      onChange={(e) => setDay(i, { works: e.target.checked })}
                    />
                    <span>{name}</span>
                  </label>
                  <label className="flex flex-col">
                    <span className="sr-only">{name} shift starts</span>
                    <input
                      className={input}
                      type="time"
                      value={day.start}
                      disabled={!day.works}
                      aria-invalid={Boolean(shown[`day-${i}`])}
                      aria-describedby={err(`day-${i}`)}
                      onChange={(e) => setDay(i, { start: e.target.value })}
                    />
                  </label>
                  <label className="flex flex-col">
                    <span className="sr-only">{name} shift ends</span>
                    <input
                      className={input}
                      type="time"
                      value={day.end}
                      disabled={!day.works}
                      aria-invalid={Boolean(shown[`day-${i}`])}
                      aria-describedby={err(`day-${i}`)}
                      onChange={(e) => setDay(i, { end: e.target.value })}
                    />
                  </label>
                </div>
                <ErrorText id={`${uid}-day-${i}-error`} message={shown[`day-${i}`]} />
              </div>
            );
          })}
        </div>
        <ErrorText id={`${uid}-days-error`} message={shown.days} />
        <button
          type="button"
          onClick={copyFirstShift}
          className="self-start rounded-md border border-[var(--border)] px-3 py-1.5 text-sm hover:bg-[var(--hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
        >
          Use the first shift&apos;s times for every workday
        </button>
      </Section>

      {commute("toWork", "Commute to work")}
      {commute("home", "Commute home")}

      {sleepWindow(
        "sleepAfterShift",
        "Sleep after a shift",
        "When you sleep now after a work day.",
      )}

      <Section title="Rest days">
        <label className="flex flex-col gap-1">
          <span>On days off, I usually</span>
          <select
            className={input}
            value={form.restDayMode}
            onChange={(e) => update({ restDayMode: e.target.value as RestDayMode })}
          >
            {Object.entries(REST_DAY_MODES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </Section>
      {sleepWindow("restDaySleep", "Sleep on rest days", "When you sleep now on a day off.")}

      <Section title="Plan start">
        <label className="flex flex-col gap-1">
          <span>First day of the 14-day plan</span>
          <input
            className={input}
            type="date"
            value={form.startDate}
            aria-invalid={Boolean(shown.startDate)}
            aria-describedby={err("startDate")}
            onChange={(e) => update({ startDate: e.target.value })}
          />
        </label>
        <ErrorText id={`${uid}-startDate-error`} message={shown.startDate} />
      </Section>

      <div className="flex flex-col gap-2">
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-[var(--accent)] px-4 py-3 text-base font-semibold text-[var(--on-accent)] hover:bg-[var(--accent-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] disabled:opacity-60"
        >
          {busy ? "Making your plan..." : "Make my plan"}
        </button>
        <p className="text-sm text-[var(--muted)]">{site.privacy}</p>
      </div>
    </form>
  );
}
