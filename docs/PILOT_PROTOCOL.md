# Pilot protocol

Zeitgeber v0.1 pilot with BPO agents on night shifts. This protocol was written and committed before any data was collected. Any change made after the first participant enrolls is logged in docs/DECISIONS.md with its date and reason.

This is a feasibility study of a wellness planning tool. It does not test for any medical condition, and it makes no clinical claims.

## 1. Questions

1. Feasibility: can agents follow a Zeitgeber plan for two weeks alongside their normal work, and keep the ratings and diary?
2. Acceptability: do they find the plan clear and worth keeping?
3. Signal: is sleepiness at the end of the shift lower during the plan weeks than in the baseline week?

## 2. Design

One group, each person compared with themselves, three weeks in a row:

| Week | What happens |
|---|---|
| 1, baseline | Usual routine. Sleepiness ratings and sleep diary only. |
| 2 and 3, plan | Follow the Zeitgeber plan made from the baseline schedule. Same ratings and diary. |

Each participant makes one plan on day 7, on their own device, from their own schedule. The plan runs 14 days. The same plan is used for both plan weeks.

## 3. Participants

- 10 to 15 agents in IT-BPM or BPO work in Metro Manila.
- Included: age 18 or older; at least four night shifts a week, each crossing midnight; the same schedule expected for the three weeks.
- Not included (self-report): pregnant; a known sleep condition; a health condition or a medicine that affects sleep; planning to travel across time zones during the study.
- People who drive or ride a motorcycle home can take part. Zeitgeber never offers them very dark lenses (rule R7 in docs/SCIENCE.md).
- Recruitment by open invitation through personal networks and community groups, never through supervisors or team leads, so no one feels pressed to join.

## 4. Measures

### 4.1 Karolinska Sleepiness Scale (KSS)

A rating from 1 to 9 of how sleepy the person feels right now (Akerstedt and Gillberg 1990; Kaida et al. 2006; docs/SCIENCE.md 8.2). Anchors on the form: 1 extremely alert, 3 alert, 5 neither alert nor sleepy, 7 sleepy but no effort to keep awake, 9 very sleepy, great effort to keep awake, fighting sleep. The exact wording of the original paper is UNVERIFIED; the form cites the published version it copies.

Taken three times on every shift:

| Rating | When |
|---|---|
| Start | within 30 minutes after the shift starts |
| Middle | within 30 minutes of the shift's midpoint |
| End | within the last 30 minutes of the shift |

### 4.2 Daily sleep diary

The core items of the Consensus Sleep Diary (Carney et al. 2012; docs/SCIENCE.md 8.3), filled in once a day after the main sleep: time into bed, time trying to sleep, minutes to fall asleep, number of awakenings, minutes awake in total, final waking time, time out of bed, sleep quality (very poor to very good), comments.

Added for Zeitgeber: worked a shift yes or no; sunglasses on the way home yes or no; minutes outdoors in daylight; caffeine times; nap start and end; whether the day's plan was followed (all, partly, not at all). In the baseline week the plan questions are left blank.

### 4.3 End of study

Five questions on a 1 to 5 scale (clear, easy to follow, fits my life, I would keep using it, I would recommend it) and two open questions: what helped, what got in the way.

## 5. Consent

Read aloud and given in writing before anything else. Participants sign or type their initials and the date. The Taglish version is a draft for review by a native speaker.

> **About this study.** Lawrence Panes is testing Zeitgeber, a free planner that suggests when to get light, avoid light, sleep and stop caffeine around night shifts. It is a wellness tool, not medical advice.
>
> **What you will do.** For three weeks you rate how sleepy you feel three times each shift, on a scale from 1 to 9, and fill in a short sleep diary once a day. In week 1 you keep your usual routine. In weeks 2 and 3 you try to follow your Zeitgeber plan. At the end you answer seven short questions. In total this takes about five minutes a day.
>
> **Your choice.** Taking part is voluntary. You can stop at any time without giving a reason, and nothing happens to you if you do. Your employer will not be told whether you took part and will never see your answers.
>
> **Your data.** Your answers are stored under a code, not your name, on paper or offline files kept by Lawrence Panes. They are never put into the Zeitgeber website or its code repository. Only group results are published, never anything that could identify you. The key that links your code to your name is deleted six months after the study ends. You can ask for your answers to be deleted at any time before then. This follows the Data Privacy Act of 2012 (Republic Act 10173).
>
> **Your safety.** If you feel worse at any point, stop following the plan and go back to your usual routine, and tell Lawrence. Do not drive or ride if you feel drowsy. Talk to a doctor if you often cannot sleep or cannot stay awake, if you nod off at work or on the road, or if you have a health condition.
>
> **Questions.** Contact Lawrence Panes at the address on the form.
>
> I have read this, my questions were answered, and I agree to take part.

## 6. Privacy and anonymization

- Each person gets a code (P01 to P15). Forms carry the code only.
- The key linking codes to names and contact details is one offline file, kept apart from the data and deleted six months after the last participant finishes.
- Data stays outside this repository. The local folder `pilot-data/` is excluded from git in `.git/info/exclude` and is never committed, pushed or shared. Storage is an encrypted drive or locked paper files.
- No pilot data enters the web app or the API. Participants use the public planner like anyone else, and it stores nothing.
- Results are reported for the group only. No subgroup of fewer than five people is reported. Free-text quotes are checked for names, employers, accounts and places before use.
- Employers and supervisors receive no individual data and no list of who took part.

## 7. Stopping rules

For one participant, the plan stops (they return to their usual routine and keep filling in the forms only if they want to) when any of these happens:

1. They say they feel worse, for any reason.
2. They report nodding off or nearly crashing while driving or riding.
3. End-of-shift KSS is 8 or 9 on three shifts within one plan week.
4. The diary shows less than 4 hours of main sleep on two days in a row.

Each stop is recorded with its reason and counted in the results. For 2, 3 and 4 the participant is also advised to talk to a doctor.

For the whole study: if three or more participants stop under rule 1 or 2, enrollment pauses and the protocol is reviewed before anyone else starts.

## 8. Analysis plan

Fixed before data collection. The study is small and exploratory, so the results are estimates with uncertainty, not proof.

- Primary outcome: for each person, mean end-of-shift KSS in the plan weeks (weeks 2 and 3) minus mean end-of-shift KSS in the baseline week. Negative means less sleepy.
- A person's period mean needs at least 3 rated shifts in that period; otherwise that person is left out of the primary analysis and the reason is reported.
- Estimate: the median of the per-person differences, with a 95% confidence interval (Hodges-Lehmann with the Wilcoxon signed-rank interval). The Wilcoxon signed-rank test p-value is reported alongside, not used alone.
- Secondary outcomes, analysed the same way: KSS at shift start and middle; total sleep time of the main sleep after a shift; sleep quality rating.
- Feasibility: share of enrolled people who finish all three weeks; share of KSS ratings and diary days completed; share of days the plan was followed in full, by rule (sunglasses, sleep window, light brake, caffeine).
- Acceptability: median and range of each end-of-study question.
- Who is analysed: everyone with enough baseline and plan-week ratings (all enrolled), plus a second analysis of those who followed the plan in full on at least half of the plan days.
- Week effects: a second week of plan use is compared with the first, to see whether any change grows, holds or fades.

## 9. What counts as no effect

The smallest change worth noticing is set at 1 point on the KSS for the end of the shift. This is a design choice for this pilot (UNVERIFIED as a published minimal important difference).

- **No meaningful effect:** the 95% confidence interval of the median difference lies entirely above -1, meaning any improvement is smaller than 1 point. This includes an interval that contains zero and stops short of -1, and any result in which sleepiness got worse.
- **Possible effect:** the interval lies entirely below 0 and reaches -1 or lower.
- **Inconclusive:** the interval includes both 0 and -1 or lower. With 10 to 15 people this is a likely outcome and will be reported as such.
- **Not feasible:** fewer than 70% of enrolled people finish, or fewer than 60% of rating and diary days are completed. Then the effect estimate is reported but not interpreted.

Every result is published in the repository as a short report with the numbers above, whichever way it falls.

## 10. Limitations

- No control group: changes over the three weeks can come from expectation, season, workload or the habit of rating.
- The baseline always comes first, so order and time effects cannot be separated.
- Self-report only. No actigraphy, light sensor or body-clock measure, so the study cannot check the model's predictions of the body clock.
- Small sample from personal networks; not representative of all agents.

## 11. References

- Akerstedt T, Gillberg M (1990). Subjective and objective sleepiness in the active individual. International Journal of Neuroscience 52(1-2): 29-37. https://doi.org/10.3109/00207459008994241
- Kaida K, Takahashi M, Akerstedt T, et al. (2006). Validation of the Karolinska sleepiness scale against performance and EEG variables. Clinical Neurophysiology 117(7): 1574-1581. https://doi.org/10.1016/j.clinph.2006.03.011
- Carney CE, Buysse DJ, Ancoli-Israel S, et al. (2012). The consensus sleep diary: standardizing prospective sleep self-monitoring. Sleep 35(2): 287-302. https://doi.org/10.5665/sleep.1642
- Republic Act No. 10173, Data Privacy Act of 2012, Philippines.
