# Generated for Sister Concern page banner.

import backend.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0011_update_sister_concern"),
    ]

    operations = [
        migrations.CreateModel(
            name="SisterConcernBanner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Sister Concern", max_length=100)),
                (
                    "banner_image",
                    models.ImageField(
                        upload_to="sister_concerns/banner/",
                        validators=[backend.models.validate_banner_image],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
    ]
