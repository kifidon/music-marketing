import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("smartlinks", "0009_supabase_watchdog"),
    ]

    operations = [
        migrations.AddField(
            model_name="song",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                help_text="Account whose artist name and social links appear on this landing page.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="songs",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
