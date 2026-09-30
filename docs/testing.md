# Comprehensive Testing Strategy

## 1. Testing Pyramid Overview

The testing strategy focuses heavily on isolated, fast unit and service-level integration tests, backed by simulated external services to guarantee zero network flakes in CI.

```text
       /\
      /  \       E2E Tests (Playwright: Critical flows: Login, Module Unlock, Submission)
     /----\
    /      \     API Integration Tests (DRF APITestCase: Serializers, Auth, Permissions)
   /--------\
  /          \   Domain Service Tests (Pytest: Scoring engine, Sequential unlock, OTP logic)
 /------------\  Unit Tests (Pytest / Vitest: Models, utilities, pure React components)
```

---

## 2. Backend Testing Specifications

### 2.1 Framework & Tools
- **Test Runner:** `pytest` + `pytest-django` + `pytest-xdist` (parallel execution)
- **Fixtures & Factories:** `factory_boy` for reproducible model fixtures.
- **Coverage Goal:** Minimum 85% line and branch coverage across `/backend/apps/*/services.py`.

### 2.2 Test Structure
```text
backend/apps/
├── assignments/
│   ├── tests/
│   │   ├── test_models.py
│   │   ├── test_services.py       # Core submission and execution logic
│   │   ├── test_views.py          # API endpoints and response envelopes
│   │   └── factories.py           # FactoryBoy model factories
```

### 2.3 External Dependency Mocking Strategy

#### 1. Code Judge Mocking:
Tests must **never** contact the live Judge0 cluster. Instead, an abstract `BaseJudgeClient` protocol is implemented, with a `MockJudgeClient` returning deterministic status responses:
```python
# apps/execution/tests/test_services.py
def test_submission_full_score_evaluation(monkeypatch):
    monkeypatch.setattr(
        "apps.execution.services.JudgeService.execute_batch",
        lambda *args, **kwargs: [
            {"status": "PASSED", "stdout": "42\n", "execution_time": 0.02}
        ]
    )
```

#### 2. LLM Provider Mocking:
External AI API calls (OpenAI/Anthropic) are intercepted using `pytest-mock` or `responses` library, returning canned Socratic hints without incurring latency or cost.

#### 3. SMS Gateway Mocking:
In test and development environments, `SMS_PROVIDER=mock` logs generated OTPs to the test console or in-memory dict rather than transmitting cellular SMS.

---

## 3. Frontend Testing Specifications

### 3.1 Framework & Tools
- **Test Runner:** `vitest`
- **DOM Assertions:** `@testing-library/react` + `@testing-library/jest-dom`
- **API Mocking:** `msw` (Mock Service Worker) for intercepting browser HTTP requests.

### 3.2 Key Testing Targets
- **Zod Form Validations:** Ensure boundary inputs (invalid phone numbers, short passwords) produce expected error tags.
- **Protected Routes & Role Guards:** Validate unauthorized redirects when a `STUDENT` attempts accessing `/admin/*`.
- **Monaco Editor Integration:** Verify syntax highlighting, language selection changes, and run/submit state changes.
- **Leaderboard Rendering:** Ensure correct sorting, medal badges, and streak counts render accurately.
