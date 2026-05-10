# Generated for video and photo gallery update.

import backend.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0012_sisterconcernbanner"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhotoGalleryBanner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Photo Gallery", max_length=100)),
                (
                    "banner_image",
                    models.ImageField(
                        upload_to="gallery/photo/banner/",
                        validators=[backend.models.validate_banner_image],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="VideoGalleryBanner",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(default="Video Gallery", max_length=100)),
                (
                    "banner_image",
                    models.ImageField(
                        upload_to="gallery/video/banner/",
                        validators=[backend.models.validate_banner_image],
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name="gallery_album",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="gallery_album",
            name="sort_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="gallery_albumdetails",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="gallery_albumdetails",
            name="sort_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="video",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="video",
            name="sort_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="video",
            name="video_file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="gallery/videos/",
                validators=[backend.models.validate_gallery_video_file],
            ),
        ),
        migrations.AlterField(
            model_name="video",
            name="url",
            field=models.URLField(blank=True, help_text="Legacy video URL", null=True),
        ),
        migrations.AlterModelOptions(
            name="gallery_album",
            options={"ordering": ["sort_order", "-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="gallery_albumdetails",
            options={"ordering": ["sort_order", "-uploaded_at"]},
        ),
        migrations.AlterModelOptions(
            name="video",
            options={"ordering": ["sort_order", "-created_at"]},
        ),
    ]
