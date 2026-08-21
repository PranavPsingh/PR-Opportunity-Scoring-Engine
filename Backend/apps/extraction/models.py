from django.conf import settings
from django.db import models

from apps.opportunities.models import Opportunity


class OpportunityExtraction(models.Model):
    class Status(models.TextChoices):
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="extractions")
    provider = models.CharField(max_length=100)
    model_identifier = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    extracted_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class ExtractionConfirmation(models.Model):
    """A separate immutable consultant decision record for an extraction."""
    extraction = models.OneToOneField(OpportunityExtraction, on_delete=models.CASCADE, related_name="confirmation")
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="extraction_confirmations")
    decisions = models.JSONField(default=dict)
    confirmed_at = models.DateTimeField(auto_now_add=True)
