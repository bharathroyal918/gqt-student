"""Seed initial rich placement drives and sample student applications."""

import os
import sys
import django
from datetime import timedelta
from decimal import Decimal

# Setup django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.utils import timezone
from apps.placements.models import PlacementDrive, PlacementApplication
from apps.students.models import StudentProfile
from apps.accounts.models import User

def seed():
    print("Seeding placement drives...")
    now = timezone.now()

    drives_data = [
        {
            "company_name": "Google Cloud",
            "company_code": "GOOG-CLOUD-2026",
            "role": "Cloud Solutions & Backend Engineer",
            "skills": "Python, Go, Kubernetes, Cloud Architecture, REST APIs, PostgreSQL",
            "location": "Bengaluru, Karnataka / Hyderabad",
            "mode_of_work": PlacementDrive.WorkMode.HYBRID,
            "stipend_or_ctc": "₹18.0 - ₹24.0 LPA",
            "bond_period": "None",
            "eligibility_criteria": "B.Tech / BE / MCA in CSE, ISE, ECE, IT. Minimum 7.5 CGPA (75%) with no active backlogs.",
            "min_cgpa": Decimal("7.50"),
            "eligible_batches": "2025, 2026",
            "job_description": "We are seeking proactive Backend & Cloud Solutions Engineers to design, build, and deploy resilient scalable cloud microservices. Responsibilities include API design, infrastructure optimization, automated testing, and collaborating with global product squads.",
            "application_deadline": now + timedelta(days=21),
            "drive_date": now + timedelta(days=28),
            "status": PlacementDrive.DriveStatus.ONGOING,
            "company_logo_url": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
        },
        {
            "company_name": "TCS Digital",
            "company_code": "TCS-DIG-2026",
            "role": "Software Development Engineer (Digital Innovator)",
            "skills": "Java, Spring Boot, React.js, Data Structures, Algorithms, SQL",
            "location": "Bengaluru / Pune / Chennai / Hyderabad",
            "mode_of_work": PlacementDrive.WorkMode.HYBRID,
            "stipend_or_ctc": "₹7.5 - ₹9.0 LPA + Joining Bonus",
            "bond_period": "1 Year Service Agreement",
            "eligibility_criteria": "BE/B.Tech (All Engineering branches eligible). Minimum 60% or 6.0 CGPA throughout 10th, 12th, and Degree. Max 1 active backlog allowed.",
            "min_cgpa": Decimal("6.00"),
            "eligible_batches": "2025, 2026",
            "job_description": "TCS Digital hiring drive selects top coders and problem solvers to build next-generation enterprise solutions across fintech, healthcare, and retail sectors.",
            "application_deadline": now + timedelta(days=14),
            "drive_date": now + timedelta(days=18),
            "status": PlacementDrive.DriveStatus.ONGOING,
            "company_logo_url": "https://upload.wikimedia.org/wikipedia/commons/b/b1/Tata_Consultancy_Services_Logo.svg",
        },
        {
            "company_name": "Amazon Web Services (AWS)",
            "company_code": "AWS-SDE1-2026",
            "role": "Software Development Engineer (SDE-1)",
            "skills": "Java, C++, Object Oriented Design, Distributed Systems, AWS Services",
            "location": "Bengaluru / Hyderabad",
            "mode_of_work": PlacementDrive.WorkMode.ON_SITE,
            "stipend_or_ctc": "₹28.0 - ₹34.0 LPA (₹60,000/mo Internship stipend)",
            "bond_period": "None",
            "eligibility_criteria": "B.Tech/M.Tech (CS, IS, EC, AI/ML, Data Science). Minimum 7.0 CGPA. Strong foundational command of algorithms and data structures.",
            "min_cgpa": Decimal("7.00"),
            "eligible_batches": "2025, 2026",
            "job_description": "Join AWS as an SDE-1 to build high-scale, ultra-reliable distributed systems powering billions of transactions globally. You will write clean, well-tested code, participate in architectural design, and push deployments with CI/CD.",
            "application_deadline": now + timedelta(days=10),
            "drive_date": now + timedelta(days=15),
            "status": PlacementDrive.DriveStatus.ONGOING,
            "company_logo_url": "https://upload.wikimedia.org/wikipedia/commons/9/93/Amazon_Web_Services_Logo.svg",
        },
        {
            "company_name": "Accenture",
            "company_code": "ACN-ASE-2026",
            "role": "Associate Software Engineer (Advanced Technology Centers)",
            "skills": "Full Stack, JavaScript, Python, DBMS, Cloud Fundamentals",
            "location": "PAN India (Bengaluru, Mumbai, Delhi-NCR, Hyderabad)",
            "mode_of_work": PlacementDrive.WorkMode.HYBRID,
            "stipend_or_ctc": "₹4.5 - ₹6.5 LPA",
            "bond_period": "None",
            "eligibility_criteria": "All streams of B.E/B.Tech/MCA. Minimum 6.5 CGPA with no pending backlogs at the time of joining.",
            "min_cgpa": Decimal("6.50"),
            "eligible_batches": "2024, 2025, 2026",
            "job_description": "Accenture is hiring Associate Software Engineers to work with global Fortune 500 clients. You will undergo extensive training on full-stack web and cloud platforms before project deployment.",
            "application_deadline": now + timedelta(days=30),
            "drive_date": now + timedelta(days=35),
            "status": PlacementDrive.DriveStatus.UPCOMING,
            "company_logo_url": "https://upload.wikimedia.org/wikipedia/commons/c/cd/Accenture.svg",
        },
        {
            "company_name": "Razorpay",
            "company_code": "RZP-FE-2026",
            "role": "Frontend / React Engineer (Fintech)",
            "skills": "TypeScript, React, Redux/Zustand, Tailwind CSS, Web Performance, Unit Testing",
            "location": "Bengaluru (Koramangala) / Remote Option",
            "mode_of_work": PlacementDrive.WorkMode.REMOTE,
            "stipend_or_ctc": "₹14.0 - ₹18.0 LPA",
            "bond_period": "None",
            "eligibility_criteria": "B.Tech/BE/BCA/MCA. Minimum 6.8 CGPA. Proven hands-on projects or open-source frontend contributions.",
            "min_cgpa": Decimal("6.80"),
            "eligible_batches": "2025, 2026",
            "job_description": "Razorpay is building the financial backbone for Indian digital commerce. We want engineers who obsess over UI polish, sub-second web performance, and elegant component architecture.",
            "application_deadline": now + timedelta(days=16),
            "drive_date": now + timedelta(days=22),
            "status": PlacementDrive.DriveStatus.ONGOING,
            "company_logo_url": "https://upload.wikimedia.org/wikipedia/commons/8/89/Razorpay_logo.svg",
        }
    ]

    created_drives = []
    for data in drives_data:
        drive, created = PlacementDrive.objects.update_or_create(
            company_code=data["company_code"],
            defaults=data
        )
        created_drives.append(drive)
        print(f"{'Created' if created else 'Updated'} drive: {drive.company_name} - {drive.role}")

    # Seed sample applications for existing student profiles
    students = list(StudentProfile.objects.all()[:6])
    if students and created_drives:
        statuses = [
            (PlacementApplication.ApplicationStatus.SELECTED, "Candidate excelled in technical interview and system design. Extended formal offer.", ""),
            (PlacementApplication.ApplicationStatus.SHORTLISTED, "Cleared round 1 online assessment. Scheduled for final technical panel.", ""),
            (PlacementApplication.ApplicationStatus.REJECTED, "Does not meet the mandatory criteria or failed coding test cutoff.", "Coding assessment cut-off was not met in Section 2 (Data Structures)."),
            (PlacementApplication.ApplicationStatus.UNDER_REVIEW, "Resume submitted for initial technical screening by the talent acquisition team.", ""),
            (PlacementApplication.ApplicationStatus.APPLIED, "", ""),
        ]

        for i, student in enumerate(students):
            for j, drive in enumerate(created_drives[:3]):
                status_idx = (i + j) % len(statuses)
                st, admin_note, rej_reason = statuses[status_idx]

                app, created = PlacementApplication.objects.update_or_create(
                    drive=drive,
                    student=student,
                    defaults={
                        "status": st,
                        "student_name": student.full_name or student.user.email,
                        "student_id_number": student.student_id_number,
                        "email": student.user.email,
                        "phone_number": "+91 9876543210",
                        "college_name": student.college_name or "GQT Engineering Academy",
                        "branch": student.branch or "Computer Science",
                        "graduation_year": student.graduation_year or 2026,
                        "cgpa_or_percentage": "8.85 CGPA",
                        "resume_url": "https://drive.google.com/file/d/sample-student-resume/view",
                        "portfolio_url": "https://github.com",
                        "github_url": student.github_url or "https://github.com",
                        "linkedin_url": student.linkedin_url or "https://linkedin.com",
                        "skills_summary": "Java, Python, React, PostgreSQL, Docker, Data Structures",
                        "cover_note": "I am passionate about building high-performance systems and have completed capstone projects in full stack web development.",
                        "admin_notes": admin_note,
                        "rejection_reason": rej_reason,
                    }
                )
                print(f"  -> Application: {student.full_name} for {drive.company_name} [{st}]")

    print("Placement seeding completed successfully!")

if __name__ == "__main__":
    seed()
