import { ExternalLink, Section } from "./ui";

export function Problem() {
  return (
    <Section id="problem" eyebrow="The problem" title="The sun rises on your way home">
      <div className="grid gap-10 lg:grid-cols-[1fr_1.2fr]">
        <div>
          <p className="font-serif text-6xl font-semibold text-[var(--accent)]">1.9 million</p>
          <p className="mt-2 text-lg">
            people worked in Philippine IT-BPM in 2025, according to the industry group IBPAP (
            <ExternalLink href="https://www.philstar.com/business/2026/01/29/2504140/it-bpm-revenues-breach-40-billion-mark">
              Philstar, 29 January 2026
            </ExternalLink>
            ).
          </p>
        </div>
        <div className="flex flex-col gap-4 text-lg leading-relaxed">
          <p>
            Many of them serve customers in United States time zones, so their shifts run through
            the Manila night and end around sunrise.
          </p>
          <p>
            Bright morning light is the signal that tells the body clock it is morning. On a sunny
            commute home it pulls the clock back toward a daytime schedule just before you try to
            sleep, so day sleep comes short and broken.
          </p>
          <p>
            Studies of simulated night work found that bright light at work, dark sunglasses on the
            way home and sleep in a dark room help the clock settle where night work and day sleep
            both fit (
            <ExternalLink href="https://doi.org/10.1177/0748730403258422">
              Crowley 2003
            </ExternalLink>
            ;{" "}
            <ExternalLink href="https://doi.org/10.2147/NSS.S10372">
              Smith and Eastman 2012
            </ExternalLink>
            ).
          </p>
        </div>
      </div>
    </Section>
  );
}
