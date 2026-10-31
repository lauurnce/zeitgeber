import { ExternalLink, Section } from "./ui";

export function Story() {
  return (
    <Section id="story" eyebrow="The name" title="A bunker, a clock and a word">
      <div className="max-w-2xl font-serif text-lg leading-relaxed sm:text-xl">
        <p>
          In 1954 the physiologist Jürgen Aschoff used the word <em>Zeitgeber</em>, German for
          &ldquo;time giver&rdquo;, for the outside cues that set a living clock. Sunlight is the
          strongest one.
        </p>
        <p className="mt-4">
          To see what the human clock does without them, Aschoff and Rütger Wever of the Max Planck
          Institute had a windowless bunker built in Andechs, Bavaria, and Aschoff went in first.
          Volunteers lived there with no clocks and no daylight. Their days drifted longer than 24
          hours, to about 25.
        </p>
        <p className="mt-4">
          The body keeps its own time, and light keeps it on schedule. Night-shift workers get their
          strongest Zeitgeber at the wrong hour.
        </p>
      </div>
      <p className="mt-6 text-sm text-[var(--muted)]">
        Sources:{" "}
        <ExternalLink href="https://doi.org/10.1126/science.148.3676.1427">
          Aschoff J (1965), Circadian rhythms in man, Science 148: 1427-1432
        </ExternalLink>
        ; on the bunker,{" "}
        <ExternalLink href="https://en.wikipedia.org/wiki/Bunker_experiment">
          Bunker experiment, Wikipedia
        </ExternalLink>
        .
      </p>
    </Section>
  );
}
