// Theme choice: dark by default. The choice (the word "light" or "dark") is the only thing
// the site keeps in the browser; schedules and plans are never stored.

export type Theme = "dark" | "light";
export const THEME_KEY = "zeitgeber-theme";

/** Runs before first paint so a saved light theme does not flash dark. */
export const themeScript = `try{var t=localStorage.getItem("${THEME_KEY}");if(t==="light"||t==="dark")document.documentElement.dataset.theme=t}catch(e){}`;

export function readTheme(): Theme {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    // storage blocked: the choice lasts for this page only
  }
}
