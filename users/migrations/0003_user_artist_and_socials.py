from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0002_user_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="artist_name",
            field=models.CharField(
                blank=True,
                help_text="Public artist / project name shown on smart links when set.",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="instagram",
            field=models.CharField(
                blank=True,
                help_text="Instagram profile URL or handle.",
                max_length=512,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="tiktok",
            field=models.CharField(
                blank=True,
                help_text="TikTok profile URL or @handle.",
                max_length=512,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="youtube",
            field=models.CharField(
                blank=True,
                help_text="YouTube channel or video URL.",
                max_length=512,
            ),
        ),
    ]
