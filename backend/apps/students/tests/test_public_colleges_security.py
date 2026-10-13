"""Tests for SEC-12: Public college list read-only behavior, bounded search, and explicit seed command."""

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.students.models import College


class PublicCollegeListSecurityTests(TestCase):
    """SEC-12: Verify PublicCollegeListView is strictly read-only and bounded."""

    def setUp(self):
        self.client = APIClient()
        self.colleges_url = reverse("api_v1:students:public_colleges_list")

    def test_get_on_empty_table_performs_no_writes(self):
        """GET request on empty table must NOT seed or insert records into the database."""
        assert College.objects.count() == 0

        response = self.client.get(self.colleges_url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json().get("data", [])
        assert data == []
        # Crucial check: No records were inserted into the database during GET
        assert College.objects.count() == 0

    def test_get_returns_active_colleges_with_bounded_search(self):
        """Active colleges are returned and search is bounded."""
        c1 = College.objects.create(name="Alpha Institute", code="ALPHA", is_active=True)
        c2 = College.objects.create(name="Beta College", code="BETA", is_active=True)
        c3 = College.objects.create(name="Gamma University", code="GAMMA", is_active=False)

        # List all active
        res = self.client.get(self.colleges_url)
        assert res.status_code == status.HTTP_200_OK
        items = res.json().get("data", [])
        names = [item["name"] for item in items]
        assert "Alpha Institute" in names
        assert "Beta College" in names
        assert "Gamma University" not in names  # Inactive excluded

        # Filter with bounded search
        search_res = self.client.get(self.colleges_url, {"search": "Alpha"})
        search_items = search_res.json().get("data", [])
        assert len(search_items) == 1
        assert search_items[0]["name"] == "Alpha Institute"

    def test_management_command_seeds_colleges(self):
        """Explicit seed_colleges management command seeds records safely."""
        assert College.objects.count() == 0
        call_command("seed_colleges")
        assert College.objects.count() > 0
