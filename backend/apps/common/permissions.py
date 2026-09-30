from rest_framework.permissions import BasePermission
from apps.accounts.models import User


class IsAdmin(BasePermission):
    """Allows access strictly to authenticated users with ADMIN role or staff status."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, "role", None) == User.RoleChoices.ADMIN
                or request.user.is_staff
                or request.user.is_superuser
            )
        )


IsAdminUser = IsAdmin  # Alias for backward compatibility


class IsStudent(BasePermission):
    """Allows access strictly to authenticated users with STUDENT role."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.RoleChoices.STUDENT
        )


IsStudentUser = IsStudent  # Alias for backward compatibility


class IsActiveStudent(BasePermission):
    """Allows access strictly to authenticated, active students."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.RoleChoices.STUDENT
            and request.user.is_active
        )


class IsApprovedStudent(BasePermission):
    """Allows access strictly to authenticated students whose account is active and approved.

    Denies access to students whose onboarding_status is PENDING_ACTIVATION or SUSPENDED.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) == User.RoleChoices.STUDENT
            and request.user.is_active
            and getattr(request.user, "onboarding_status", None)
            == User.OnboardingStatusChoices.ACTIVE
        )


class IsOwnerOrAdmin(BasePermission):
    """Object-level permission allowing owners or admins to access resources.

    Protects student profile, scores, submissions, tasks, AI conversations,
    notifications, and progress from cross-student access.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Administrators always have access
        if (
            getattr(request.user, "role", None) == User.RoleChoices.ADMIN
            or request.user.is_staff
            or request.user.is_superuser
        ):
            return True

        # Check various ownership relations:
        # 1. Direct user object (e.g. User)
        if obj == request.user:
            return True

        # 2. obj.user relation (e.g. StudentProfile, Notification.recipient, LoginActivity, etc.)
        if hasattr(obj, "user") and obj.user == request.user:
            return True

        # 3. obj.recipient relation (e.g. Notification)
        if hasattr(obj, "recipient") and obj.recipient == request.user:
            return True

        # 4. obj.student relation
        if hasattr(obj, "student"):
            student = obj.student
            if hasattr(student, "user") and student.user == request.user:
                return True
            if student == request.user:
                return True
            if hasattr(request.user, "student_profile") and student == request.user.student_profile:
                return True

        return False
