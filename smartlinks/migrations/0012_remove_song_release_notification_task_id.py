from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("smartlinks", "0011_song_cover_s3_upload_path"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="song",
            name="release_notification_task_id",
        ),
    ]
