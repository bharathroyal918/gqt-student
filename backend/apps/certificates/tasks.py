"""Asynchronous PDF certificate document generation worker."""

import concurrent.futures
import io
import logging
import uuid
from typing import Optional

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

_cert_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=3, thread_name_prefix="cert_generator_worker"
)


def _generate_certificate_pdf_worker(certificate_id: str) -> bool:
    """Generate professional PDF certificate document in the background."""
    from apps.certificates.models import Certificate

    try:
        certificate = Certificate.objects.select_related("student", "course").get(id=certificate_id)
    except Certificate.DoesNotExist:
        logger.warning("Certificate %s not found for PDF generation.", certificate_id)
        return False

    try:
        buffer = io.BytesIO()
        # Create landscape canvas (11 x 8.5 inches)
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)

        # 1. Decorative Double Outer Border
        p.setStrokeColor(colors.HexColor("#1e293b"))  # Slate 800
        p.setLineWidth(6)
        p.rect(20, 20, width - 40, height - 40)

        p.setStrokeColor(colors.HexColor("#3b82f6"))  # Brand Blue
        p.setLineWidth(1.5)
        p.rect(26, 26, width - 52, height - 52)

        # 2. Institutional Header & Logo Representation
        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(colors.HexColor("#6366f1"))  # Indigo 500
        p.drawCentredString(width / 2.0, height - 65, "GQT ADVANCED LEARNING & ASSESSMENT PORTAL")

        p.setFont("Helvetica-Bold", 28)
        p.setFillColor(colors.HexColor("#0f172a"))  # Deep slate
        p.drawCentredString(width / 2.0, height - 110, "CERTIFICATE OF COMPLETION")

        # 3. Subtitle / Presentation text
        p.setFont("Helvetica-Oblique", 13)
        p.setFillColor(colors.HexColor("#64748b"))  # Slate 500
        p.drawCentredString(width / 2.0, height - 145, "This is to officially certify that")

        # 4. Student Name
        student_display_name = certificate.student_name or certificate.student.full_name or "Student"
        p.setFont("Helvetica-Bold", 26)
        p.setFillColor(colors.HexColor("#1d4ed8"))  # Vibrant Blue
        p.drawCentredString(width / 2.0, height - 195, student_display_name.upper())

        # Underline for recipient name
        name_width = p.stringWidth(student_display_name.upper(), "Helvetica-Bold", 26)
        p.setStrokeColor(colors.HexColor("#cbd5e1"))
        p.setLineWidth(1)
        p.line((width - name_width) / 2.0 - 20, height - 205, (width + name_width) / 2.0 + 20, height - 205)

        # 5. Program & Course Description
        p.setFont("Helvetica", 13)
        p.setFillColor(colors.HexColor("#334155"))
        p.drawCentredString(
            width / 2.0,
            height - 240,
            "has successfully fulfilled all sequential curriculum requirements and practical milestones in",
        )

        course_title = certificate.course_title or certificate.course.title
        p.setFont("Helvetica-Bold", 20)
        p.setFillColor(colors.HexColor("#0f172a"))
        p.drawCentredString(width / 2.0, height - 280, course_title)

        # 6. Verification Details & Metadata
        issue_date_str = certificate.issued_at.strftime("%B %d, %Y") if certificate.issued_at else timezone.now().strftime("%B %d, %Y")
        
        # Left signature / date column
        p.setFont("Helvetica-Bold", 10)
        p.setFillColor(colors.HexColor("#475569"))
        p.drawString(60, 110, f"Date of Issue: {issue_date_str}")
        p.drawString(60, 90, f"Student ID: {certificate.student.student_id_number}")

        # Right signature / verification column
        p.drawRightString(width - 60, 110, f"Certificate ID: {certificate.certificate_id}")
        p.setFont("Helvetica", 8)
        p.drawRightString(width - 60, 90, f"Verification Hash: {certificate.verification_hash[:24]}...")

        # Center Academic Authority
        p.setFont("Helvetica-Bold", 11)
        p.setFillColor(colors.HexColor("#0f172a"))
        p.drawCentredString(width / 2.0, 95, "Academic Director & Board of Examiners")
        p.setStrokeColor(colors.HexColor("#94a3b8"))
        p.setLineWidth(1)
        p.line(width / 2.0 - 110, 115, width / 2.0 + 110, 115)

        p.showPage()
        p.save()

        # Save generated document into model FileField
        buffer.seek(0)
        file_name = f"{certificate.certificate_id}.pdf"
        certificate.pdf_file.save(file_name, ContentFile(buffer.getvalue()), save=True)
        logger.info("Successfully generated PDF document for certificate %s", certificate.certificate_id)
        return True

    except Exception as exc:
        logger.error("Failed to generate PDF for certificate %s: %s", certificate_id, str(exc))
        return False


def dispatch_async_certificate_generation(certificate_id: str) -> concurrent.futures.Future:
    """Submit PDF document generation to background worker non-blockingly."""
    return _cert_executor.submit(_generate_certificate_pdf_worker, certificate_id)
