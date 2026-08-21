import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("angles", "0001_initial")]
    operations = [
        migrations.AlterField(
            model_name="anglegeneration",
            name="score",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="angle_generations", to="scoring.opportunityscore"),
        ),
    ]
