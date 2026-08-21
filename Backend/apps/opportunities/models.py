from django.conf import settings
from django.db import models

from apps.clients.models import Client


class Opportunity(models.Model):
    """A prospective client story collected before PR analysis begins."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        READY_FOR_ANALYSIS = "ready_for_analysis", "Ready for analysis"
        ANALYZED = "analyzed", "Analyzed"
        ARCHIVED = "archived", "Archived"

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="opportunities")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    story_type = models.CharField(max_length=100, blank=True)
    funding_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    funding_stage = models.CharField(max_length=100, blank=True)
    founder_available = models.BooleanField(null=True, blank=True)
    product_launched = models.BooleanField(null=True, blank=True)
    product_launch_date = models.DateField(null=True, blank=True)
    customer_count = models.PositiveIntegerField(null=True, blank=True)
    revenue_information = models.TextField(blank=True)
    geographic_relevance = models.TextField(blank=True)
    target_audience = models.TextField(blank=True)
    supporting_information = models.TextField(blank=True)
    client_briefing = models.TextField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="created_opportunities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        indexes = [
            models.Index(fields=["client", "status"], name="opportuniti_client__4d9865_idx"),
            models.Index(fields=["status", "-updated_at"], name="opportuniti_status_70dc5d_idx"),
        ]

    def __str__(self) -> str:
        return self.title
