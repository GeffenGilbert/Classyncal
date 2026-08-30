import { useCallback, useSyncExternalStore } from "react";

export const THEME_STORAGE_KEY = "classyncal-theme";

const root = () => document.documentElement;

// The `dark` class on <html> is the single source of truth. The inline script in
// index.html sets it before first paint, so there is nothing to hand down through
// a provider - every caller of useTheme() reads the same value straight from the
// DOM, which is also what the static /privacy and /terms pages read.
//
// Light is the default and dark is opt-in: the OS preference is deliberately not
// consulted, so a visitor on a dark-themed machine still lands on the light site.
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
