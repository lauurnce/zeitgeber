// A real plan document for the permanent-nights fixture worker (seed 0), made with
// zeitgeber.output.plan_document. Regenerate it if the plan schema changes.
import type { PlanDocument } from "@/lib/plan";

import data from "./sample-plan.json";

export function samplePlan(): PlanDocument {
  return structuredClone(data) as PlanDocument;
}
