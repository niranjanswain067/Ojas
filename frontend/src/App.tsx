import React, { useState } from "react";
import { AppShell } from "./components/shared/AppShell";
import { SettingsPage } from "./pages/SettingsPage";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<
    "projects" | "workspace" | "reports" | "settings"
  >("settings");

  return (
    <AppShell activeTab={activeTab} onTabChange={setActiveTab}>
      {activeTab === "settings" && <SettingsPage />}
      {activeTab === "projects" && (
        <div className="max-w-4xl mx-auto py-12 px-4 text-center">
          <h2 className="text-lg font-bold text-[#1B2430] dark:text-[#E6EAF0]">
            Projects
          </h2>
          <p className="text-xs text-[#5F6B7A] dark:text-[#98A3B3] mt-2">
            Projects module is scheduled for Phase 8.
          </p>
        </div>
      )}
      {activeTab === "workspace" && (
        <div className="max-w-4xl mx-auto py-12 px-4 text-center">
          <h2 className="text-lg font-bold text-[#1B2430] dark:text-[#E6EAF0]">
            Workspace
          </h2>
          <p className="text-xs text-[#5F6B7A] dark:text-[#98A3B3] mt-2">
            Workspace module is scheduled for Phase 10.
          </p>
        </div>
      )}
      {activeTab === "reports" && (
        <div className="max-w-4xl mx-auto py-12 px-4 text-center">
          <h2 className="text-lg font-bold text-[#1B2430] dark:text-[#E6EAF0]">
            Reports
          </h2>
          <p className="text-xs text-[#5F6B7A] dark:text-[#98A3B3] mt-2">
            Reports module is scheduled for Phase 19.
          </p>
        </div>
      )}
    </AppShell>
  );
};

export default App;

