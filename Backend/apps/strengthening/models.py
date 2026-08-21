from django.db import models

from apps.angles.models import PRAngle
from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore


class StoryStrengtheningAnalysis(models.Model):
    """Immutable snapshot of one grounded strengthening analysis."""

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="strengthening_analyses")
    score = models.ForeignKey(OpportunityScore, null=True, blank=True, on_delete=models.SET_NULL, related_name="strengthening_analyses")
    source_snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["opportunity", "-created_at"])]


class StoryStrengtheningRecommendation(models.Model):
    class Severity(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        COMPLETED = "COMPLETED", "Completed"
        DISMISSED = "DISMISSED", "Dismissed"

    analysis = models.ForeignKey(StoryStrengtheningAnalysis, on_delete=models.CASCADE, related_name="recommendations")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="strengthening_recommendations")
    angle = models.ForeignKey(PRAngle, null=True, blank=True, on_delete=models.SET_NULL, related_name="strengthening_recommendations")
    title = models.CharField(max_length=255)
    weakness = models.TextField()
    affected_dimension = models.CharField(max_length=50)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    explanation = models.TextField()
    recommendation = models.TextField()
    required_information = models.JSONField(default=list)
    required_evidence = models.JSONField(default=list)
    expected_benefit = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    source_factors = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["severity", "id"]
        indexes = [models.Index(fields=["opportunity", "status"])]
