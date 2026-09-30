# Development Workflow & Engineering Conventions

## 1. Prerequisites & Tooling

To develop locally on the GQT Student Portal platform, ensure your workstation has:
- **Python:** 3.11 or higher
- **Node.js:** 20.x LTS or higher (with npm 10+)
- **Docker & Docker Compose:** Latest stable release (Docker Desktop on Windows with WSL2 recommended)
- **Git:** 2.40+

---

## 2. Quickstart Guide

### 2.1 Backend Setup (Local Environment)

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 3. Install development dependencies
pip install -r requirements/local.txt

# 4. Copy the environment configuration
cp ../.env.example .env

# 5. Start required background services via Docker Compose
docker compose -f ../infrastructure/docker-compose.dev.yml up -d postgres redis

# 6. Apply database migrations
python manage.py migrate

# 7. Start the development server
python manage.py runserver 0.0.0.0:8000
```

### 2.2 Frontend Setup (Vite + React)

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Copy environment configuration
cp .env.example .env

# 4. Start Vite development server
npm run dev
```
The frontend dev server will spin up at `http://localhost:5173`.

---

## 3. Code Standards & Tooling

### 3.1 Python / Django Standards
- **Formatting:** `black` (line length: 100 characters).
- **Import Sorting:** `isort` with `--profile black`.
- **Linting:** `flake8` and `mypy` for static type checking.
- **Rules:**
  - Every service method must have complete Python type annotations (`def execute(submission_id: UUID) -> ExecutionResultDTO:`).
  - Docstrings follow Google/Sphinx format for domain services.
  - No database queries inside loops; always leverage `prefetch_related` and `select_related`.

### 3.2 TypeScript / React Standards
- **Linter & Formatter:** ESLint + Prettier.
- **Strict Typing:** `tsconfig.json` runs in `"strict": true` mode. Use of `any` is strictly prohibited unless explicitly commented with architectural justification.
- **Component Design:**
  - One component per file.
  - Presentational components must remain pure and free from direct API calls.
  - Complex async queries are placed inside custom query hooks (`useStudentProgressQuery`).

---

## 4. Naming Conventions

| Artifact | Language / Ecosystem | Convention | Example |
|---|---|---|---|
| Django Models | Python | PascalCase | `StudentProfile`, `QuestionSubmission` |
| Django Services | Python | PascalCase | `SubmissionExecutionService` |
| Django App Names | Python | snake_case (plural or singular noun) | `assignments`, `leaderboard` |
| DB Tables | PostgreSQL | snake_case, prefixed | `accounts_user`, `assignments_submission` |
| Python Functions & Vars | Python | snake_case | `calculate_daily_score()` |
| Python Constants | Python | SCREAMING_SNAKE_CASE | `MAX_OTP_ATTEMPTS = 5` |
| React Components | TypeScript | PascalCase | `CodeEditorPanel.tsx`, `LeaderboardTable.tsx` |
| React Custom Hooks | TypeScript | camelCase prefixed with `use` | `useAuth.ts`, `useSubmissionRunner.ts` |
| TypeScript Types/Interfaces | TypeScript | PascalCase | `IStudentProfile`, `SubmissionStatus` |
| REST API Endpoints | HTTP | kebab-case, plural nouns | `/api/v1/question-submissions/` |
| JSON Request/Response Keys | JSON | snake_case | `{"is_unlocked": true, "submission_id": "..."}` |

---

## 5. Git & Commit Guidelines

We enforce the **Conventional Commits** specification:
- `feat(modules)`: Add sequential locking rule validation
- `fix(scoring)`: Correct half-score calculation for partial testcases
- `refactor(accounts)`: Decouple OTP generation into dedicated service
- `docs(api)`: Update API envelope specification
- `test(execution)`: Add sandbox timeout mock tests
- `chore(deps)`: Bump simplejwt to latest stable
