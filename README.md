# GQT Student Portal — Architecture & Platform Blueprint

Welcome to the **GQT Student Learning and Coding Assessment Platform** repository. This is an enterprise-grade, high-concurrency educational and automated coding assessment portal tailored for structured sequential learning, interactive coding, daily tasks, capstone projects, automated grading, leaderboard mechanics, and integrated AI tutoring.

---

## 🏛️ Monorepo Structure

```text
gqt-student-portal/
├── backend/                  # Django REST Framework backend with clean modular apps
│   ├── config/               # Settings (base/dev/prod), URLs, Celery, WSGI/ASGI
│   ├── apps/                 # Modular Django domain apps
│   │   ├── accounts/         # Users, roles, auth (Email+Password, Mobile+OTP), JWT
│   │   ├── students/         # StudentProfile, batch info, onboarding
│   │   ├── courses/          # Courses, enrollments, curriculum structure
│   │   ├── modules/          # 17 sequential topics & unlock progression
│   │   ├── assignments/      # Coding problems, testcases (visible/hidden), submissions
│   │   ├── execution/        # Sandboxed code judge integration (Judge0/Piston/isolate)
│   │   ├── scoring/          # Scoring engine (Full / Half / Zero policy)
│   │   ├── leaderboard/      # High-performance ranking & caching engine
│   │   ├── tasks/            # Daily practice tasks & completion tracking
│   │   ├── projects/         # Project submissions (GitHub links, file uploads, reviews)
│   │   ├── ai_assistant/     # Sandboxed LLM tutor (external provider, rate-limited)
│   │   ├── notifications/    # In-app notifications & institutional announcements
│   │   ├── analytics/        # Student performance metrics & aggregation
│   │   ├── reports/          # Batch/Student diagnostic reports
│   │   ├── certificates/     # Verifiable credentials & achievement badges
│   │   ├── contact/          # Support desk & queries
│   │   └── common/           # Abstract models, base services, custom exceptions, audit
│   └── requirements/         # Split requirements (base.txt, local.txt, production.txt)
│
├── frontend/                 # Vite + React 18 + TypeScript SPA
│   ├── src/
│   │   ├── app/              # Application root, providers, router configuration
│   │   ├── components/       # Design system primitives, feedback, data display
│   │   ├── features/         # Domain-sliced modules (auth, student, admin, coding, etc.)
│   │   ├── layouts/          # AuthLayout, StudentLayout, AdminLayout
│   │   ├── routes/           # Protected routes, role guards (STUDENT / ADMIN)
│   │   ├── hooks/            # Custom reusable hooks
│   │   ├── services/         # Third-party integrations
│   │   ├── api/              # Axios instance, interceptors, centralized API contracts
│   │   ├── store/            # Lightweight Zustand stores (auth, editor, UI)
│   │   ├── types/            # TypeScript interfaces & domain types
│   │   ├── schemas/          # Zod validation schemas
│   │   ├── utils/            # Pure utility functions
│   │   ├── constants/        # System constants & curriculum definitions
│   │   ├── assets/           # Static assets, branding
│   │   └── styles/           # Tailwind CSS & global theme tokens
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── infrastructure/           # Containerization, orchestration, and service definitions
│   ├── docker-compose.yml    # Full stack definition (Postgres, Redis, Backend, Celery, Frontend)
│   ├── docker-compose.dev.yml
│   └── docker/               # Dedicated Dockerfiles and Nginx configurations
│
├── docs/                     # Architectural documentation, specifications, and ADRs
│   ├── architecture.md       # High-level architecture blueprint
│   ├── database.md           # Entity relationships, schema design, and indexing strategy
│   ├── api.md                # REST API design specifications and error conventions
│   ├── security.md           # Security policies, auth flows, and sandbox isolation
│   ├── development.md        # Local development setup and developer workflows
│   ├── deployment.md         # Production deployment strategy and CI/CD
│   ├── testing.md            # Testing pyramid (Backend unit/integration, Frontend unit/E2E)
│   └── decisions/            # Architectural Decision Records (ADRs)
│
└── scripts/                  # Automation scripts for setup, seeding, and migrations
```

---

## 🎯 17 Sequential Learning Curriculum Topics

The curriculum is strictly ordered. Access to module $N+1$ requires meeting passing criteria on module $N$:

1. **Data Types**
2. **If-Else**
3. **Loops**
4. **Strings**
5. **Lists**
6. **Tuple**
7. **Set**
8. **Dictionary**
9. **Merging Collections**
10. **Functions**
11. **Lambda Functions**
12. **OOP Concepts**
13. **Encapsulation**
14. **Inheritance**
15. **Polymorphism**
16. **Abstraction**
17. **Interface**

---

## 🛠️ Technology Stack Overview

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11+, Django 5.x, Django REST Framework (DRF), Celery 5.x |
| **Data & Cache** | PostgreSQL 16, Redis 7 (broker, caching, rate limiting) |
| **Authentication** | JWT (`djangorestframework-simplejwt`), Argon2 / PBKDF2, OTP with HMAC |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Framer Motion, Monaco Editor |
| **State & Data Fetching** | TanStack Query v5 (server cache), Zustand (client/editor session state) |
| **Forms & Validation** | React Hook Form, Zod |
| **Data Visualization** | Recharts |
| **Code Execution** | Isolated Sandboxed Code Execution Service (Judge0 / Piston / isolate) |
| **AI Assistant** | Server-side LLM Orchestration Layer (OpenAI / Claude API via Celery/SSE) |
| **Infrastructure** | Docker, Docker Compose, Nginx, Gunicorn / Uvicorn |

---

## 🚀 Current Project Phase: Phase 0

> [!NOTE]
> This phase establishes the comprehensive software architecture, technical blueprints, development standards, repository scaffolding, and ADRs before business module implementation begins in Phase 1.
