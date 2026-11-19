import { ThemeMode } from "../api/types";

const THEME_STORAGE_KEY = "ojas_theme";

export function getSystemTheme(): "light" | "dark" {
  if (typeof window !== "undefined" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

export function applyTheme(mode: ThemeMode): void {
  if (typeof document === "undefined") return;

  const root = document.documentElement;
  const isDark = mode === "dark" || (mode === "system" && getSystemTheme() === "dark");

  if (isDark) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }

  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode);
  } catch {
    // localStorage may be disabled
  }
}

export function getInitialTheme(defaultSettingTheme: ThemeMode = "system"): ThemeMode {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null;
    if (saved && (saved === "light" || saved === "dark" || saved === "system")) {
      return saved;
    }
  } catch {
    // fallback
  }
  return defaultSettingTheme;
}

