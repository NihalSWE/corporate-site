# Generated for About Us badge image validation.

import backend.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0016_aboutherosection_badge_image"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aboutherosection",
            name="badge_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="about/hero/badge/",
                validators=[backend.models.validate_about_badge_image],
            ),
        ),
    ]
