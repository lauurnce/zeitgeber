const productionHost = process.env.VERCEL_PROJECT_PRODUCTION_URL;

export const site = {
  name: "Zeitgeber",
  tagline: "A body-clock planner for night-shift workers.",
  description:
    "Zeitgeber turns your shift schedule into a 14-day plan for light, sleep and caffeine, using published models of the human body clock. Free, and your schedule is not stored.",
  url:
    process.env.NEXT_PUBLIC_SITE_URL ??
    (productionHost ? `https://${productionHost}` : "http://localhost:3000"),
  github: "https://github.com/lauurnce/zeitgeber",
  science: "https://github.com/lauurnce/zeitgeber/blob/main/docs/SCIENCE.md",
  author: "Lawrence Panes",
  authorUrl: "https://lauurnce.is-a.dev",
  notice:
    "Zeitgeber is a wellness planning tool, not medical advice. If you have a sleep condition, are pregnant or have a health condition, talk to a doctor.",
  privacy: "Your schedule is used to make this plan and isn't stored.",
} as const;
