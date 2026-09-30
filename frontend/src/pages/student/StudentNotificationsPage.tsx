import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Bell,
  CheckCheck,
  Megaphone,
  Calendar,
  Clock,
  Award,
  BookOpen,
  CheckCircle2,
  Trash2,
  ExternalLink,
  Flame,
  FileCheck,
  TrendingUp,
  Info,
} from "lucide-react";
import {
  studentApi,
  StudentNotificationItem,
  StudentAnnouncementItem,
} from "../../api/studentApi";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { EmptyState } from "../../components/ui/EmptyState";

type TabType = "all" | "unread" | "announcements" | "tasks" | "projects" | "achievements";

export const StudentNotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabType>("all");

  // 1. Fetch Notifications
  const {
    data: notifData,
    isLoading: isNotifLoading,
  } = useQuery({
    queryKey: ["student", "notifications"],
    queryFn: () => studentApi.getNotifications(),
  });

  // 2. Fetch Announcements
  const {
    data: announcements = [],
    isLoading: isAnnouncementsLoading,
  } = useQuery({
    queryKey: ["student", "announcements"],
    queryFn: studentApi.getAnnouncements,
  });

  const notifications = notifData?.notifications || [];
  const unreadCount = notifData?.unread_count || 0;

  // 3. Mark Single Read Mutation
  const markReadMutation = useMutation({
    mutationFn: (id: string) => studentApi.markNotificationAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student", "notifications"] });
      queryClient.invalidateQueries({ queryKey: ["student", "notifications", "unread-count"] });
    },
  });

  // 4. Mark All Read Mutation
  const markAllReadMutation = useMutation({
    mutationFn: () => studentApi.markAllNotificationsAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student", "notifications"] });
      queryClient.invalidateQueries({ queryKey: ["student", "notifications", "unread-count"] });
    },
  });

  // 5. Delete Notification Mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => studentApi.deleteNotification(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["student", "notifications"] });
      queryClient.invalidateQueries({ queryKey: ["student", "notifications", "unread-count"] });
    },
  });

  // Filter notifications based on tab
  const filteredNotifications = notifications.filter((n) => {
    if (activeTab === "all") return true;
    if (activeTab === "unread") return !n.is_read;
    if (activeTab === "tasks") {
      return (
        n.notification_type === "TASK_DEADLINE" ||
        n.notification_type === "DEADLINE_REMINDER" ||
        n.notification_type === "TASK_COMPLETED"
      );
    }
    if (activeTab === "projects") {
      return (
        n.notification_type === "PROJECT_MARKED" ||
        n.notification_type === "PROJECT_FEEDBACK" ||
        n.notification_type === "SUBMISSION_GRADED"
      );
    }
    if (activeTab === "achievements") {
      return (
        n.notification_type === "ACHIEVEMENT" ||
        n.notification_type === "CERTIFICATE" ||
        n.notification_type === "RANK_CHANGE" ||
        n.notification_type === "STREAK_ALERT"
      );
    }
    return true;
  });

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case "TASK_DEADLINE":
      case "DEADLINE_REMINDER":
        return <Clock className="h-5 w-5 text-amber-400" />;
      case "PROJECT_MARKED":
      case "PROJECT_FEEDBACK":
      case "SUBMISSION_GRADED":
        return <FileCheck className="h-5 w-5 text-emerald-400" />;
      case "RANK_CHANGE":
        return <TrendingUp className="h-5 w-5 text-indigo-400" />;
      case "ACHIEVEMENT":
      case "CERTIFICATE":
        return <Award className="h-5 w-5 text-purple-400" />;
      case "MODULE_UNLOCKED":
        return <BookOpen className="h-5 w-5 text-blue-400" />;
      case "STREAK_ALERT":
        return <Flame className="h-5 w-5 text-rose-400" />;
      case "ADMIN_ANNOUNCEMENT":
        return <Megaphone className="h-5 w-5 text-amber-400" />;
      default:
        return <Info className="h-5 w-5 text-brand-400" />;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "URGENT":
        return <Badge variant="rose">Urgent</Badge>;
      case "HIGH":
        return <Badge variant="amber">High Priority</Badge>;
      case "NORMAL":
        return <Badge variant="indigo">Normal</Badge>;
      default:
        return <Badge variant="slate">General</Badge>;
    }
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Bell className="h-6 w-6 text-brand-400" />
            Notifications & Announcements
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Real-time curriculum alerts, grading results, deadline reminders, and cohort updates.
          </p>
        </div>

        {unreadCount > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
            className="flex items-center gap-2 self-start sm:self-auto text-xs"
          >
            <CheckCheck className="h-4 w-4 text-brand-400" />
            <span>Mark all as read ({unreadCount})</span>
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-surface-800 text-xs">
        <button
          onClick={() => setActiveTab("all")}
          className={`px-3 py-2 rounded-xl font-medium transition-all shrink-0 flex items-center gap-1.5 ${
            activeTab === "all"
              ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
              : "text-slate-400 hover:text-white hover:bg-surface-800"
          }`}
        >
          <span>All Alerts</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-800 text-slate-300">
            {notifications.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("unread")}
          className={`px-3 py-2 rounded-xl font-medium transition-all shrink-0 flex items-center gap-1.5 ${
            activeTab === "unread"
              ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
              : "text-slate-400 hover:text-white hover:bg-surface-800"
          }`}
        >
          <span>Unread</span>
          {unreadCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-brand-500 text-white font-bold">
              {unreadCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab("announcements")}
          className={`px-3 py-2 rounded-xl font-medium transition-all shrink-0 flex items-center gap-1.5 ${
            activeTab === "announcements"
              ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
              : "text-slate-400 hover:text-white hover:bg-surface-800"
          }`}
        >
          <Megaphone className="h-3.5 w-3.5 text-amber-400" />
          <span>Announcements</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-surface-800 text-slate-300">
            {announcements.length}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("tasks")}
          className={`px-3 py-2 rounded-xl font-medium transition-all shrink-0 flex items-center gap-1.5 ${
            activeTab === "tasks"
              ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
              : "text-slate-400 hover:text-white hover:bg-surface-800"
          }`}
        >
          <Clock className="h-3.5 w-3.5 text-amber-400" />
          <span>Deadlines & Tasks</span>
        </button>

        <button
          onClick={() => setActiveTab("projects")}
          className={`px-3 py-2 rounded-xl font-medium transition-all shrink-0 flex items-center gap-1.5 ${
            activeTab === "projects"
              ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
              : "text-slate-400 hover:text-white hover:bg-surface-800"
          }`}
        >
          <FileCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span>Grades & Projects</span>
        </button>

        <button
          onClick={() => setActiveTab("achievements")}
          className={`px-3 py-2 rounded-xl font-medium transition-all shrink-0 flex items-center gap-1.5 ${
            activeTab === "achievements"
              ? "bg-brand-500/10 text-brand-400 border border-brand-500/20"
              : "text-slate-400 hover:text-white hover:bg-surface-800"
          }`}
        >
          <Award className="h-3.5 w-3.5 text-purple-400" />
          <span>Achievements</span>
        </button>
      </div>

      {/* Main Content Feed */}
      {activeTab === "announcements" ? (
        // Institutional Announcements Feed
        <div className="space-y-4">
          {isAnnouncementsLoading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading announcements...</div>
          ) : announcements.length === 0 ? (
            <EmptyState
              icon={<Megaphone className="h-10 w-10 text-slate-500" />}
              title="No Broadcast Announcements"
              description="There are currently no institution-wide or cohort announcements."
            />
          ) : (
            announcements.map((ann: StudentAnnouncementItem) => (
              <Card
                key={ann.id}
                className="p-5 border-surface-800 bg-surface-900/70 hover:border-surface-700 transition-colors"
              >
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    <Megaphone className="h-5 w-5" />
                  </div>
                  <div className="space-y-2 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="font-bold text-white text-base leading-tight">{ann.title}</h3>
                      {getPriorityBadge(ann.priority)}
                    </div>
                    <p className="text-xs text-slate-300 whitespace-pre-line leading-relaxed">
                      {ann.content}
                    </p>
                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-500 pt-2 border-t border-surface-800/80">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3 text-slate-400" />
                        <span>Published {formatTimestamp(ann.published_at || ann.created_at)}</span>
                      </span>
                      <span className="text-slate-600">•</span>
                      <span>By {ann.published_by_name}</span>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>
      ) : (
        // In-App Notifications Feed
        <div className="space-y-3">
          {isNotifLoading ? (
            <div className="py-12 text-center text-xs text-slate-400">Loading notifications...</div>
          ) : filteredNotifications.length === 0 ? (
            <EmptyState
              icon={<CheckCircle2 className="h-10 w-10 text-emerald-400" />}
              title="All Caught Up!"
              description={
                activeTab === "unread"
                  ? "You have no unread alerts at this time."
                  : "No notifications matching this category."
              }
            />
          ) : (
            filteredNotifications.map((notif: StudentNotificationItem) => {
              const isUnread = !notif.is_read;
              return (
                <Card
                  key={notif.id}
                  className={`p-4 transition-all border ${
                    isUnread
                      ? "bg-surface-900 border-brand-500/30 shadow-sm"
                      : "bg-surface-900/40 border-surface-800/80 text-slate-400"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3.5 flex-1 min-w-0">
                      <div
                        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${
                          isUnread
                            ? "bg-surface-800 border-surface-700"
                            : "bg-surface-850 border-surface-800 opacity-70"
                        }`}
                      >
                        {getNotificationIcon(notif.notification_type)}
                      </div>

                      <div className="space-y-1 flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <h4
                            className={`text-xs sm:text-sm font-semibold truncate ${
                              isUnread ? "text-white font-bold" : "text-slate-300"
                            }`}
                          >
                            {notif.title}
                          </h4>
                          {isUnread && (
                            <span className="h-2 w-2 rounded-full bg-brand-400 shrink-0" title="Unread" />
                          )}
                        </div>

                        <p className="text-xs text-slate-300 leading-relaxed">{notif.body}</p>

                        <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-slate-500">
                          <span>{formatTimestamp(notif.created_at)}</span>
                          <span className="text-slate-700">•</span>
                          <span className="text-slate-400">{notif.notification_type_display}</span>

                          {notif.action_url && (
                            <Link
                              to={notif.action_url}
                              className="flex items-center gap-1 text-brand-400 hover:text-brand-300 font-medium ml-2"
                            >
                              <span>View details</span>
                              <ExternalLink className="h-3 w-3" />
                            </Link>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 shrink-0">
                      {isUnread && (
                        <button
                          onClick={() => markReadMutation.mutate(notif.id)}
                          className="text-slate-400 hover:text-brand-400 p-1.5 rounded-lg hover:bg-surface-800 transition-colors"
                          title="Mark as read"
                        >
                          <CheckCheck className="h-4 w-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteMutation.mutate(notif.id)}
                        className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-surface-800 transition-colors"
                        title="Dismiss alert"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
