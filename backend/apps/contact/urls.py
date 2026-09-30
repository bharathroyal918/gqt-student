"""URL routes for student and public contact endpoints."""

from django.urls import path

from apps.contact.views import CompanyInfoView, ContactInquirySubmitView

app_name = "contact"

urlpatterns = [
    path("info/", CompanyInfoView.as_view(), name="company_info"),
    path("inquiries/", ContactInquirySubmitView.as_view(), name="inquiry_submit"),
]
