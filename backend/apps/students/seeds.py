"""Default institutional colleges seed data."""

import logging
from apps.students.models import College

logger = logging.getLogger(__name__)

DEFAULT_COLLEGES = [
    {
        "name": "GQT Academy of Technology & Research",
        "code": "GQT-TECH",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "GQT Engineering & Innovation Campus",
        "code": "GQT-ENG",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_active": True,
    },
    {
        "name": "RV College of Engineering",
        "code": "RVCE",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "PES University",
        "code": "PESU",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "BMS College of Engineering",
        "code": "BMSCE",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "MS Ramaiah Institute of Technology",
        "code": "MSRIT",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "Bangalore Institute of Technology",
        "code": "BIT",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "Dayananda Sagar College of Engineering",
        "code": "DSCE",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "Sir M Visvesvaraya Institute of Technology",
        "code": "SMVIT",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "JNTU College of Engineering",
        "code": "JNTUH",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_active": True,
    },
    {
        "name": "Osmania University College of Engineering",
        "code": "OUCE",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_active": True,
    },
    {
        "name": "Chaitanya Bharathi Institute of Technology",
        "code": "CBIT",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_active": True,
    },
    {
        "name": "Vasavi College of Engineering",
        "code": "VCE",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_active": True,
    },
    {
        "name": "VNR Vignana Jyothi Institute of Engineering & Technology",
        "code": "VNRVJIET",
        "city": "Hyderabad",
        "state": "Telangana",
        "is_active": True,
    },
    {
        "name": "College of Engineering Guindy, Anna University",
        "code": "CEG",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "is_active": True,
    },
    {
        "name": "PSG College of Technology",
        "code": "PSG",
        "city": "Coimbatore",
        "state": "Tamil Nadu",
        "is_active": True,
    },
    {
        "name": "Vellore Institute of Technology",
        "code": "VIT",
        "city": "Vellore",
        "state": "Tamil Nadu",
        "is_active": True,
    },
    {
        "name": "Manipal Institute of Technology",
        "code": "MIT",
        "city": "Manipal",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "National Institute of Technology Karnataka",
        "code": "NITK",
        "city": "Surathkal",
        "state": "Karnataka",
        "is_active": True,
    },
    {
        "name": "Indian Institute of Information Technology",
        "code": "IIITB",
        "city": "Bengaluru",
        "state": "Karnataka",
        "is_active": True,
    },
]


def seed_default_colleges():
    """Seed initial approved institutional colleges if none exist."""
    count = 0
    for col_data in DEFAULT_COLLEGES:
        obj, created = College.objects.get_or_create(
            name=col_data["name"],
            defaults=col_data,
        )
        if created:
            count += 1
    if count > 0:
        logger.info("Successfully seeded %d initial institutional colleges.", count)
    return count
