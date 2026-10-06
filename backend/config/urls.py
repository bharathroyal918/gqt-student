"""Root URL Configuration for GQT Student Portal."""

from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.certificates.views import PublicCertificateVerifyView
from apps.projects.views import ProjectFileDownloadView

# API v1 URL patterns
api_v1_patterns = [
    path("", include("apps.common.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("admin/students/", include("apps.students.admin_urls")),
    path("admin/courses/", include("apps.courses.admin_urls")),
    path("admin/modules/", include("apps.modules.admin_urls")),
    path("admin/assignments/", include("apps.assignments.admin_urls")),
    path("admin/tasks/", include("apps.tasks.admin_urls")),
    path("admin/projects/", include("apps.projects.admin_urls")),
    path("admin/announcements/", include("apps.notifications.admin_urls")),
    path("admin/certificates/", include("apps.certificates.admin_urls")),
    path("admin/contact/", include("apps.contact.admin_urls")),
    path("admin/placements/", include("apps.placements.admin_urls")),
    path("admin/leaderboard/", include("apps.leaderboard.admin_urls")),
    path("admin/", include("apps.analytics.admin_urls")),
    path("leaderboard/", include("apps.leaderboard.urls")),
    path("contact/", include("apps.contact.urls")),
    path("students/assignments/", include("apps.assignments.student_urls")),
    path("students/tasks/", include("apps.tasks.urls")),
    path("students/projects/", include("apps.projects.urls")),
    path("students/placements/", include("apps.placements.student_urls")),
    path("students/ai/", include("apps.ai_assistant.urls")),
    path("students/notifications/", include("apps.notifications.urls")),
    path("students/", include("apps.certificates.urls")),
    path("certificates/verify/<str:identifier>/", PublicCertificateVerifyView.as_view(), name="public_cert_verify"),
    path("projects/files/<uuid:file_id>/download/", ProjectFileDownloadView.as_view(), name="project_file_download"),
    path("students/recorded-classes/", include("apps.courses.student_urls")),
    path("students/", include("apps.students.urls")),
]

from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def root_status_view(request):
    return JsonResponse(
        {
            "status": "online",
            "name": "Global Quality Technologies (GQT) Student Portal API",
            "version": "v1",
            "docs": "/api/docs/",
            "health": "/api/v1/health/",
        }
    )


urlpatterns = [
    path("", root_status_view, name="root_status"),
    path("admin/", admin.site.urls),
    path("health/", include("apps.common.urls")),
    path("certificates/verify/<str:identifier>/", PublicCertificateVerifyView.as_view(), name="root_public_cert_verify"),
    path("api/v1/", include((api_v1_patterns, "api_v1"))),
    # OpenAPI 3 Schema & Interactive API Explorers
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

