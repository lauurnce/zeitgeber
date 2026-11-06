# Copy review

Every user-facing string in the plan outputs (timeline, plan JSON, calendar export and
nudges), in English and Taglish. Generated from `zeitgeber/output/copy.toml` by
`uv run python scripts/copy_review.py`; a test fails when this file and the catalog
differ. To change wording, edit the catalog (or mark changes here and they are copied
over), then regenerate.

Status: all Taglish strings are drafts waiting for review by a native speaker.

Words in braces are filled from the plan: `{start}` and `{end}` are clock times such
as "2 AM" or "9:30 AM", `{minutes}` and `{hours}` are whole numbers, `{with}` and
`{without}` are scores in hours with one decimal, `{change}` is a name from
"Names of changes". Keep every placeholder in both languages.

Filled-in examples for the three fixture workers: `tests/golden/*.txt`.

Not covered here: the web site copy in `web/src/lib/site.ts` (English only for now).

## Disclaimers

Top of the timeline, the plan JSON and the calendar.

| Key | Where | English | Taglish |
|---|---|---|---|
| `disclaimer.wellness` | disclaimer | Zeitgeber is a wellness planning tool, not medical advice. | Ang Zeitgeber ay wellness planning tool, hindi medical advice. |
| `disclaimer.doctor` | disclaimer | If you have a sleep condition, are pregnant or have a health condition, talk to a doctor before changing your sleep. | Kung may problema ka sa tulog, buntis ka, o may health condition, kausapin muna ang doktor bago baguhin ang tulog mo. |
| `disclaimer.model` | disclaimer | The times come from a body-clock model. Your body may differ, so adjust a time if it does not suit you. | Galing sa body-clock model ang mga oras. Pwedeng iba ang katawan mo, kaya i-adjust ang oras kung hindi bagay sa iyo. |

## Recommendations

The "What to change" list.

| Key | Where | English | Taglish |
|---|---|---|---|
| `rec.sunglasses.cat3` | recommendation | Wear dark sunglasses (category 3) on the commute home whenever the sun is up. | Mag-shades (category 3) sa biyahe pauwi tuwing may araw. |
| `rec.sunglasses.dark` | recommendation | Wear very dark sunglasses on the commute home whenever the sun is up. Only if you are not the one driving. | Mag-suot ng napakadilim na shades sa biyahe pauwi tuwing may araw. Para lang ito kung hindi ikaw ang nagmamaneho. |
| `rec.sleep` | recommendation | After each night shift, sleep from {start} to {end} in a dark room. | Pagkatapos ng bawat night shift, matulog mula {start} hanggang {end} sa madilim na kwarto. |
| `rec.rest_day` | recommendation | On rest days, sleep from {start} to {end}. | Sa rest days, matulog mula {start} hanggang {end}. |
| `rec.light_brake` | recommendation | After day sleep, go outside for {minutes} minutes at {start}. | Pagkatapos ng tulog sa araw, lumabas nang {minutes} minuto sa {start}. |
| `rec.light_seek` | recommendation | During your shift, stay in the brightest spot you can from {start} to {end}. | Habang naka-shift, pumwesto sa pinakamaliwanag na lugar mula {start} hanggang {end}. |
| `rec.nap` | recommendation | Nap from {start} to {end} before leaving for work. | Umidlip mula {start} hanggang {end} bago umalis papasok. |
| `rec.caffeine` | recommendation | Have caffeine only from {start} to {end}, then switch to water. | Kape lang mula {start} hanggang {end}, tapos tubig na. |
| `rec.keep` | recommendation, when no change scores better | Your current schedule scored as well as any plan we tried. Keep it as it is. | Kasing-ayos na ng kahit anong plan na sinubukan namin ang schedule mo ngayon. Ituloy mo lang. |

## Nudges

One per plan event; also the calendar reminder text.

| Key | Where | English | Taglish |
|---|---|---|---|
| `nudge.sunglasses` | nudge | Shades on for the ride home, even if it is cloudy. Morning light tells your body it is morning. We want it to stay night for your body until you fall asleep. | Shades on pauwi, kahit maulap. Ang liwanag sa umaga ang nagsasabi sa katawan mo na umaga na. Gusto nating gabi pa rin para sa kanya hanggang makatulog ka. |
| `nudge.caffeine` | nudge | {end} is your last coffee. Water after that, so you fall asleep more easily when you get home. | {end} ang huling kape mo. Tubig na lang pagkatapos, para madali kang makatulog pag-uwi. |
| `nudge.light_seek` | nudge | {start} to {end}: stay in the brightest spot you can. This helps move your body clock toward your night schedule. | {start} hanggang {end}: dito ka sa pinakamaliwanag na pwesto. Ito ang tumutulong ilipat ang body clock mo papunta sa night schedule. |
| `nudge.sleep_low` | nudge, when the body-clock low falls inside this sleep | Lights out by {start}. Blackout curtains on, phone face down. Sleep now, while your body clock is at its lowest. | Lights out na by {start}. Sarado ang blackout curtains, nakataob ang phone. Matulog ka na habang pinakamababa ang body clock mo. |
| `nudge.sleep` | nudge, when the body-clock low falls outside this sleep | Lights out by {start}. Blackout curtains on, phone face down. A dark room helps you sleep through to {end}. | Lights out na by {start}. Sarado ang blackout curtains, nakataob ang phone. Mas tuloy-tuloy ang tulog mo hanggang {end} kapag madilim ang kwarto. |
| `nudge.rest_sleep` | nudge | Rest day: sleep from {start} to {end}. A late night keeps your body clock close to your work nights. | Rest day: tulog ka mula {start} hanggang {end}. Ang medyo late na tulog ang nagpapanatili sa body clock mo na malapit sa work nights mo. |
| `nudge.light_brake` | nudge | Go outside for {minutes} minutes at {start}. Daylight after you wake keeps your body clock from drifting too late. | Lumabas ka nang {minutes} minuto sa {start}. Ang liwanag ng araw pagkagising ang pumipigil na masyadong ma-late ang body clock mo. |
| `nudge.nap` | nudge | Nap from {start} to {end} before work. Set an alarm and get up when it rings. | Idlip muna mula {start} hanggang {end} bago pumasok. Mag-alarm ka at bumangon pagtunog nito. |

## Event titles

Timeline rows and calendar event names.

| Key | Where | English | Taglish |
|---|---|---|---|
| `event.shift` | event title | Shift | Shift |
| `event.commute_to_work` | event title | Commute to work | Biyahe papasok |
| `event.commute_home` | event title | Commute home | Biyahe pauwi |
| `event.sleep` | event title | Sleep | Tulog |
| `event.rest_sleep` | event title | Rest-day sleep | Tulog sa rest day |
| `event.nap` | event title | Nap | Idlip |
| `event.light_seek` | event title | Bright light | Maliwanag na pwesto |
| `event.light_brake` | event title | Outdoors after waking | Labas pagkagising |
| `event.sunglasses` | event title | Sunglasses on | Shades on |
| `event.caffeine` | event title | Caffeine OK | Pwede ang kape |

## Names of changes

Used inside the explanations.

| Key | Where | English | Taglish |
|---|---|---|---|
| `change.sunglasses` | explanation, name of the change | Sunglasses on the way home | Shades pauwi |
| `change.sleep_start_offset_h` | explanation, name of the change | Day sleep start | Simula ng tulog sa araw |
| `change.sleep_len_h` | explanation, name of the change | Day sleep length | Haba ng tulog sa araw |
| `change.rest_day` | explanation, name of the change | Rest-day sleep | Tulog sa rest day |
| `change.light_brake` | explanation, name of the change | Outdoors after waking | Labas pagkagising |
| `change.light_seek_start_h` | explanation, name of the change | Bright light during the shift | Liwanag habang naka-shift |
| `change.nap_len_min` | explanation, name of the change | Pre-shift nap | Idlip bago mag-shift |

## Explanations

The "Why" list.

| Key | Where | English | Taglish |
|---|---|---|---|
| `explain.score` | explanation | {change}: without it, the misalignment score goes from {with} h to {without} h. | {change}: kung wala ito, ang misalignment score ay magiging {without} h mula {with} h. |
| `explain.cost` | explanation, when the change on its own raises the score | {change}: on its own this raises the misalignment score from {without} h to {with} h, but the plan as a whole works better with it. | {change}: kung ito lang, tumataas ang misalignment score mula {without} h hanggang {with} h, pero mas maayos ang buong plan kapag kasama ito. |
| `explain.sleep_floor` | explanation, when a longer day sleep raises the score | {change}: a shorter sleep would score {without} h instead of {with} h, but the plan keeps at least {hours} hours of sleep. | {change}: mas mababa sana ang score sa mas maikling tulog ({without} h imbes na {with} h), pero sinisigurado ng plan na may {hours} oras ka man lang na tulog. |
| `explain.needed` | explanation, when the plan does not work without the change | {change}: the rest of the plan does not fit without it. | {change}: hindi kakasya ang natitirang plan kung wala ito. |

## Timeline

Headings and labels in the daily text view.

| Key | Where | English | Taglish |
|---|---|---|---|
| `timeline.title` | timeline | Your {days}-day plan from {date} | Ang {days}-day plan mo simula {date} |
| `timeline.timezone` | timeline | All times are {tz} time. | Lahat ng oras ay {tz} time. |
| `timeline.changes` | timeline | What to change | Mga babaguhin |
| `timeline.why` | timeline | Why | Bakit |
| `timeline.score` | timeline | Misalignment score: {before} h now, {after} h with the plan. Lower is better. | Misalignment score: {before} h ngayon, {after} h sa plan. Mas mababa, mas maganda. |
| `timeline.cross_check` | timeline | A second body-clock model gives {before} h now and {after} h with the plan. | Sa pangalawang body-clock model, {before} h ngayon at {after} h sa plan. |
| `timeline.days` | timeline | Day by day | Bawat araw |
| `timeline.next_day` | timeline, after an end time on the following day | next day | kinabukasan |
| `timeline.body_clock_low` | timeline | Body clock lowest around {time} | Pinakamababa ang body clock bandang {time} |
| `timeline.changed` | timeline, marks a row the plan adds or changes | new | bago |

## Calendar

Calendar export.

| Key | Where | English | Taglish |
|---|---|---|---|
| `ics.calendar_name` | calendar name | Zeitgeber plan | Zeitgeber plan |

## Weekday labels

| English | Taglish |
|---|---|
| Mon | Lun |
| Tue | Mar |
| Wed | Miy |
| Thu | Huw |
| Fri | Biy |
| Sat | Sab |
| Sun | Lin |

## Grounding check word lists

Rewordings from the optional language model are rejected when they contain one of these
terms (matched at the start of a word, any case). Add Tagalog terms that should also be
blocked.

`melatonin\w*`, `dos(?:e|es|age|ages|ing)`, `disorders?`, `treat(?:s|ed|ing|ment|ments)?`, `cur(?:e|es|ed|ing)`, `diagnos\w*`, `medications?`, `medicines?`, `prescri\w*`, `pills?`, `supplements?`, `insomnia`, `sedatives?`, `gamot\w*`, `gamutin`, `ginagamot`, `lunas\w*`, `malunasan`, `reseta`, `nireseta\w*`, `pampatulog`, `tableta\w*`, `diyagnos\w*`, `sakit`

Number words counted as numbers, so a rewording cannot add a quantity in words. The
Tagalog linker form ("dalawang", "isang") is counted too.

`zero`, `wala`, `one`, `isa`, `uno`, `two`, `dalawa`, `dos`, `three`, `tatlo`, `tres`, `four`, `apat`, `kwatro`, `kuwatro`, `five`, `lima`, `singko`, `six`, `anim`, `sais`, `seven`, `pito`, `siyete`, `eight`, `walo`, `otso`, `nine`, `siyam`, `nuwebe`, `ten`, `sampu`, `diyes`, `dyes`, `eleven`, `onse`, `twelve`, `dose`, `fifteen`, `twenty`, `thirty`, `sixty`, `half`, `kalahati`
