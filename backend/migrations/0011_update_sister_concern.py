# Generated for Sister Concern admin/frontend update.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0010_aboutherosection_video_file"),
    ]

    operations = [
        migrations.RenameField(
            model_name="sisterconcern",
            old_name="image",
            new_name="logo",
        ),
        migrations.AlterField(
            model_name="sisterconcern",
            name="description",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="sisterconcern",
            name="logo",
            field=models.ImageField(upload_to="sister_concerns/logos/"),
        ),
        migrations.RemoveField(
            model_name="sisterconcern",
            name="icon",
        ),
        migrations.AddField(
            model_name="sisterconcern",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="sisterconcern",
            name="is_active",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="sisterconcern",
            name="sort_order",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name="sisterconcern",
            options={"ordering": ["sort_order", "title"]},
        ),
        migrations.AlterField(
            model_name="sisterconcern",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
