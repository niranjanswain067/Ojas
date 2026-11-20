import React, { useState, useEffect } from "react";
import {
  Save,
  RotateCcw,
  Sliders,
  Cpu,
  RefreshCw,
  Server,
  AlertCircle,
} from "lucide-react";
import type { Settings } from "../../api/types";

interface SettingsFormProps {
  initialSettings: Settings;
  saving: boolean;
  onSave: (updates: Partial<Settings>) => Promise<void>;
  onReset: () => void;
}

export const SettingsForm: React.FC<SettingsFormProps> = ({
  initialSettings,
  saving,
  onSave,
  onReset,
}) => {
  const [formData, setFormData] = useState<Settings>(initialSettings);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    setFormData(initialSettings);
    setIsDirty(false);
    setErrors({});
  }, [initialSettings]);

  const handleChange = (field: keyof Settings, value: string | number) => {
    setFormData((prev) => {
      const next = { ...prev, [field]: value };
      setIsDirty(JSON.stringify(next) !== JSON.stringify(initialSettings));
      return next;
    });

    // Validate field on change
    validateField(field, value);
  };

  const validateField = (field: keyof Settings, value: string | number) => {
    let err = "";
    if (field === "port") {
      const p = Number(value);
      if (isNaN(p) || p < 1024 || p > 65535) {
        err = "Port must be between 1024 and 65535";
      }
    } else if (field === "temperature") {
      const t = Number(value);
      if (isNaN(t) || t < 0.0 || t > 2.0) {
        err = "Temperature must be between 0.0 and 2.0";
      }
    } else if (field === "n_ctx") {
      const c = Number(value);
      if (isNaN(c) || c < 512 || c > 131072) {
        err = "Context size must be between 512 and 131072";
      }
    } else if (field === "n_threads") {
      const th = Number(value);
      if (isNaN(th) || th < 1 || th > 128) {
        err = "Threads must be at least 1";
      }
    } else if (field === "max_tokens") {
      const m = Number(value);
      if (isNaN(m) || m < 1) {
        err = "Max tokens must be positive";
      }
    } else if (field === "iteration_limit") {
      const it = Number(value);
      if (isNaN(it) || it < 1 || it > 50) {
        err = "Iteration limit must be between 1 and 50";
      }
    } else if (field === "test_timeout") {
      const to = Number(value);
      if (isNaN(to) || to < 5 || to > 600) {
        err = "Test timeout must be between 5s and 600s";
      }
    } else if (field === "editor_font_size") {
      const fs = Number(value);
      if (isNaN(fs) || fs < 8 || fs > 32) {
        err = "Editor font size must be between 8px and 32px";
      }
    }

    setErrors((prev) => {
      const next = { ...prev };
      if (err) next[field] = err;
      else delete next[field];
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (Object.keys(errors).length > 0) return;

    // Filter only changed fields
    const changes: Partial<Settings> = {};
    for (const key of Object.keys(formData) as (keyof Settings)[]) {
      if (formData[key] !== initialSettings[key]) {
        (changes as any)[key] = formData[key];
      }
    }

    if (Object.keys(changes).length === 0) return;
    await onSave(changes);
  };

  const modelReloadFields = ["model_path", "n_ctx", "n_threads", "n_batch", "n_gpu_layers"];
  const willTriggerReload = modelReloadFields.some(
    (field) => (formData as any)[field] !== (initialSettings as any)[field]
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Model Section */}
      <div className="bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-[#D5DBE3] dark:border-[#2D3541]">
          <div className="flex items-center gap-2">
            <Cpu size={18} className="text-[#1F3A5F] dark:text-[#6FA0E0]" />
            <h3 className="font-semibold text-sm text-[#1B2430] dark:text-[#E6EAF0]">
              LLM Inference Engine
            </h3>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-400">
            Model reload needed on change
          </span>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              GGUF Model File Path
            </label>
            <input
              type="text"
              value={formData.model_path}
              onChange={(e) => handleChange("model_path", e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] focus:ring-1 focus:ring-[#1F3A5F] dark:focus:ring-[#6FA0E0] outline-none"
              placeholder="models/your-model.gguf"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
                Context Window (tokens)
              </label>
              <input
                type="number"
                step="256"
                value={formData.n_ctx}
                onChange={(e) => handleChange("n_ctx", parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
              />
              {errors.n_ctx && <span className="text-[10px] text-red-500">{errors.n_ctx}</span>}
            </div>

            <div>
              <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
                CPU Threads
              </label>
              <input
                type="number"
                min="1"
                max="64"
                value={formData.n_threads}
                onChange={(e) => handleChange("n_threads", parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
              />
              {errors.n_threads && <span className="text-[10px] text-red-500">{errors.n_threads}</span>}
            </div>

            <div>
              <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
                GPU Layers Offload
              </label>
              <input
                type="number"
                min="0"
                max="128"
                value={formData.n_gpu_layers}
                onChange={(e) => handleChange("n_gpu_layers", parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
                Max Generated Tokens
              </label>
              <input
                type="number"
                step="128"
                min="128"
                value={formData.max_tokens}
                onChange={(e) => handleChange("max_tokens", parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
              />
              {errors.max_tokens && <span className="text-[10px] text-red-500">{errors.max_tokens}</span>}
            </div>

            <div>
              <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
                Temperature ({formData.temperature})
              </label>
              <input
                type="range"
                min="0.0"
                max="1.5"
                step="0.05"
                value={formData.temperature}
                onChange={(e) => handleChange("temperature", parseFloat(e.target.value))}
                className="w-full mt-2 accent-[#1F3A5F] dark:accent-[#6FA0E0]"
              />
              {errors.temperature && <span className="text-[10px] text-red-500">{errors.temperature}</span>}
            </div>

            <div>
              <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
                Batch Size (n_batch)
              </label>
              <input
                type="number"
                step="64"
                value={formData.n_batch}
                onChange={(e) => handleChange("n_batch", parseInt(e.target.value, 10))}
                className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Fix Loop Section */}
      <div className="bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-[#D5DBE3] dark:border-[#2D3541]">
          <Sliders size={18} className="text-[#1F3A5F] dark:text-[#6FA0E0]" />
          <h3 className="font-semibold text-sm text-[#1B2430] dark:text-[#E6EAF0]">
            Autonomous Fix Loop
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              Iteration Limit
            </label>
            <input
              type="number"
              min="1"
              max="20"
              value={formData.iteration_limit}
              onChange={(e) => handleChange("iteration_limit", parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
            />
            <p className="text-[11px] text-[#5F6B7A] dark:text-[#98A3B3] mt-1">
              Maximum develop-test-fix cycles before human escalation.
            </p>
            {errors.iteration_limit && <span className="text-[10px] text-red-500">{errors.iteration_limit}</span>}
          </div>

          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              Pytest Timeout (seconds)
            </label>
            <input
              type="number"
              min="10"
              max="300"
              value={formData.test_timeout}
              onChange={(e) => handleChange("test_timeout", parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
            />
            <p className="text-[11px] text-[#5F6B7A] dark:text-[#98A3B3] mt-1">
              Max duration allowed for a single pytest suite execution.
            </p>
            {errors.test_timeout && <span className="text-[10px] text-red-500">{errors.test_timeout}</span>}
          </div>
        </div>
      </div>

      {/* Server & General Section */}
      <div className="bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-[#D5DBE3] dark:border-[#2D3541]">
          <Server size={18} className="text-[#1F3A5F] dark:text-[#6FA0E0]" />
          <h3 className="font-semibold text-sm text-[#1B2430] dark:text-[#E6EAF0]">
            Host & Server Configuration
          </h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              Host
            </label>
            <input
              type="text"
              value={formData.host}
              onChange={(e) => handleChange("host", e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              Port
            </label>
            <input
              type="number"
              value={formData.port}
              onChange={(e) => handleChange("port", parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
            />
            {errors.port && <span className="text-[10px] text-red-500">{errors.port}</span>}
          </div>

          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              Editor Font Size (px)
            </label>
            <input
              type="number"
              min="8"
              max="32"
              value={formData.editor_font_size || 14}
              onChange={(e) => handleChange("editor_font_size", parseInt(e.target.value, 10))}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
            />
            {errors.editor_font_size && (
              <span className="text-[10px] text-red-500">{errors.editor_font_size}</span>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-[#1B2430] dark:text-[#E6EAF0] mb-1">
              Log Verbosity
            </label>
            <select
              value={formData.log_level}
              onChange={(e) => handleChange("log_level", e.target.value)}
              className="w-full px-3 py-2 bg-white dark:bg-[#14181F] border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-mono text-[#1B2430] dark:text-[#E6EAF0] outline-none"
            >
              <option value="debug">debug</option>
              <option value="info">info</option>
              <option value="warning">warning</option>
              <option value="error">error</option>
            </select>
          </div>
        </div>
      </div>

      {/* Warnings & Action Footer */}
      {willTriggerReload && (
        <div className="flex items-center gap-2 p-3 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-xl text-xs text-amber-800 dark:text-amber-300">
          <AlertCircle size={16} className="shrink-0" />
          <span>
            Saving these changes will trigger a <strong>model reload</strong> in the backend.
          </span>
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={onReset}
          disabled={!isDirty || saving}
          className="flex items-center gap-1.5 px-4 py-2 border border-[#D5DBE3] dark:border-[#2D3541] rounded-lg text-xs font-medium text-[#5F6B7A] dark:text-[#98A3B3] hover:text-[#1B2430] dark:hover:text-[#E6EAF0] hover:bg-white dark:hover:bg-gray-800 transition disabled:opacity-40"
        >
          <RotateCcw size={14} />
          <span>Reset Changes</span>
        </button>

        <button
          type="submit"
          disabled={!isDirty || Object.keys(errors).length > 0 || saving}
          className="flex items-center gap-1.5 px-5 py-2.5 bg-[#1F3A5F] hover:bg-[#1F3A5F]/90 dark:bg-[#6FA0E0] dark:hover:bg-[#6FA0E0]/90 text-white dark:text-[#14181F] rounded-lg text-xs font-semibold shadow-sm transition disabled:opacity-40"
        >
          {saving ? (
            <>
              <RefreshCw size={14} className="animate-spin" />
              <span>Saving & Applying…</span>
            </>
          ) : (
            <>
              <Save size={14} />
              <span>Save Configuration</span>
            </>
          )}
        </button>
      </div>
    </form>
  );
};
