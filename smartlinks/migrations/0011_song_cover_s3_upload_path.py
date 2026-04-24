import smartlinks.upload_paths
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smartlinks", "0010_song_owner"),
    ]

    operations = [
        migrations.AlterField(
            model_name="song",
            name="cover_art",
            field=models.ImageField(
                help_text="Stored under your account in S3 when configured (see AWS_* env vars).",
                max_length=512,
                upload_to=smartlinks.upload_paths.song_cover_upload_to,
            ),
        ),
    ]
