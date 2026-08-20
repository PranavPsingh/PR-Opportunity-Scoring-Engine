from django.contrib.auth.hashers import make_password
from django.db import migrations


DEMO_PASSWORD = "PathosDemo2026!"
DEMO_USERS = (
    ("admin@pathos.local", "Avery Admin", "admin", True),
    ("alex@pathos.local", "Alex Consultant", "consultant", False),
    ("jamie@pathos.local", "Jamie Consultant", "consultant", False),
    ("morgan@pathos.local", "Morgan Consultant", "consultant", False),
    ("taylor@pathos.local", "Taylor Consultant", "consultant", False),
)


def seed_demo_users(apps, schema_editor):
    User = apps.get_model("users", "User")
    for email, name, role, is_staff in DEMO_USERS:
        User.objects.get_or_create(
            email=email,
            defaults={
                "name": name,
                "role": role,
                "is_staff": is_staff,
                "is_active": True,
                "password": make_password(DEMO_PASSWORD),
            },
        )


def remove_demo_users(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(email__in=[entry[0] for entry in DEMO_USERS]).delete()


class Migration(migrations.Migration):
    dependencies = [("users", "0001_initial")]

    operations = [migrations.RunPython(seed_demo_users, remove_demo_users)]
