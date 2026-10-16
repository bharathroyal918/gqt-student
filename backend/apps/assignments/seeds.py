"""Seed initial production-grade coding challenges with starter codes and test cases."""

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError


def seed_coding_questions():
    """Seed comprehensive coding questions across all curriculum modules."""
    try:
        call_command("seed_curriculum_questions")
    except (CommandError, DatabaseError, OSError, ValueError, RuntimeError) as e:
        print(f"Error seeding coding questions: {e}")
