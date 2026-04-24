from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="timezone",
            field=models.CharField(
                default="UTC",
                help_text="IANA zone (e.g. America/Los_Angeles). Used when setting a song’s local release time in admin.",
                max_length=64,
            ),
        ),
    ]
