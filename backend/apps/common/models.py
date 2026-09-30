import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract model providing self-updating created_at and updated_at fields."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(models.Model):
    """Abstract model providing UUID primary keys to prevent enumeration attacks."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """Abstract model providing soft-activation toggle."""

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Primary base model combining UUID primary key and timestamp audit tracking."""

    class Meta:
        abstract = True
