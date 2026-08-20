from django.conf import settings
from django.db import models


class Client(models.Model):
    """An organisation whose potential PR opportunities Pathos evaluates."""

    company_name = models.CharField(max_length=255)
    industry = models.CharField(max_length=150)
    location = models.CharField(max_length=255)
    website = models.URLField(max_length=500)
    description = models.TextField()
    company_size = models.CharField(max_length=100)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="created_clients",
    )
    authorized_consultants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="authorized_clients",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["company_name", "id"]

    def __str__(self) -> str:
        return self.company_name
