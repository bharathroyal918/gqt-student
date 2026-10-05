"""Placement drive business services and Supabase synchronization logic."""

import logging
from typing import Any, Dict, Optional
from django.db.models import Count, Q
from django.utils import timezone

from apps.common.supabase import get_supabase_admin_client, get_supabase_client
from apps.placements.models import PlacementApplication, PlacementDrive

logger = logging.getLogger(__name__)


class PlacementService:
    """Service layer for Placement Drives and Application workflows."""

    @staticmethod
    def sync_drive_to_supabase(drive: PlacementDrive) -> bool:
        """Mirror or sync placement drive to Supabase if configured."""
        try:
            client = get_supabase_admin_client() or get_supabase_client()
            if not client:
                return False

            payload = {
                "id": str(drive.id),
                "company_name": drive.company_name,
                "company_code": drive.company_code,
                "role": drive.role,
                "skills": drive.skills,
                "location": drive.location,
                "mode_of_work": drive.mode_of_work,
                "stipend_or_ctc": drive.stipend_or_ctc,
                "bond_period": drive.bond_period,
                "eligibility_criteria": drive.eligibility_criteria,
                "min_cgpa": float(drive.min_cgpa),
                "eligible_batches": drive.eligible_batches,
                "job_description": drive.job_description,
                "application_deadline": drive.application_deadline.isoformat() if drive.application_deadline else None,
                "status": drive.status,
                "is_active": drive.is_active,
                "updated_at": timezone.now().isoformat(),
            }
            # Upsert into placement_drives table
            client.table("placement_drives").upsert(payload).execute()
            logger.info(f"Synced Placement Drive {drive.id} ({drive.company_name}) to Supabase")
            return True
        except Exception as exc:
            logger.warning(f"Supabase drive sync skipped or not ready: {exc}")
            return False

    @staticmethod
    def sync_application_to_supabase(application: PlacementApplication) -> bool:
        """Mirror student placement application data to Supabase."""
        try:
            client = get_supabase_admin_client() or get_supabase_client()
            if not client:
                return False

            payload = {
                "id": str(application.id),
                "drive_id": str(application.drive_id),
                "student_id": str(application.student_id),
                "student_name": application.student_name,
                "student_id_number": application.student_id_number,
                "email": application.email,
                "phone_number": application.phone_number,
                "college_name": application.college_name,
                "branch": application.branch,
                "graduation_year": application.graduation_year,
                "cgpa_or_percentage": application.cgpa_or_percentage,
                "resume_url": application.resume_url,
                "github_url": application.github_url,
                "linkedin_url": application.linkedin_url,
                "portfolio_url": application.portfolio_url,
                "skills_summary": application.skills_summary,
                "cover_note": application.cover_note,
                "status": application.status,
                "admin_notes": application.admin_notes,
                "rejection_reason": application.rejection_reason,
                "submitted_at": application.submitted_at.isoformat() if application.submitted_at else timezone.now().isoformat(),
                "updated_at": timezone.now().isoformat(),
            }
            client.table("placement_applications").upsert(payload).execute()
            logger.info(f"Synced Placement Application {application.id} for student {application.student_name} to Supabase")
            return True
        except Exception as exc:
            logger.warning(f"Supabase application sync skipped or not ready: {exc}")
            return False

    @staticmethod
    def get_admin_metrics() -> Dict[str, Any]:
        """Aggregate high-level metrics for admin dashboard."""
        total_drives = PlacementDrive.objects.count()
        active_drives = PlacementDrive.objects.filter(is_active=True, status=PlacementDrive.DriveStatus.ONGOING).count()
        total_applications = PlacementApplication.objects.count()
        selected_candidates = PlacementApplication.objects.filter(status=PlacementApplication.ApplicationStatus.SELECTED).count()
        shortlisted_candidates = PlacementApplication.objects.filter(status=PlacementApplication.ApplicationStatus.SHORTLISTED).count()
        rejected_candidates = PlacementApplication.objects.filter(status=PlacementApplication.ApplicationStatus.REJECTED).count()

        return {
            "total_drives": total_drives,
            "active_drives": active_drives,
            "total_applications": total_applications,
            "selected_candidates": selected_candidates,
            "shortlisted_candidates": shortlisted_candidates,
            "rejected_candidates": rejected_candidates,
        }

    @staticmethod
    def get_drive_stats(drive: PlacementDrive) -> Dict[str, int]:
        """Get application breakdown for a specific drive."""
        stats = drive.applications.aggregate(
            total=Count("id"),
            applied=Count("id", filter=Q(status=PlacementApplication.ApplicationStatus.APPLIED)),
            under_review=Count("id", filter=Q(status=PlacementApplication.ApplicationStatus.UNDER_REVIEW)),
            shortlisted=Count("id", filter=Q(status=PlacementApplication.ApplicationStatus.SHORTLISTED)),
            selected=Count("id", filter=Q(status=PlacementApplication.ApplicationStatus.SELECTED)),
            rejected=Count("id", filter=Q(status=PlacementApplication.ApplicationStatus.REJECTED)),
        )
        return {
            "total": stats["total"] or 0,
            "applied": stats["applied"] or 0,
            "under_review": stats["under_review"] or 0,
            "shortlisted": stats["shortlisted"] or 0,
            "selected": stats["selected"] or 0,
            "rejected": stats["rejected"] or 0,
        }
