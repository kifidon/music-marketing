from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Project user model. Add fields here as needed; keep AUTH_USER_MODEL = "users.User"
    in settings and reference users via django.contrib.auth.get_user_model().
    """

    timezone = models.CharField(
        max_length=64,
        default="UTC",
        help_text="IANA zone (e.g. America/Los_Angeles). Used when setting a song’s local release time in admin.",
    )

    class Meta:
        db_table = "users_user"
