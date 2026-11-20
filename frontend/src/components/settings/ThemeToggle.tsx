import React from "react";
import { Sun, Moon, Laptop } from "lucide-react";
import type { ThemeMode } from "../../api/types";
import { applyTheme } from "../../app/theme";

interface ThemeToggleProps {
  currentTheme: ThemeMode;
  onThemeChange?: (newTheme: ThemeMode) => void;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  currentTheme,
  onThemeChange,
}) => {
  const handleSelect = (mode: ThemeMode) => {
    applyTheme(mode);
    if (onThemeChange) {
      onThemeChange(mode);
    }
  };

  const options: { mode: ThemeMode; label: string; icon: typeof Sun }[] = [
    { mode: "light", label: "Light", icon: Sun },
    { mode: "dark", label: "Dark", icon: Moon },
    { mode: "system", label: "System", icon: Laptop },
  ];

  return (
    <div className="bg-[#F5F7FA] dark:bg-[#1C222B] border border-[#D5DBE3] dark:border-[#2D3541] rounded-xl p-4 shadow-sm">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-[#1B2430] dark:text-[#E6EAF0]">
          Appearance
        </h3>
        <p className="text-xs text-[#5F6B7A] dark:text-[#98A3B3]">
          Choose your interface color scheme or match your operating system.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-2 bg-[#FFFFFF] dark:bg-[#14181F] p-1.5 rounded-lg border border-[#D5DBE3] dark:border-[#2D3541]">
        {options.map(({ mode, label, icon: Icon }) => {
          const isActive = currentTheme === mode;
          return (
            <button
              key={mode}
              type="button"
              onClick={() => handleSelect(mode)}
              className={`flex items-center justify-center gap-1.5 py-2 px-3 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? "bg-[#1F3A5F] text-white dark:bg-[#6FA0E0] dark:text-[#14181F] shadow-sm"
                  : "text-[#5F6B7A] dark:text-[#98A3B3] hover:text-[#1B2430] dark:hover:text-[#E6EAF0] hover:bg-gray-100 dark:hover:bg-gray-800/60"
              }`}
            >
              <Icon size={14} />
              <span>{label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

