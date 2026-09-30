# ADR-002: Service Layer Pattern and Thin Views in Django REST Framework

## Context
Standard Django conventions often place business logic into model methods ("fat models") or inside DRF Serializers/ViewSets ("fat views" / "fat serializers"). In an assessment platform where actions involve multi-step transactions (e.g., executing code, evaluating Full/Half/Zero scoring, unlocking sequential modules, and updating streaks and leaderboards), mixing business logic into views or serializers leads to:
- Tight coupling to HTTP requests.
- Difficulty writing pure unit tests without constructing fake HTTP request/response contexts.
- Serializers bloated with side effects (sending notifications, triggering Celery tasks).
- Inability to reuse core business operations across API views, background workers, and management commands.

## Decision
We enforce a strict **Service Layer Pattern** across all backend apps (`apps/<domain>/services.py`):

1. **Thin Views:** Views/ViewSets only handle HTTP parsing, permission checks, calling the service, and returning the standard response envelope.
2. **Pure Serializers:** DRF Serializers perform schema validation and serialization/deserialization only. They do not trigger business logic or write to unrelated database tables.
3. **Domain Services:** All business rules, transactions (`transaction.atomic()`), calculations, and background task dispatches reside in explicit service classes or functional service modules.

## Consequences
- **Positive:**
  - High testability: Domain logic can be unit-tested without HTTP mocking.
  - Reusability: Celery background workers and API views call the exact same service methods.
  - Clear separation of concerns and adherence to Single Responsibility Principle (SRP).
- **Negative:**
  - Additional boilerplate (an extra layer between serializer and view). Highly justified by system complexity.
