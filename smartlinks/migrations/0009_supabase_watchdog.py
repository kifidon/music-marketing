from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("smartlinks", "0008_song_landing_template"),
    ]

    operations = [
        migrations.CreateModel(
            name="SupabaseWatchdog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("flag", models.BooleanField(default=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Supabase watchdog",
                "db_table": "supabase_watchdog",
            },
        ),
    ]
