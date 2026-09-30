"""Admin URL routes for curriculum module management."""

from django.urls import path

from apps.modules.admin_views import (
    ModuleAdminDetailUpdateView,
    ModuleAdminListCreateView,
    ModuleAdminPublishView,
    ModuleAdminReorderView,
)

app_name = "admin_modules"

urlpatterns = [
    path("", ModuleAdminListCreateView.as_view(), name="list_create"),
    path("reorder/", ModuleAdminReorderView.as_view(), name="reorder"),
    path("<uuid:pk>/", ModuleAdminDetailUpdateView.as_view(), name="detail_update"),
    path("<uuid:pk>/publish/", ModuleAdminPublishView.as_view(), name="publish"),
]
