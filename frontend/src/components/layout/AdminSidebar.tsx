import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  BookOpen,
  FolderKanban,
  FileCheck,
  Award,
  Bell,
  BarChart3,
  HelpCircle,
  FileText,
} from "lucide-react";
import { BrandLogo } from "../common/BrandLogo";

interface AdminSidebarProps {
  isOpen: boolean;
  onCloseMobile: () => void;
}

export const AdminSidebar: React.FC<AdminSidebarProps> = ({ isOpen, onCloseMobile }) => {
  const navItems = [
    { name: "Dashboard", href: "/admin/dashboard", icon: LayoutDashboard },
    { name: "Students", href: "/admin/students", icon: Users },
    { name: "Courses", href: "/admin/courses", icon: BookOpen },
    { name: "Assignments", href: "/admin/assignments", icon: FileCheck },
    { name: "Daily Tasks", href: "/admin/tasks", icon: FolderKanban },
    { name: "Projects", href: "/admin/projects", icon: FolderKanban },
    { name: "Certificates", href: "/admin/certificates", icon: Award },
    { name: "Announcements", href: "/admin/announcements", icon: Bell },
    { name: "Inquiries", href: "/admin/inquiries", icon: HelpCircle },
    { name: "Analytics", href: "/admin/analytics", icon: BarChart3 },
    { name: "Reports", href: "/admin/reports", icon: FileText },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 dark:border-surface-800 bg-white dark:bg-surface-950 transition-all duration-300 lg:static lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand Logo Header */}
        <div className="flex h-16 shrink-0 items-center border-b border-slate-200 dark:border-surface-800 px-5 bg-white dark:bg-surface-950">
          <BrandLogo
            variant="sidebar"
            badge="Admin"
            badgeVariant="admin"
            subtitle="Global Quest Technologies"
          />
        </div>

        {/* Navigation links */}
        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  `group flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-brand-600 text-white shadow-md shadow-brand-500/25 font-semibold"
                      : "text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-surface-900 hover:text-slate-900 dark:hover:text-white"
                  }`
                }
              >
                <Icon className="h-4 w-4 shrink-0 transition-transform duration-150 group-hover:scale-110" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Environment footer */}
        <div className="border-t border-slate-200 dark:border-surface-800 p-4">
          <div className="rounded-xl border border-slate-200 dark:border-surface-800/80 bg-slate-50 dark:bg-surface-900/60 p-3 text-xs">
            <div className="flex items-center justify-between text-slate-600 dark:text-slate-400">
              <span>Platform</span>
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">Production</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500">
              <span>API Gateway</span>
              <span>v1 REST</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
