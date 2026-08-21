import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("opportunities", "0001_initial"), ("scoring", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="AngleGeneration", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("provider", models.CharField(max_length=100)), ("model_identifier", models.CharField(max_length=255)), ("input_facts", models.JSONField(default=list)), ("created_at", models.DateTimeField(auto_now_add=True)), ("created_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="angle_generations", to=settings.AUTH_USER_MODEL)), ("opportunity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="angle_generations", to="opportunities.opportunity")), ("score", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="angle_generations", to="scoring.opportunityscore"))], options={"ordering": ["-created_at", "-id"]}),
        migrations.CreateModel(name="PRAngle", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=255)), ("summary", models.TextField()), ("potential_score", models.PositiveSmallIntegerField()), ("potential_level", models.CharField(choices=[("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")], max_length=10)), ("rationale", models.TextField()), ("target_audience", models.JSONField(default=list)), ("media_categories", models.JSONField(default=list)), ("key_message", models.TextField()), ("supporting_facts", models.JSONField(default=list)), ("required_evidence", models.JSONField(default=list)), ("risks", models.JSONField(default=list)), ("missing_information", models.JSONField(default=list)), ("selected", models.BooleanField(default=False)), ("generation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="angles", to="angles.anglegeneration"))], options={"ordering": ["-potential_score", "id"]}),
        migrations.AddIndex(model_name="anglegeneration", index=models.Index(fields=["opportunity", "-created_at"], name="angles_angle_opportu_2a48cf_idx")),
    ]
