# REST API Design & Convention Specifications

## 1. API Architecture Principles

- **Base URL & Versioning:** All endpoints are versioned under URI path: `/api/v1/`
- **Transport Security:** Strictly HTTPS only with TLS 1.3.
- **Data Format:** JSON request bodies and responses (`Content-Type: application/json`).
- **HTTP Methods:**
  - `GET`: Read resources (idempotent, safe).
  - `POST`: Create resource or trigger action (non-idempotent).
  - `PUT`: Full resource replacement.
  - `PATCH`: Partial resource update.
  - `DELETE`: Remove resource or soft-deactivate.

---

## 2. Standardized Response Envelopes

Every API response follows a consistent top-level JSON structure.

### 2.1 Success Envelope (Single Object)
```json
{
  "success": true,
  "data": {
    "id": "e6a2b37c-9b1c-4b52-bbf1-8a9d12345678",
    "title": "1. Data Types",
    "order_index": 1,
    "is_unlocked": true
  },
  "meta": {
    "timestamp": "2026-09-30T09:40:00Z"
  }
}
```

### 2.2 Success Envelope (Paginated List)
```json
{
  "success": true,
  "data": [
    {
      "id": "d9812450-4d51-419b-a05e-85a228399581",
      "student_name": "Aditya Rao",
      "total_score": 1450,
      "global_rank": 1
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_records": 480,
      "total_pages": 24,
      "has_next": true,
      "has_prev": false
    },
    "timestamp": "2026-09-30T09:40:00Z"
  }
}
```

### 2.3 Error Envelope
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "The submitted payload contains validation errors.",
    "details": {
      "mobile_number": [
        "Enter a valid 10-digit mobile number with country code."
      ]
    },
    "request_id": "req-987abc-54321"
  },
  "meta": {
    "timestamp": "2026-09-30T09:40:00Z"
  }
}
```

---

## 3. Standard HTTP Status Codes

| Code | Status | Meaning in GQT Platform |
|---|---|---|
| `200` | OK | Request processed successfully with data payload. |
| `201` | Created | Resource successfully created (e.g. Student Onboarded, Submission logged). |
| `202` | Accepted | Request accepted for async processing (e.g. Code Judge evaluation). |
| `204` | No Content | Request succeeded, no payload returned (e.g. Delete, Logout). |
| `400` | Bad Request | Validation error or invalid payload structure. |
| `401` | Unauthorized | Missing, expired, or invalid JWT token. |
| `403` | Forbidden | Insufficient permissions (e.g. Student attempting admin onboarding). |
| `404` | Not Found | Requested entity does not exist or belongs to another tenant. |
| `409` | Conflict | Duplicate entry (e.g. Mobile number or Student ID already exists). |
| `422` | Unprocessable | Semantic failure (e.g. Attempting to submit to a locked module). |
| `429` | Too Many Requests | Rate limit reached (e.g. OTP spam protection, LLM quota). |
| `500` | Internal Server Error | Unhandled server exception (logged with stack trace and request ID). |

---

## 4. Standard Endpoint Contracts

### 4.1 Authentication Endpoints (`/api/v1/auth/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/login/email/` | Authenticate with email + password | None |
| `POST` | `/api/v1/auth/otp/send/` | Request login OTP to registered mobile | None (Rate limited: 3/min) |
| `POST` | `/api/v1/auth/otp/verify/` | Verify OTP & receive JWT pair | None |
| `POST` | `/api/v1/auth/refresh/` | Refresh access token using refresh token | None (Refresh token in body) |
| `POST` | `/api/v1/auth/logout/` | Blacklist refresh token & clear session | Bearer JWT |
| `GET` | `/api/v1/auth/me/` | Fetch current user & profile context | Bearer JWT |

### 4.2 Admin Management Endpoints (`/api/v1/admin/`)

| Method | Endpoint | Description | Role Required |
|---|---|---|---|
| `POST` | `/api/v1/admin/students/onboard/` | Single student onboarding | ADMIN |
| `POST` | `/api/v1/admin/students/bulk-import/` | CSV bulk onboarding of students | ADMIN |
| `GET` | `/api/v1/admin/students/` | List all students with search & filter | ADMIN |
| `PATCH` | `/api/v1/admin/students/{id}/status/` | Activate, suspend, or reset student | ADMIN |
| `POST` | `/api/v1/admin/modules/{id}/override-unlock/` | Manually unlock module for a student | ADMIN |
| `GET` | `/api/v1/admin/projects/pending-review/` | List project submissions awaiting review | ADMIN |
| `POST` | `/api/v1/admin/projects/{id}/review/` | Submit review, grade & feedback | ADMIN |

### 4.3 Curriculum & Modules Endpoints (`/api/v1/modules/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/courses/{id}/modules/` | List 17 sequential topics with student lock states | Bearer JWT |
| `GET` | `/api/v1/modules/{id}/` | Get module detail & lecture content (if unlocked) | Bearer JWT |
| `GET` | `/api/v1/modules/{id}/questions/` | Get questions inside module | Bearer JWT |

### 4.4 Coding & Assessment Endpoints (`/api/v1/assignments/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/assignments/{id}/` | Get coding question, boilerplate, visible test cases | Bearer JWT |
| `POST` | `/api/v1/assignments/{id}/run/` | Execute code against visible testcases only | Bearer JWT |
| `POST` | `/api/v1/assignments/{id}/submit/` | Formal submission graded against visible + hidden cases | Bearer JWT |
| `GET` | `/api/v1/assignments/submissions/{id}/` | Check submission result & execution status | Bearer JWT |

### 4.5 Leaderboard & Tasks (`/api/v1/leaderboard/`, `/api/v1/tasks/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/leaderboard/global/` | Global student rankings (cached in Redis) | Bearer JWT |
| `GET` | `/api/v1/leaderboard/batch/` | Batch-specific student rankings | Bearer JWT |
| `GET` | `/api/v1/tasks/daily/` | Get current day's coding challenge | Bearer JWT |
| `POST` | `/api/v1/tasks/{id}/complete/` | Mark daily task complete & award streak | Bearer JWT |

### 4.6 Capstone Projects (`/api/v1/projects/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/projects/` | List student capstone projects | Bearer JWT |
| `POST` | `/api/v1/projects/{id}/submit/` | Submit GitHub URL, live demo, project ZIP files | Bearer JWT |
| `GET` | `/api/v1/projects/{id}/submission/` | View submission status & admin feedback | Bearer JWT |

### 4.7 AI Tutor Assistant (`/api/v1/ai/`)

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/ai/conversations/` | Start or resume an AI conversation session | Bearer JWT |
| `POST` | `/api/v1/ai/chat/` | Send prompt to AI tutor with question context | Bearer JWT (Rate limited) |
| `GET` | `/api/v1/ai/conversations/{id}/messages/` | Fetch historical AI chat messages | Bearer JWT |
