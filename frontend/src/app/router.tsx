import React, { Suspense, lazy } from "react";
import { createBrowserRouter, Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

// Layouts
import { AdminLayout } from "../components/layout/AdminLayout";
import { StudentLayout } from "../components/layout/StudentLayout";

// Guards
import { ProtectedRoute } from "../components/auth/ProtectedRoute";
import { StudentRouteGuard } from "../components/auth/StudentRouteGuard";

// Fast Loading Spinner Fallback for Lazy Route Boundaries
const RouteLoadingFallback: React.FC = () => (
  <div className="flex min-h-[400px] w-full items-center justify-center p-12">
    <div className="flex flex-col items-center gap-3">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      <span className="text-xs font-medium text-slate-400">Loading view...</span>
    </div>
  </div>
);

// Wrapper to wrap lazy elements in Suspense
const withSuspense = (Component: React.LazyExoticComponent<React.ComponentType<any>>) => (
  <Suspense fallback={<RouteLoadingFallback />}>
    <Component />
  </Suspense>
);

// Auth Pages (Lazy)
const StudentLoginPage = lazy(() =>
  import("../pages/auth/StudentLoginPage").then((m) => ({ default: m.StudentLoginPage }))
);
const StudentRegisterPage = lazy(() =>
  import("../pages/auth/StudentRegisterPage").then((m) => ({ default: m.StudentRegisterPage }))
);
const AdminLoginPage = lazy(() =>
  import("../pages/auth/AdminLoginPage").then((m) => ({ default: m.AdminLoginPage }))
);
const ForgotPasswordPage = lazy(() =>
  import("../pages/auth/ForgotPasswordPage").then((m) => ({ default: m.ForgotPasswordPage }))
);
const ResetPasswordPage = lazy(() =>
  import("../pages/auth/ResetPasswordPage").then((m) => ({ default: m.ResetPasswordPage }))
);
const UnauthorizedPage = lazy(() =>
  import("../pages/UnauthorizedPage").then((m) => ({ default: m.UnauthorizedPage }))
);

// Student Pages (Lazy)
const StudentDashboardPage = lazy(() =>
  import("../pages/student/StudentDashboardPage").then((m) => ({ default: m.StudentDashboardPage }))
);
const StudentCoursesPage = lazy(() =>
  import("../pages/student/StudentCoursesPage").then((m) => ({ default: m.StudentCoursesPage }))
);
const StudentRecordedClassesPage = lazy(() =>
  import("../pages/student/StudentRecordedClassesPage").then((m) => ({
    default: m.StudentRecordedClassesPage,
  }))
);
const StudentRecordedClassWatchPage = lazy(() =>
  import("../pages/student/StudentRecordedClassWatchPage").then((m) => ({
    default: m.StudentRecordedClassWatchPage,
  }))
);
const StudentCourseDetailPage = lazy(() =>
  import("../pages/student/StudentCourseDetailPage").then((m) => ({
    default: m.StudentCourseDetailPage,
  }))
);
const StudentModuleDetailPage = lazy(() =>
  import("../pages/student/StudentModuleDetailPage").then((m) => ({
    default: m.StudentModuleDetailPage,
  }))
);
const StudentAssignmentsPage = lazy(() =>
  import("../pages/student/StudentAssignmentsPage").then((m) => ({
    default: m.StudentAssignmentsPage,
  }))
);
const StudentAssignmentDetailPage = lazy(() =>
  import("../pages/student/StudentAssignmentDetailPage").then((m) => ({
    default: m.StudentAssignmentDetailPage,
  }))
);
const StudentTasksPage = lazy(() =>
  import("../pages/student/StudentTasksPage").then((m) => ({ default: m.StudentTasksPage }))
);
const StudentProjectsPage = lazy(() =>
  import("../pages/student/StudentProjectsPage").then((m) => ({ default: m.StudentProjectsPage }))
);
const StudentProjectSubmitPage = lazy(() =>
  import("../pages/student/StudentProjectSubmitPage").then((m) => ({
    default: m.StudentProjectSubmitPage,
  }))
);
const StudentHelpAiPage = lazy(() =>
  import("../pages/student/StudentHelpAiPage").then((m) => ({ default: m.StudentHelpAiPage }))
);
const StudentNotificationsPage = lazy(() =>
  import("../pages/student/StudentNotificationsPage").then((m) => ({
    default: m.StudentNotificationsPage,
  }))
);
const StudentProfilePage = lazy(() =>
  import("../pages/student/StudentProfilePage").then((m) => ({ default: m.StudentProfilePage }))
);
const StudentContactPage = lazy(() =>
  import("../pages/student/StudentContactPage").then((m) => ({ default: m.StudentContactPage }))
);
const StudentPlacementsPage = lazy(() =>
  import("../pages/student/StudentPlacementsPage").then((m) => ({
    default: m.StudentPlacementsPage,
  }))
);
const StudentAttendancePage = lazy(() =>
  import("../pages/student/StudentAttendancePage").then((m) => ({
    default: m.StudentAttendancePage,
  }))
);

// Admin Portal Pages (Lazy)
const DashboardPage = lazy(() =>
  import("../pages/admin/DashboardPage").then((m) => ({ default: m.DashboardPage }))
);
const PlacementDrivesPage = lazy(() =>
  import("../pages/admin/PlacementDrivesPage").then((m) => ({
    default: m.PlacementDrivesPage,
  }))
);
const PlacementApplicantsPage = lazy(() =>
  import("../pages/admin/PlacementApplicantsPage").then((m) => ({
    default: m.PlacementApplicantsPage,
  }))
);
const StudentsPage = lazy(() =>
  import("../pages/admin/StudentsPage").then((m) => ({ default: m.StudentsPage }))
);
const StudentDetailPage = lazy(() =>
  import("../pages/admin/StudentDetailPage").then((m) => ({ default: m.StudentDetailPage }))
);
const AdminAttendancePage = lazy(() =>
  import("../pages/admin/AdminAttendancePage").then((m) => ({ default: m.AdminAttendancePage }))
);
const CoursesPage = lazy(() =>
  import("../pages/admin/CoursesPage").then((m) => ({ default: m.CoursesPage }))
);
const CourseDetailPage = lazy(() =>
  import("../pages/admin/CourseDetailPage").then((m) => ({ default: m.CourseDetailPage }))
);
const AdminRecordedClassesPage = lazy(() =>
  import("../pages/admin/AdminRecordedClassesPage").then((m) => ({
    default: m.AdminRecordedClassesPage,
  }))
);
const AssignmentsPage = lazy(() =>
  import("../pages/admin/AssignmentsPage").then((m) => ({ default: m.AssignmentsPage }))
);
const AssignmentDetailPage = lazy(() =>
  import("../pages/admin/AssignmentDetailPage").then((m) => ({ default: m.AssignmentDetailPage }))
);
const TasksPage = lazy(() =>
  import("../pages/admin/TasksPage").then((m) => ({ default: m.TasksPage }))
);
const ProjectsPage = lazy(() =>
  import("../pages/admin/ProjectsPage").then((m) => ({ default: m.ProjectsPage }))
);
const ProjectDetailPage = lazy(() =>
  import("../pages/admin/ProjectDetailPage").then((m) => ({ default: m.ProjectDetailPage }))
);
const AnnouncementsPage = lazy(() =>
  import("../pages/admin/AnnouncementsPage").then((m) => ({ default: m.AnnouncementsPage }))
);
const CertificatesPage = lazy(() =>
  import("../pages/admin/CertificatesPage").then((m) => ({ default: m.CertificatesPage }))
);
const ContactInquiriesPage = lazy(() =>
  import("../pages/admin/ContactInquiriesPage").then((m) => ({ default: m.ContactInquiriesPage }))
);
const AnalyticsPage = lazy(() =>
  import("../pages/admin/AnalyticsPage").then((m) => ({ default: m.AnalyticsPage }))
);
const ReportsPage = lazy(() =>
  import("../pages/admin/ReportsPage").then((m) => ({ default: m.ReportsPage }))
);
const AdminProfilePage = lazy(() =>
  import("../pages/admin/AdminProfilePage").then((m) => ({ default: m.AdminProfilePage }))
);

// Admin Role Guard
const AdminRoleGuard: React.FC = () => {
  const { user } = useAuthStore();

  if (!user || user.role !== "ADMIN") {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

// Smart Root Redirector
const RootRedirector: React.FC = () => {
  const { isAuthenticated, user } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role === "ADMIN") {
    return <Navigate to="/admin/dashboard" replace />;
  }

  return <Navigate to="/dashboard" replace />;
};

export const router = createBrowserRouter([
  // Root Redirect
  {
    path: "/",
    element: <RootRedirector />,
  },

  // Public Student Authentication
  {
    path: "/login",
    element: withSuspense(StudentLoginPage),
  },
  {
    path: "/student/login",
    element: withSuspense(StudentLoginPage),
  },

  // Public Student Registration
  {
    path: "/register",
    element: withSuspense(StudentRegisterPage),
  },
  {
    path: "/student/register",
    element: withSuspense(StudentRegisterPage),
  },

  // Public Admin Authentication
  {
    path: "/admin/login",
    element: withSuspense(AdminLoginPage),
  },
  {
    path: "/auth/admin-login",
    element: withSuspense(AdminLoginPage),
  },
  {
    path: "/auth/admin/login",
    element: withSuspense(AdminLoginPage),
  },
  {
    path: "/auth/login",
    element: withSuspense(StudentLoginPage),
  },
  {
    path: "/auth/student-login",
    element: withSuspense(StudentLoginPage),
  },

  // Password Recovery & OTP Flows
  {
    path: "/forgot-password",
    element: withSuspense(ForgotPasswordPage),
  },
  {
    path: "/auth/forgot-password",
    element: withSuspense(ForgotPasswordPage),
  },
  {
    path: "/reset-password",
    element: withSuspense(ResetPasswordPage),
  },
  {
    path: "/auth/reset-password",
    element: withSuspense(ResetPasswordPage),
  },
  {
    path: "/unauthorized",
    element: withSuspense(UnauthorizedPage),
  },

  // Protected Student Portal (Authenticated + Role = STUDENT)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <StudentRouteGuard />,
        children: [
          {
            element: <StudentLayout />,
            children: [
              {
                path: "/dashboard",
                element: withSuspense(StudentDashboardPage),
              },
              {
                path: "/courses",
                element: withSuspense(StudentCoursesPage),
              },
              {
                path: "/courses/:courseId",
                element: withSuspense(StudentCourseDetailPage),
              },
              {
                path: "/recorded-classes",
                element: withSuspense(StudentRecordedClassesPage),
              },
              {
                path: "/recorded-classes/:courseId",
                element: withSuspense(StudentRecordedClassWatchPage),
              },
              {
                path: "/recorded-classes/:courseId/video/:videoId",
                element: withSuspense(StudentRecordedClassWatchPage),
              },
              {
                path: "/modules/:moduleId",
                element: withSuspense(StudentModuleDetailPage),
              },
              {
                path: "/assignments",
                element: withSuspense(StudentAssignmentsPage),
              },
              {
                path: "/assignments/:assignmentId",
                element: withSuspense(StudentAssignmentDetailPage),
              },
              {
                path: "/tasks",
                element: withSuspense(StudentTasksPage),
              },
              {
                path: "/projects",
                element: withSuspense(StudentProjectsPage),
              },
              {
                path: "/projects/submit",
                element: withSuspense(StudentProjectSubmitPage),
              },
              {
                path: "/help-ai",
                element: withSuspense(StudentHelpAiPage),
              },
              {
                path: "/notifications",
                element: withSuspense(StudentNotificationsPage),
              },
              {
                path: "/profile",
                element: withSuspense(StudentProfilePage),
              },
              {
                path: "/placements",
                element: withSuspense(StudentPlacementsPage),
              },
              {
                path: "/attendance",
                element: withSuspense(StudentAttendancePage),
              },
              {
                path: "/qr-attendance",
                element: withSuspense(StudentAttendancePage),
              },
              {
                path: "/contact",
                element: withSuspense(StudentContactPage),
              },
            ],
          },
        ],
      },
    ],
  },

  // Protected Admin Portal (Authenticated + Role = ADMIN)
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AdminRoleGuard />,
        children: [
          {
            path: "/admin",
            element: <AdminLayout />,
            children: [
              {
                path: "dashboard",
                element: withSuspense(DashboardPage),
              },
              {
                path: "placements",
                element: withSuspense(PlacementDrivesPage),
              },
              {
                path: "placements/applicants",
                element: withSuspense(PlacementApplicantsPage),
              },
              {
                path: "placements/:id/applicants",
                element: withSuspense(PlacementApplicantsPage),
              },
              {
                path: "students",
                element: withSuspense(StudentsPage),
              },
              {
                path: "students/:id",
                element: withSuspense(StudentDetailPage),
              },
              {
                path: "attendance",
                element: withSuspense(AdminAttendancePage),
              },
              {
                path: "courses",
                element: withSuspense(CoursesPage),
              },
              {
                path: "courses/:id",
                element: withSuspense(CourseDetailPage),
              },
              {
                path: "recorded-classes",
                element: withSuspense(AdminRecordedClassesPage),
              },
              {
                path: "courses/:id/videos",
                element: withSuspense(AdminRecordedClassesPage),
              },
              {
                path: "assignments",
                element: withSuspense(AssignmentsPage),
              },
              {
                path: "assignments/:id",
                element: withSuspense(AssignmentDetailPage),
              },
              {
                path: "tasks",
                element: withSuspense(TasksPage),
              },
              {
                path: "projects",
                element: withSuspense(ProjectsPage),
              },
              {
                path: "projects/submissions/:id",
                element: withSuspense(ProjectDetailPage),
              },
              {
                path: "announcements",
                element: withSuspense(AnnouncementsPage),
              },
              {
                path: "certificates",
                element: withSuspense(CertificatesPage),
              },
              {
                path: "inquiries",
                element: withSuspense(ContactInquiriesPage),
              },
              {
                path: "inquiries/:id",
                element: withSuspense(ContactInquiriesPage),
              },
              {
                path: "inquiry",
                element: withSuspense(ContactInquiriesPage),
              },
              {
                path: "contact",
                element: withSuspense(ContactInquiriesPage),
              },
              {
                path: "contact-inquiries",
                element: withSuspense(ContactInquiriesPage),
              },
              {
                path: "support",
                element: withSuspense(ContactInquiriesPage),
              },
              {
                path: "analytics",
                element: withSuspense(AnalyticsPage),
              },
              {
                path: "reports",
                element: withSuspense(ReportsPage),
              },
              {
                path: "profile",
                element: withSuspense(AdminProfilePage),
              },
              {
                path: "settings",
                element: withSuspense(AdminProfilePage),
              },
              {
                path: "account",
                element: withSuspense(AdminProfilePage),
              },
            ],
          },
        ],
      },
    ],
  },

  // Catch-all 404
  {
    path: "*",
    element: (
      <div className="flex min-h-screen items-center justify-center bg-surface-950 text-slate-400">
        <div className="text-center p-8 rounded-3xl border border-surface-800 bg-surface-900/60 max-w-md">
          <div className="text-6xl font-black text-white">404</div>
          <h2 className="mt-4 text-xl font-bold text-white">Resource Not Found</h2>
          <p className="mt-2 text-sm text-slate-400">
            The page or route you requested does not exist or may have been relocated.
          </p>
          <div className="mt-6">
            <Navigate to="/" replace />
          </div>
        </div>
      </div>
    ),
  },
]);
