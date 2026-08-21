from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("opportunities", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="OpportunityScore", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("overall_score", models.PositiveSmallIntegerField()), ("potential", models.CharField(choices=[("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")], max_length=10)), ("newsworthiness_score", models.PositiveSmallIntegerField()), ("media_appeal_score", models.PositiveSmallIntegerField()), ("timeliness_score", models.PositiveSmallIntegerField()), ("credibility_score", models.PositiveSmallIntegerField()), ("audience_interest_score", models.PositiveSmallIntegerField()), ("scoring_version", models.CharField(default="v1", max_length=20)), ("metadata", models.JSONField(default=dict)), ("scored_at", models.DateTimeField(auto_now_add=True)), ("opportunity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="opportunities.opportunity")), ("scored_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="opportunity_scores", to=settings.AUTH_USER_MODEL))], options={"ordering": ["-scored_at", "-id"]}), migrations.AddIndex(model_name="opportunityscore", index=models.Index(fields=["opportunity", "-scored_at"], name="scoring_opp_opportu_080644_idx"))]
