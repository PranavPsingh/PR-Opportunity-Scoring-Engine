from django.conf import settings
from django.db import models

from apps.opportunities.models import Opportunity


class OpportunityScore(models.Model):
    """An immutable, versioned result from the deterministic scoring engine."""

    class Potential(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="scores")
    overall_score = models.PositiveSmallIntegerField()
    potential = models.CharField(max_length=10, choices=Potential.choices)
    newsworthiness_score = models.PositiveSmallIntegerField()
    media_appeal_score = models.PositiveSmallIntegerField()
    timeliness_score = models.PositiveSmallIntegerField()
    credibility_score = models.PositiveSmallIntegerField()
    audience_interest_score = models.PositiveSmallIntegerField()
    scoring_version = models.CharField(max_length=20, default="v1")
    metadata = models.JSONField(default=dict)
    scored_at = models.DateTimeField(auto_now_add=True)
    scored_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="opportunity_scores")

    class Meta:
        ordering = ["-scored_at", "-id"]
        indexes = [models.Index(fields=["opportunity", "-scored_at"])]

