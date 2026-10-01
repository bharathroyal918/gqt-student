"""Generate complete Supabase PostgreSQL SQL DDL schema for all Django apps."""

import os
import sys
from pathlib import Path
from io import StringIO

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/postgres"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django
django.setup()

from django.core.management import call_command
from django.db.migrations.loader import MigrationLoader
from django.db import DEFAULT_DB_ALIAS, connections

loader = MigrationLoader(connections[DEFAULT_DB_ALIAS])
ordered_nodes = loader.graph.forwards_plan(list(loader.graph.leaf_nodes()))

output_file = BASE_DIR / "supabase_schema.sql"
print(f"Generating PostgreSQL schema for {len(ordered_nodes)} migrations...")

with open(output_file, "w", encoding="utf-8") as f:
    f.write("-- ==============================================================================\n")
    f.write("-- GQT STUDENT PORTAL - COMPLETE SUPABASE POSTGRESQL SCHEMA DDL\n")
    f.write("-- Generated automatically from Django migrations for Supabase Project\n")
    f.write("-- ==============================================================================\n\n")

    for app_label, migration_name in ordered_nodes:
        f.write(f"\n-- >>> Application: {app_label} | Migration: {migration_name} <<<\n")
        out = StringIO()
        try:
            call_command("sqlmigrate", app_label, migration_name, stdout=out)
            f.write(out.getvalue())
        except Exception as exc:
            f.write(f"-- Migration {app_label}.{migration_name} skipped or failed: {exc}\n")

print(f"Supabase PostgreSQL schema written to: {output_file}")
