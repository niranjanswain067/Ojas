import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  type ThemeMode,
  type ResolvedTheme,
  getStoredTheme,
  getSystemTheme,
  applyThemeToDocument,
  THEME_STORAGE_KEY,
} from './theme';

interface ThemeContextValue {
  theme: ThemeMode;
  resolvedTheme: ResolvedTheme;
  setTheme: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>(() => getStoredTheme());
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() =>
    theme === 'system' ? getSystemTheme() : theme
  );

  const setTheme = (mode: ThemeMode) => {
    setThemeState(mode);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch {
      // ignore localstorage errors
    }
  };

  useEffect(() => {
    const handleSystemChange = () => {
      if (theme === 'system') {
        const sys = getSystemTheme();
        setResolvedTheme(sys);
        applyThemeToDocument(sys);
      }
    };

    const mediaQuery = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
    mediaQuery?.addEventListener?.('change', handleSystemChange);

    const activeResolved = theme === 'system' ? getSystemTheme() : theme;
    setResolvedTheme(activeResolved);
    applyThemeToDocument(activeResolved);

    return () => {
      mediaQuery?.removeEventListener?.('change', handleSystemChange);
    };
  }, [theme]);

  const value = useMemo(
    () => ({
      theme,
      resolvedTheme,
      setTheme,
    }),
    [theme, resolvedTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5000,
        refetchOnWindowFocus: false,
        retry: 1,
      },
    },
  });
}

interface ProvidersProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
}

export function Providers({ children, queryClient }: ProvidersProps) {
  const client = useMemo(() => queryClient ?? createQueryClient(), [queryClient]);

  return (
    <QueryClientProvider client={client}>
      <ThemeProvider>{children}</ThemeProvider>
    </QueryClientProvider>
  );
}

