/**
 * Theme tokens and utilities based on 03_UI_Design.md §8.2.
 */

export type ThemeMode = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

export interface ThemeColors {
  bg: string;
  surface: string;
  border: string;
  text: string;
  muted: string;
  primary: string;
  success: string;
  warning: string;
  danger: string;
  llm: string;
}

export const LIGHT_THEME: ThemeColors = {
  bg: '#FFFFFF',
  surface: '#F5F7FA',
  border: '#D5DBE3',
  text: '#1B2430',
  muted: '#5F6B7A',
  primary: '#1F3A5F',
  success: '#2E7D32',
  warning: '#B26A00',
  danger: '#C62828',
  llm: '#F8E3C5',
};

export const DARK_THEME: ThemeColors = {
  bg: '#14181F',
  surface: '#1C222B',
  border: '#2D3541',
  text: '#E6EAF0',
  muted: '#98A3B3',
  primary: '#6FA0E0',
  success: '#66BB6A',
  warning: '#FFB74D',
  danger: '#EF5350',
  llm: '#4A3A22',
};

export const THEME_STORAGE_KEY = 'ojas-theme';

export function getSystemTheme(): ResolvedTheme {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return 'dark';
  }
  try {
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    return mql?.matches ? 'dark' : 'light';
  } catch {
    return 'dark';
  }
}

export function getStoredTheme(): ThemeMode {
  if (typeof window === 'undefined') {
    return 'system';
  }
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null;
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
  } catch {
    // ignore
  }
  return 'system';
}

export function applyThemeToDocument(theme: ResolvedTheme): void {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
}
