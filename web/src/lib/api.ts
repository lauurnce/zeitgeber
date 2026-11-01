// Calls to the Zeitgeber API. The schedule goes in the request body only: it is not kept in
// the browser (no storage, no cookies, no analytics) and the API does not store it.

import type { Lang, PlanDocument } from "./plan";
import type { ProblemError } from "./schedule";

export const API_URL = (
  process.env.NEXT_PUBLIC_ZEITGEBER_API_URL ?? "https://zeitgeber-five.vercel.app"
).replace(/\/$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly errors: ProblemError[] = [],
  ) {
    super(message);
  }
}

async function post(path: string, body: unknown, signal?: AbortSignal): Promise<Response> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal,
      credentials: "omit",
      cache: "no-store",
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("We could not reach the planner. Check your connection and try again.", 0);
  }
  if (response.ok) return response;
  let problem: { detail?: string; errors?: ProblemError[] } = {};
  try {
    problem = await response.json();
  } catch {
    // not a problem document
  }
  const messages: Record<number, string> = {
    413: "The schedule is too large to send.",
    422: problem.detail ?? "Some details in the schedule need fixing.",
    429: "Too many plans in a short time. Wait a minute and try again.",
  };
  throw new ApiError(
    messages[response.status] ?? "The planner had a problem. Try again in a moment.",
    response.status,
    problem.errors ?? [],
  );
}

export async function fetchPlan(body: unknown, signal?: AbortSignal): Promise<PlanDocument> {
  return (await post("/v1/plan", body, signal)).json();
}

export async function fetchCalendar(plan: PlanDocument, lang: Lang): Promise<Blob> {
  return (await post("/v1/calendar", { plan, lang })).blob();
}
