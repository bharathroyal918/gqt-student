import React, { useState } from "react";
import { Outlet, NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  BookOpen,
  Code2,
  CalendarCheck,
  Sparkles,
} from "lucide-react";
import { StudentSidebar } from "./StudentSidebar";
import { StudentHeader } from "./StudentHeader";

export const StudentLayout: React.FC = () => {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Quick mobile bottom bar items for high-frequency student tasks
  const mobileBarItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Courses", href: "/courses", icon: BookOpen },
    { name: "Assignments", href: "/assignments", icon: Code2 },
    { name: "Tasks", href: "/tasks", icon: CalendarCheck },
    { name: "Help AI", href: "/help-ai", icon: Sparkles },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-950 font-sans text-slate-100">
      {/* Sidebar (Desktop + Mobile Drawer) */}
      <StudentSidebar
        isOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <StudentHeader onToggleMobileSidebar={() => setIsMobileSidebarOpen((prev) => !prev)} />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 pb-20 lg:pb-8">
          <Outlet />
        </main>

        {/* Mobile Bottom Navigation Bar (Visible only on small screens) */}
        <nav
          aria-label="Mobile Navigation"
          className="fixed bottom-0 inset-x-0 z-30 border-t border-surface-800 bg-surface-950/95 px-3 py-2 backdrop-blur-lg lg:hidden flex items-center justify-around"
        >
          {mobileBarItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-1 py-1 px-2.5 rounded-xl text-[10px] font-medium transition-all ${
                    isActive
                      ? "text-brand-400 font-semibold"
                      : "text-slate-400 hover:text-slate-200"
                  }`
                }
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
