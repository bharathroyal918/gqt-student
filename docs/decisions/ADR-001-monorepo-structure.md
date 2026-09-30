# ADR-001: Adoption of Monorepo Structure with Strict Domain Separation

## Context
The GQT Student Portal encompasses a complex web ecosystem comprising a Django REST Framework backend, a high-interaction React frontend (featuring Monaco code editor and real-time execution feedback), background asynchronous Celery workers, infrastructure configuration, and developer tooling. 

We considered two primary repository approaches:
1. **Multi-Repo:** Separate Git repositories for `frontend`, `backend`, `infrastructure`, and `docs`.
2. **Monorepo:** A unified repository organized into distinct top-level directories: `/frontend`, `/backend`, `/infrastructure`, `/docs`, `/scripts`.

## Decision
We adopt a **Unified Monorepo Architecture** with strict modular boundaries.

### Key Justifications:
- **Synchronized Feature Rollouts:** Changes to backend API contracts (e.g., changes to submission scoring envelopes or Monaco editor payloads) can be committed, code-reviewed, and verified alongside their frontend implementations in a single Git pull request.
- **Single Source of Truth:** Documentation, architecture blueprints, environment templates, and Docker Compose configurations reside directly adjacent to the active code.
- **Streamlined CI/CD:** End-to-end integration and smoke tests can run in one pipeline without coordinating multi-repository git submodules or cross-repo webhook triggers.
- **Isolation Preserved:** The backend and frontend maintain completely separate dependency trees (`requirements/` and `package.json`), avoiding dependency leaks.

## Consequences
- **Positive:**
  - Fast onboarding for developers (one repository clone).
  - Cross-stack atomic commits.
  - Unified issue tracking and release tagging.
- **Negative:**
  - Repository size will grow larger over time; mitigated by strict `.gitignore` rules (excluding binary assets, build artifacts, and node_modules).
