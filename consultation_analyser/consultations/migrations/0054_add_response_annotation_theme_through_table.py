# Custom migration to handle M2M field with through table

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def migrate_existing_themes(apps, schema_editor):
    """Migrate existing M2M relationships to the new through table"""
    ResponseAnnotation = apps.get_model('consultations', 'ResponseAnnotation')
    Theme = apps.get_model('consultations', 'Theme')
    ResponseAnnotationTheme = apps.get_model('consultations', 'ResponseAnnotationTheme')
    
    # Get the through table name for the old M2M field
    old_through_table = 'consultations_responseannotation_themes'
    
    # Check if the old table exists before trying to migrate data
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = %s
        """, [old_through_table])
        
        if cursor.fetchone()[0] > 0:
            # Migrate existing relationships as original AI assignments
            cursor.execute(f"""
                INSERT INTO consultations_responseannotationtheme 
                (id, created_at, modified_at, response_annotation_id, theme_id, is_original_ai_assignment, assigned_by_id)
                SELECT 
                    gen_random_uuid(),
                    NOW(),
                    NOW(),
                    responseannotation_id,
                    theme_id,
                    true,
                    NULL
                FROM {old_through_table}
            """)


def reverse_migrate_themes(apps, schema_editor):
    """Reverse migration - recreate simple M2M relationships"""
    # This would be complex to implement properly, so we'll just pass
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0053_merge_20250613_1223"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Step 1: Create the through model
        migrations.CreateModel(
            name="ResponseAnnotationTheme",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                ("is_original_ai_assignment", models.BooleanField(default=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "response_annotation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="consultations.responseannotation",
                    ),
                ),
                (
                    "theme",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, 
                        to="consultations.theme"
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
                "abstract": False,
            },
        ),
        
        # Step 2: Add indexes and constraints to the through model
        migrations.AddIndex(
            model_name="responseannotationtheme",
            index=models.Index(
                fields=["response_annotation", "is_original_ai_assignment"],
                name="consultatio_respons_cfc7ac_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="responseannotationtheme",
            index=models.Index(
                fields=["theme", "is_original_ai_assignment"],
                name="consultatio_theme_i_16a421_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="responseannotationtheme",
            constraint=models.UniqueConstraint(
                fields=("response_annotation", "theme", "is_original_ai_assignment"),
                name="unique_theme_assignment",
            ),
        ),
        
        # Step 3: Migrate existing data
        migrations.RunPython(
            migrate_existing_themes,
            reverse_migrate_themes,
        ),
        
        # Step 4: Remove the old M2M field
        migrations.RemoveField(
            model_name="responseannotation",
            name="themes",
        ),
        
        # Step 5: Add the new M2M field with through table
        migrations.AddField(
            model_name="responseannotation",
            name="themes",
            field=models.ManyToManyField(
                blank=True,
                through="consultations.ResponseAnnotationTheme",
                to="consultations.theme",
            ),
        ),
    ]