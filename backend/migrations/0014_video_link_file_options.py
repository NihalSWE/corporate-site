# Generated for flexible video gallery sources.

import backend.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0013_gallery_update"),
    ]

    operations = [
        migrations.AlterField(
            model_name="video",
            name="url",
            field=models.URLField(blank=True, help_text="YouTube, Vimeo, Facebook, or direct video link", null=True),
        ),
        migrations.AlterField(
            model_name="video",
            name="video_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="gallery/videos/",
                validators=[backend.models.validate_gallery_video_file],
            ),
        ),
    ]
