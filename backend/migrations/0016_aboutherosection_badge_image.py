# Generated for dynamic About Us badge image.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0015_remove_about_business_section"),
    ]

    operations = [
        migrations.AddField(
            model_name="aboutherosection",
            name="badge_image",
            field=models.ImageField(blank=True, null=True, upload_to="about/hero/badge/"),
        ),
    ]
