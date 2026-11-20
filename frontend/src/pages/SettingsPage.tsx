import React, { useEffect, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Sliders } from 'lucide-react';
import type { HealthResponse, Settings, ThemeMode } from '../api/types';
import { apiGet, apiPut } from '../api/client';
import { SettingsForm } from '../components/settings/SettingsForm';
import { HealthCard } from '../components/settings/HealthCard';
import { ThemeToggle } from '../components/settings/ThemeToggle';
import { applyTheme, getStoredTheme } from '../app/theme';
import type { SettingsUpdateResponse } from '../api/types';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [healthLoading, setHealthLoading] = useState<boolean>(false);
  const [notification, setNotification] = useState<{
    type: 'success' | 'warning' | 'error';
    message: string;
  } | null>(null);

  const [currentTheme, setCurrentTheme] = useState<ThemeMode>(() => getStoredTheme());

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [settingsData, healthData] = await Promise.all([
        apiGet<Settings>('/settings'),
        apiGet<HealthResponse>('/health'),
      ]);
      setSettings(settingsData);
      setHealth(healthData);
      if (settingsData.theme) {
        setCurrentTheme(settingsData.theme as ThemeMode);
        applyTheme(settingsData.theme as ThemeMode);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setNotification({
        type: 'error',
        message: `Failed to load settings or health: ${message}`,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshHealth = useCallback(async () => {
    setHealthLoading(true);
    try {
      const healthData = await apiGet<HealthResponse>('/health');
      setHealth(healthData);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setNotification({
        type: 'error',
        message: `Failed to refresh health: ${message}`,
      });
    } finally {
      setHealthLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSave = async (updates: Partial<Settings>) => {
    setSaving(true);
    setNotification(null);
    try {
      const res = await apiPut<SettingsUpdateResponse>('/settings', updates);
      setSettings(res.settings);

      if (res.model_reload_required) {
        if (res.model_reload_status === 'reloaded') {
          setNotification({
            type: 'success',
            message: 'Settings saved! LLM model was reloaded successfully.',
          });
        } else if (res.model_reload_status === 'error') {
          setNotification({
            type: 'warning',
            message: 'Settings saved, but LLM model could not be loaded. Check model path.',
          });
        }
        await refreshHealth();
      } else {
        setNotification({
          type: 'success',
          message: 'Settings saved successfully.',
        });
      }

      if (updates.theme) {
        setCurrentTheme(updates.theme as ThemeMode);
        applyTheme(updates.theme as ThemeMode);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setNotification({
        type: 'error',
        message: `Failed to update settings: ${message}`,
      });
    } finally {
      setSaving(false);
    }
  };

  const handleThemeChange = async (newTheme: ThemeMode) => {
    setCurrentTheme(newTheme);
    applyTheme(newTheme);
    try {
      const res = await apiPut<SettingsUpdateResponse>('/settings', { theme: newTheme });
      setSettings(res.settings);
    } catch {
      // theme saved locally even if backend call fails
    }
  };

  if (loading && !settings) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-muted">
            Loading settings and system status…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-text flex items-center gap-2">
          <Sliders className="text-primary" size={24} />
          <span>Application Settings</span>
        </h1>
        <p className="text-xs sm:text-sm text-muted mt-1">
          Configure offline model inference, autonomous fix loop constraints, and UI appearance.
        </p>
      </div>

      {/* Notification Banner */}
      {notification && (
        <div
          className={`flex items-start justify-between gap-3 p-4 rounded-xl text-xs border ${
            notification.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
              : notification.type === 'warning'
              ? 'bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800'
              : 'bg-red-50 text-red-800 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {notification.type === 'success' && <CheckCircle2 size={16} />}
            {notification.type === 'warning' && <AlertTriangle size={16} />}
            {notification.type === 'error' && <XCircle size={16} />}
            <span>{notification.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setNotification(null)}
            className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-sm leading-none"
          >
            ×
          </button>
        </div>
      )}

      {/* Main Grid: Form on left, Health & Theme on right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {settings && (
            <SettingsForm
              initialSettings={settings}
              saving={saving}
              onSave={handleSave}
              onReset={() => setSettings({ ...settings })}
            />
          )}
        </div>

        <div className="space-y-6">
          <ThemeToggle
            currentTheme={currentTheme}
            onThemeChange={handleThemeChange}
          />

          <HealthCard
            health={health}
            loading={healthLoading}
            onRefresh={refreshHealth}
          />
        </div>
      </div>
    </div>
  );
};
