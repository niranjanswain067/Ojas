import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { Providers, useTheme } from './providers';
import { THEME_STORAGE_KEY } from './theme';

function TestThemeConsumer() {
  const { theme, resolvedTheme, setTheme } = useTheme();
  return (
    <div>
      <span data-testid="theme-val">{theme}</span>
      <span data-testid="resolved-val">{resolvedTheme}</span>
      <button onClick={() => setTheme('light')}>Set Light</button>
      <button onClick={() => setTheme('dark')}>Set Dark</button>
      <button onClick={() => setTheme('system')}>Set System</button>
    </div>
  );
}

describe('Providers and ThemeContext', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('provides theme and changes mode', () => {
    render(
      <Providers>
        <TestThemeConsumer />
      </Providers>
    );

    expect(screen.getByTestId('theme-val').textContent).toBe('system');

    act(() => {
      screen.getByText('Set Light').click();
    });

    expect(screen.getByTestId('theme-val').textContent).toBe('light');
    expect(screen.getByTestId('resolved-val').textContent).toBe('light');
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light');
    expect(document.documentElement.classList.contains('dark')).toBe(false);

    act(() => {
      screen.getByText('Set Dark').click();
    });

    expect(screen.getByTestId('theme-val').textContent).toBe('dark');
    expect(screen.getByTestId('resolved-val').textContent).toBe('dark');
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark');
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});

