# Generated to remove the About Us business section.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("backend", "0014_video_link_file_options"),
    ]

    operations = [
        migrations.DeleteModel(
            name="AboutBusinessSection",
        ),
    ]
