from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smartlinks", "0012_remove_song_release_notification_task_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="song",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Optional. Shown on the minimal landing template under the artist line.",
            ),
        ),
    ]
