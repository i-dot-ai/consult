# Add a permission for dashboards
from django.db import migrations


def create_dashboard_permission(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.create(name="Dashboard access")


def delete_dashboard_viewer_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="Dashboard access").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("authentication", "0003_user_groups_user_is_superuser_user_user_permissions"),
    ]
    operations = [
        migrations.RunPython(
            create_dashboard_permission, reverse_code=delete_dashboard_viewer_group
        ),
    ]
