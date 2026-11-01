// Types for the plan document (schema 1.0, docs/schema/plan-1.0.json) and display helpers.
// Clock times are read from the local ISO strings the API returns, so the view always shows
// the schedule's own timezone, whatever the browser's timezone is.

export type Lang = "en" | "tl";
export interface Text {
  en: string;
  tl: string;
}

export type EventKind =
  | "shift"
  | "commute_to_work"
  | "commute_home"
  | "sleep"
  | "rest_sleep"
  | "nap"
  | "light_seek"
  | "light_brake"
  | "sunglasses"
  | "caffeine";

export interface PlanEvent {
  id: string;
  kind: EventKind;
  start_utc: string;
  end_utc: string;
  start_local: string;
  end_local: string;
  title: Text;
  rule_ids: string[];
  recommended: boolean;
  reminder: { minutes_before: number; related: "start" | "end" } | null;
}

export interface PlanDay {
  date: string;
  label: Text;
  events: PlanEvent[];
  cbt_min_local: string | null;
  category: string | null;
}

export interface ScoreSummary {
  total_h: number;
  phase_angle_h: number;
  work_in_low_h: number;
  sleep_in_night_frac: number;
  social_jetlag_h: number;
  modal_category: string;
  flagged_days: number;
  lam: number;
}

export interface PlanDocument {
  schema_version: "1.0";
  plan_id: string;
  generated_at: string;
  timezone: string;
  start_date: string;
  days_count: number;
  seed: number;
  disclaimers: Text[];
  recommendations: { intervention: string; rule_ids: string[]; text: Text }[];
  explanations: {
    intervention: string;
    rule_ids: string[];
    score_with_h: number;
    score_without_h: number | null;
    delta_score_h: number | null;
    text: Text;
  }[];
  score: {
    model: string;
    baseline: ScoreSummary;
    plan: ScoreSummary;
    cross_check_model: string | null;
    cross_check_baseline: ScoreSummary | null;
    cross_check_plan: ScoreSummary | null;
  };
  days: PlanDay[];
  nudges: { event_id: string; template: string; text: Text; source: Record<Lang, string> }[];
}

/** Display groups for the charts: what a segment means to the reader. */
export type Group = "work" | "commute" | "sleep" | "plan";

export function groupOf(kind: EventKind): Group {
  if (kind === "shift") return "work";
  if (kind === "commute_to_work" || kind === "commute_home") return "commute";
  if (kind === "sleep" || kind === "rest_sleep") return "sleep";
  return "plan";
}

export const GROUP_LABELS: Record<Group, string> = {
  work: "Work",
  commute: "Commute",
  sleep: "Sleep",
  plan: "Plan step",
};

/** Local date "YYYY-MM-DD" and clock hours (0 to 24) of a local ISO time. */
export function localParts(iso: string): { date: string; hours: number } {
  const date = iso.slice(0, 10);
  const hours = Number(iso.slice(11, 13)) + Number(iso.slice(14, 16)) / 60;
  return { date, hours };
}

/** "2 AM", "9:30 AM", "12 PM": the clock style used in the plan text. */
export function clock(hours: number): string {
  const total = Math.round((((hours % 24) + 24) % 24) * 60) % 1440;
  const h = Math.floor(total / 60);
  const m = total % 60;
  const suffix = h < 12 ? "AM" : "PM";
  const h12 = h % 12 || 12;
  return m === 0 ? `${h12} ${suffix}` : `${h12}:${String(m).padStart(2, "0")} ${suffix}`;
}

export function clockOf(iso: string): string {
  return clock(localParts(iso).hours);
}

export interface Segment {
  start: number; // hours on the local day, 0 to 24
  end: number;
  event: PlanEvent;
}

/** The parts of all plan events that fall on local ``date``, clipped to that day. */
export function segmentsOn(doc: PlanDocument, date: string): Segment[] {
  const out: Segment[] = [];
  for (const event of doc.days.flatMap((d) => d.events)) {
    const s = localParts(event.start_local);
    const e = localParts(event.end_local);
    const start = s.date < date ? 0 : s.date === date ? s.hours : null;
    const end = e.date > date ? 24 : e.date === date ? e.hours : null;
    if (start === null || end === null || end <= start) continue;
    out.push({ start, end, event });
  }
  return out.sort((a, b) => a.start - b.start || a.end - b.end);
}

/** Biological night: CBTmin minus 6 h to CBTmin plus 2 h (docs/SCIENCE.md 7.3). */
export const NIGHT_BEFORE_H = 6;
export const NIGHT_AFTER_H = 2;

export function biologicalNight(cbtLocal: string): { start: number; end: number; low: number } {
  const low = localParts(cbtLocal).hours;
  return { start: low - NIGHT_BEFORE_H, end: low + NIGHT_AFTER_H, low };
}

export function textFor(t: Text, lang: Lang): string {
  return lang === "en" ? t.en : t.tl;
}
