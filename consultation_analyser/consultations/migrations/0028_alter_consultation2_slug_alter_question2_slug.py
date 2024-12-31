# Generated by Django 5.1.4 on 2024-12-31 11:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("consultations", "0027_update_all_consultation_models"),
    ]

    operations = [
        migrations.AlterField(
            model_name="consultation2",
            name="slug",
            field=models.SlugField(editable=False, max_length=256),
        ),
        migrations.AlterField(
            model_name="question2",
            name="slug",
            field=models.SlugField(editable=False, max_length=256),
        ),
    ]
