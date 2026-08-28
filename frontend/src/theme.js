import { useCallback, useSyncExternalStore } from "react";

export const THEME_STORAGE_KEY = "classyncal-theme";

const root = () => document.documentElement;

// The `dark` class on <html> is the single source of truth. The inline script in
// index.html sets it before first paint, so there is nothing to hand down through
// a provider - every caller of useTheme() reads the same value straight from the
// DOM, which is also what the static /privacy and /terms pages read.
function subscribe(onStoreChange) {
  const observer = new MutationObserver(onStoreChange);
  observer.observe(root(), { attributes: true, attributeFilter: ["class"] });
  return () => observer.disconnect();
}

function getSnapshot() {
  return root().classList.contains("dark") ? "dark" : "light";
}

export function setTheme(theme) {
  root().classList.toggle("dark", theme === "dark");
  // Native date/time pickers, select menus and scrollbars follow color-scheme
  // rather than any class. Without this the review modal's many date/time
  // inputs keep rendering light-on-light while everything around them is dark.
  root().style.colorScheme = theme;
}

// Follows the OS only until the user states a preference - once they use the
// toggle their stored choice wins and system changes stop being applied.
// Called once from main.jsx rather than on import, to keep this module free of
// side effects that fire just from being imported.
export function watchSystemTheme() {
  const media = window.matchMedia("(prefers-color-scheme: dark)");

  function handleChange(event) {
    if (readStoredTheme()) return;
    setTheme(event.matches ? "dark" : "light");
  }

  media.addEventListener("change", handleChange);
  return () => media.removeEventListener("change", handleChange);
}

function readStoredTheme() {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY);
  } catch {
    // Safari in private mode throws on storage access.
    return null;
  }
}

export function useTheme() {
  const theme = useSyncExternalStore(subscribe, getSnapshot, () => "light");

  const toggleTheme = useCallback(() => {
    const next = getSnapshot() === "dark" ? "light" : "dark";
    try {
      localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Storage is unavailable, so the choice lasts for this visit only.
    }
    setTheme(next);
  }, []);

  return { theme, toggleTheme };
}
