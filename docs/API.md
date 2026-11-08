# Zeitgeber API

Base URL: `https://zeitgeber-five.vercel.app` (Vercel Python function, region `sin1`, Singapore).
Interactive schema: `/docs`; machine-readable: `/openapi.json`.

Wellness planning, not medical advice.

## Privacy

The API is stateless. Each schedule is processed in memory for one request and dropped. There is
no database, no cache of schedules and no cookies. The app never logs request bodies or query
strings; an unexpected error is logged by its exception type and path only. The platform's
request log records method, path, status and timing. The optional nudge rewording sends one
filled template at a time to the wording provider, never the schedule, and is off unless the
server sets `ZEITGEBER_LLM_WORDING`.

## Routes

| Route | Body | Returns |
|---|---|---|
| `GET /v1/health` | none | status, core version, models, plan schema version |
| `POST /v1/plan` | `{schedule, options?}` | plan document, schema 1.0 (`docs/schema/plan-1.0.json`) |
| `POST /v1/plan.ics?lang=en\|tl` | `{schedule, options?}` | the plan as an iCalendar file |
| `POST /v1/simulate` | `{schedule, model?}` | CBTmin and DLMO per local day, for debugging |

`schedule` is the schedule model in `zeitgeber/schedule.py`; `tests/fixtures/schedules/` has
three examples. `options`: `seed` (default 0), `cross_check` (default true, adds a Hannay19
score), `slow_caffeine` (default false, rule C2), `wording` (default false). `model`:
`forger99` (default), `jewett99` or `hannay19`.

## Example

```sh
python3 -c "import json; d = json.load(open('tests/fixtures/schedules/permanent_nights.json')); \
  d.pop('description'); print(json.dumps({'schedule': d}))" > plan-request.json
curl -s -X POST https://zeitgeber-five.vercel.app/v1/plan \
  -H 'content-type: application/json' --data @plan-request.json \
  -w '\n%{http_code} %{time_total}s\n'
```

## Limits

- Request body: at most 32 KB (`413`).
- Compute routes: 20 requests per minute per client per function instance (`429` with
  `Retry-After`). Health is not limited. The client key is a salted hash of the forwarded
  address, kept in memory for one minute.
- Browser calls: only from `https://zeitgeber-five.vercel.app` and `http://localhost:3000`
  (`ZEITGEBER_CORS_ORIGINS` overrides).
- Function time limit: 60 s.
- Latency: `POST /v1/plan` takes about 22 s warm on the deployed function, over the 6 s budget
  (docs/DECISIONS.md D42).

## Errors

Errors are RFC 9457 problem details with media type `application/problem+json`:
`{type, title, status, detail, errors?}`. The `type` links to a section below.

### invalid-request

`422`. The body or a query parameter failed validation. `errors` lists each problem with its
`location` (for example `["schedule", "sleep", "after_shift"]`), a plain `message` and a
`type`. Schedule conflicts, such as a sleep that starts before the commute home ends, are
reported here in words. A schedule that is valid but has no feasible plan also returns `422`
with a `detail`.

### request-too-large

`413`. The body is over 32 KB.

### too-many-requests

`429`. Wait for the number of seconds in `Retry-After`.

### not-found

`404`. Unknown route.

### method-not-allowed

`405`. The route exists with a different method.

### internal-error

`500`. Something failed on the server. The response and the log carry no schedule details.

### error

Any other HTTP error.
