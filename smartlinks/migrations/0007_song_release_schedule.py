from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smartlinks", "0006_song_urls_textfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="song",
            name="release_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="UTC instant when the track is “out”; used to schedule fan notification.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="song",
            name="release_notification_task_id",
            field=models.CharField(
                blank=True,
                help_text="Celery task id for the scheduled fan notification (internal).",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="song",
            name="release_timezone",
            field=models.CharField(
                default="UTC",
                help_text="IANA zone for how the release time was chosen (for future email copy).",
                max_length=64,
            ),
        ),
    ]
