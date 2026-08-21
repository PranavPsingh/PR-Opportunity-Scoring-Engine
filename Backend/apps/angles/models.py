from django.conf import settings
from django.db import models

from apps.opportunities.models import Opportunity
from apps.scoring.models import OpportunityScore


class AngleGeneration(models.Model):
    """An immutable, timestamped set of PR angle recommendations."""

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="angle_generations")
    score = models.ForeignKey(OpportunityScore, null=True, blank=True, on_delete=models.SET_NULL, related_name="angle_generations")
    provider = models.CharField(max_length=100)
    model_identifier = models.CharField(max_length=255)
    input_facts = models.JSONField(default=list)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="angle_generations")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["opportunity", "-created_at"])]


class PRAngle(models.Model):
    class Potential(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    generation = models.ForeignKey(AngleGeneration, on_delete=models.CASCADE, related_name="angles")
    title = models.CharField(max_length=255)
    summary = models.TextField()
    potential_score = models.PositiveSmallIntegerField()
    potential_level = models.CharField(max_length=10, choices=Potential.choices)
    rationale = models.TextField()
    target_audience = models.JSONField(default=list)
    media_categories = models.JSONField(default=list)
    key_message = models.TextField()
    supporting_facts = models.JSONField(default=list)
    required_evidence = models.JSONField(default=list)
    risks = models.JSONField(default=list)
    missing_information = models.JSONField(default=list)
    selected = models.BooleanField(default=False)

    class Meta:
        ordering = ["-potential_score", "id"]
