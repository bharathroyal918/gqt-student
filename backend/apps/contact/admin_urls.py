"""URL routing for Admin Contact Inquiry management."""

from django.urls import path

from apps.contact.admin_views import (
    AdminContactInquiryDetailView,
    AdminContactInquiryListView,
)

app_name = "admin_contact"

urlpatterns = [
    path("inquiries/", AdminContactInquiryListView.as_view(), name="inquiry_list"),
    path(
        "inquiries/<uuid:inquiry_id>/",
        AdminContactInquiryDetailView.as_view(),
        name="inquiry_detail",
    ),
]
