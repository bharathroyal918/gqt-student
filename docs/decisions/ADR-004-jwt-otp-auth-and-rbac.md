# ADR-004: Dual Authentication (Email/Pass & Mobile/OTP) with JWT Rotation and RBAC

## Context
Educational institutions require flexible access methods for students. Many students access portals via mobile numbers and SMS OTP, while administrative staff and some students prefer standard email and password authentication. Crucially, the platform operates in a closed institutional environment where **public self-registration is strictly disallowed**—all accounts must be initiated via administrative onboarding.

## Decision
We implement a unified **JWT-based Authentication Architecture with Dual Authentication Channels and Role-Based Access Control (RBAC)**:

1. **Authentication Channels:**
   - **Email + Password:** Uses secure hashing (Argon2id/PBKDF2).
   - **Mobile Number + OTP:** Generates cryptographically secure 6-digit OTPs stored with a 5-minute TTL in Redis; max 5 attempts.
2. **Token Strategy:**
   - Stateless JWT Access Token (15-minute validity) passed in the `Authorization` header.
   - Long-lived Refresh Token (7-day validity) stored securely in HTTP-only cookie or memory-rotated.
   - **Token Rotation with Blacklisting:** Every token refresh operation invalidates the previous refresh token and issues a new pair, neutralizing stolen refresh tokens.
3. **Role-Based Access Control (RBAC):**
   - Explicit `Role` enum: `ADMIN` and `STUDENT`.
   - Admin routes and operations require `IsAdminRole` permission class.
   - Students are restricted to assigned courses, unlocked modules, and their own submissions via `IsOwnerOrAdmin`.

## Consequences
- **Positive:**
  - High convenience for students (fast login via SMS OTP).
  - High security for administrative functions.
  - Reduced token replay risk via automatic token rotation and blacklisting.
  - Complete control over student roster with no spam/unauthorized signups.
- **Negative:**
  - Requires third-party SMS provider integration (mocked in development/testing).
