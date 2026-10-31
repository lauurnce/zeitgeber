import { site } from "@/lib/site";

import { ExternalLink, Section } from "./ui";

const GROUPS: { title: string; items: [string, string][] }[] = [
  {
    title: "Body-clock models",
    items: [
      [
        "Forger DB, Jewett ME, Kronauer RE (1999). A simpler model of the human circadian pacemaker. Journal of Biological Rhythms 14: 532-537.",
        "https://doi.org/10.1177/074873099129000867",
      ],
      [
        "Jewett ME, Forger DB, Kronauer RE (1999). Revised limit cycle oscillator model of human circadian pacemaker. Journal of Biological Rhythms 14: 493-499.",
        "https://doi.org/10.1177/074873049901400608",
      ],
      [
        "Hannay KM, Booth V, Forger DB (2019). Macroscopic models for human circadian rhythms. Journal of Biological Rhythms 34: 658-671.",
        "https://doi.org/10.1177/0748730419878298",
      ],
      [
        "Arcascope. circadian 1.0.3, the open-source package that runs the models.",
        "https://github.com/Arcascope/circadian",
      ],
    ],
  },
  {
    title: "How light moves the clock",
    items: [
      [
        "Khalsa SBS, Jewett ME, Cajochen C, Czeisler CA (2003). A phase response curve to single bright light pulses in human subjects. Journal of Physiology 549: 945-952.",
        "https://doi.org/10.1113/jphysiol.2003.040477",
      ],
      [
        "Czeisler CA et al. (1999). Stability, precision, and near-24-hour period of the human circadian pacemaker. Science 284: 2177-2181.",
        "https://doi.org/10.1126/science.284.5423.2177",
      ],
    ],
  },
  {
    title: "Night-shift strategies",
    items: [
      [
        "Crowley SJ, Lee C, Tseng CY, Fogg LF, Eastman CI (2003). Journal of Biological Rhythms 18: 513-523.",
        "https://doi.org/10.1177/0748730403258422",
      ],
      [
        "Smith MR, Fogg LF, Eastman CI (2009). A compromise circadian phase position for permanent night work improves mood, fatigue, and performance. Sleep 32: 1481-1489.",
        "https://doi.org/10.1093/sleep/32.11.1481",
      ],
      [
        "Smith MR, Eastman CI (2012). Shift work: health, performance and safety problems, traditional countermeasures, and innovative management strategies to reduce circadian misalignment. Nature and Science of Sleep 4: 111-132.",
        "https://doi.org/10.2147/NSS.S10372",
      ],
    ],
  },
  {
    title: "Caffeine and naps",
    items: [
      [
        "Drake C, Roehrs T, Shambroom J, Roth T (2013). Caffeine effects on sleep taken 0, 3, or 6 hours before going to bed. Journal of Clinical Sleep Medicine 9: 1195-1200.",
        "https://doi.org/10.5664/jcsm.3170",
      ],
      [
        "Ruggiero JS, Redeker NS (2014). Effects of napping on sleepiness and sleep-related performance deficits in night-shift workers: a systematic review. Biological Research for Nursing 16: 134-142.",
        "https://doi.org/10.1177/1099800413476571",
      ],
    ],
  },
];

export function Science() {
  return (
    <Section id="science" eyebrow="The science" title="Built on published work">
      <p className="max-w-2xl text-lg">
        Every model, light level and rule in Zeitgeber comes from a cited source. Values that could
        not be checked against a source are marked as unverified.{" "}
        <ExternalLink href={site.science}>Read the full science notes on GitHub</ExternalLink>.
      </p>
      <div className="mt-8 grid gap-8 md:grid-cols-2">
        {GROUPS.map((g) => (
          <div key={g.title}>
            <h3 className="text-lg font-semibold">{g.title}</h3>
            <ul className="mt-3 flex flex-col gap-3 text-sm text-[var(--muted)]">
              {g.items.map(([text, href]) => (
                <li key={href}>
                  <ExternalLink href={href}>{text}</ExternalLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Section>
  );
}
