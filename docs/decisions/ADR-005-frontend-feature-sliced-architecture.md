# ADR-005: Feature-Driven Modular Architecture for React 18 + Vite Frontend

## Context
Large-scale frontend applications with multiple complex views (Monaco code editor with split testcase panes, admin review consoles, student dashboards, real-time leaderboard, capstone project file uploaders, and interactive AI chat drawers) frequently succumb to spaghetti architecture when organized solely by technical type (e.g. putting all components in `components/`, all hooks in `hooks/`). This leads to tight coupling, high cognitive load, and difficulty navigating domain code.

## Decision
We adopt a **Feature-Driven Modular Architecture** inside `/frontend/src/`:

```text
src/
├── app/                  # Application initialization, root providers, router config
├── components/           # Generic reusable UI primitives (Button, Modal, Input, Badge)
├── features/             # Business domain slices
│   ├── auth/             # Login, OTP verification, password setup
│   ├── admin/            # Student onboarding, review workbench, overrides
│   ├── student/          # Dashboard, streak overview, progress widgets
│   ├── courses/          # Course listing, enrollment
│   ├── modules/          # 17 sequential topics, topic locks
│   ├── coding/           # Monaco editor, testcase viewer, execution runner
│   ├── leaderboard/      # Global & batch rankings, podium
│   ├── tasks/            # Daily practice tasks
│   ├── projects/         # Project submissions, file uploader, reviews
│   ├── ai_assistant/     # Floating AI tutor drawer, chat thread
│   ├── notifications/    # Notifications panel, broadcast announcements
│   └── certificates/     # Certificate verification, badge showcase
├── layouts/              # AuthLayout, StudentLayout, AdminLayout
├── routes/               # ProtectedRoute, RoleGuard, route trees
├── api/                  # Axios HTTP client, centralized endpoints, error interceptors
├── store/                # Global Zustand stores (Auth session, UI state, Editor settings)
├── types/                # TypeScript domain models and API contracts
└── schemas/              # Zod validation schemas
```

### State Separation Rules:
- **Server Data Cache:** Managed exclusively via **TanStack Query v5**. Handled with explicit cache keys (`['modules', courseId]`, `['submission', submissionId]`).
- **Client Session State:** Minimal Zustand stores (`useAuthStore`, `useEditorStore`).
- **Form Validation:** React Hook Form bound with Zod schemas.

## Consequences
- **Positive:**
  - High cohesion: all code related to Monaco coding assessment lives in `features/coding/`.
  - Independent maintainability: developers can build or refactor features without touching unrelated parts of the app.
  - Clear boundaries between presentational UI and business domain logic.
- **Negative:**
  - Requires developers to maintain discipline regarding whether a component belongs in global `components/` or local `features/*/components/`.
