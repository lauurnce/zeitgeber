"use client";

import { useEffect, useRef, useState } from "react";

import { ChartLegend, ClockChart } from "@/components/ClockChart";
import { LanguageToggle } from "@/components/LanguageToggle";
import { Nudges } from "@/components/Nudges";
import { PlanSummary } from "@/components/PlanSummary";
import { ScheduleForm } from "@/components/ScheduleForm";
import { Timeline } from "@/components/Timeline";
import { ApiError, fetchCalendar, fetchPlan } from "@/lib/api";
import type { Lang, PlanDocument } from "@/lib/plan";
import {
  defaultForm,
  fieldErrorsFromProblem,
  toRequest,
  type FieldErrors,
  type ScheduleForm as Form,
} from "@/lib/schedule";

/** The planner: form, then results. Everything lives in this component's memory only. */
export function Planner({ initial }: { initial?: Form }) {
  const [form] = useState<Form>(() => initial ?? defaultForm());
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [plan, setPlan] = useState<PlanDocument | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [lang, setLang] = useState<Lang>("en");
  const [day, setDay] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const results = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    if (!busy) return;
    const started = Date.now();
    const timer = setInterval(() => setElapsed(Math.round((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(timer);
  }, [busy]);

  useEffect(() => {
    if (plan) results.current?.focus();
  }, [plan]);

  const submit = async (next: Form) => {
    controller.current?.abort();
    const ctrl = new AbortController();
    controller.current = ctrl;
    setBusy(true);
    setElapsed(0);
    setError(null);
    setFieldErrors({});
    try {
      const doc = await fetchPlan(toRequest(next), ctrl.signal);
      setPlan(doc);
      setDay(Math.min(8, doc.days.length - 1));
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      if (err instanceof ApiError) {
        setError(err.message);
        setFieldErrors(fieldErrorsFromProblem(err.errors));
      } else {
        setError("The planner had a problem. Try again in a moment.");
      }
    } finally {
      if (controller.current === ctrl) setBusy(false);
    }
  };

  const download = async () => {
    if (!plan) return;
    setDownloading(true);
    try {
      const blob = await fetchCalendar(plan, lang);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "zeitgeber-plan.ics";
      document.body.append(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The calendar could not be made.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="grid gap-10 lg:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
      <div className="flex flex-col gap-4">
        <ScheduleForm initial={form} busy={busy} serverErrors={fieldErrors} onSubmit={submit} />
        <div aria-live="polite" className="text-sm">
          {busy ? (
            <p>
              Making your plan. This can take up to 30 seconds while the body-clock model runs (
              {elapsed} s so far).
            </p>
          ) : null}
          {error ? (
            <p role="alert" className="font-semibold text-[var(--error)]">
              {error}
            </p>
          ) : null}
        </div>
      </div>

      {plan ? (
        <div className="flex min-w-0 flex-col gap-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 ref={results} tabIndex={-1} className="text-2xl font-semibold focus:outline-none">
              Your plan
            </h2>
            <LanguageToggle lang={lang} onChange={setLang} />
          </div>
          <PlanSummary plan={plan} lang={lang} />
          <section aria-labelledby="clock-heading" className="flex flex-col gap-3">
            <h2 id="clock-heading" className="text-xl font-semibold">
              Body clock on one day
            </h2>
            <p className="text-sm text-[var(--muted)]">
              Inner ring: your biological night from the model, with the body-clock low marked.
              Outer rings: work, commute and sleep, with plan steps on the outside. Midnight is at
              the top.
            </p>
            <ClockChart plan={plan} dayIndex={day} lang={lang} />
            <ChartLegend />
          </section>
          <Timeline plan={plan} lang={lang} selected={day} onSelect={setDay} />
          <Nudges plan={plan} lang={lang} />
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={download}
              disabled={downloading}
              className="self-start rounded-md bg-[var(--accent)] px-4 py-3 font-semibold text-[var(--on-accent)] hover:bg-[var(--accent-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)] disabled:opacity-60"
            >
              {downloading ? "Preparing calendar..." : "Download calendar (.ics)"}
            </button>
            <p className="text-sm text-[var(--muted)]">
              Adds the plan to Google Calendar or Apple Calendar, with reminders, in the language
              shown above.
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
