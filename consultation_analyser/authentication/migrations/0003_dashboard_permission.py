# Allow users to view dashboard
from django.db import migrations


def create_dashboard_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.create(name="Dashboard access")


def delete_dashboard_viewer_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Dashboard access").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0002_insert_user"),
    ]
    operations = [
        migrations.RunPython(create_dashboard_permission),
    ]
