import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { TPOSidebar } from "./TPOSidebar";
import { TPOHeader } from "./TPOHeader";

export const TPOLayout: React.FC = () => {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-surface-950 font-sans text-slate-900 dark:text-slate-100">
      {/* Sidebar */}
      <TPOSidebar
        isOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Content Pane */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <TPOHeader onToggleMobileSidebar={() => setIsMobileSidebarOpen((prev) => !prev)} />
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
