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
    artist_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Public artist / project name shown on smart links when set.",
    )
    instagram = models.CharField(
        max_length=512,
        blank=True,
        help_text="Instagram profile URL or handle.",
    )
    tiktok = models.CharField(
        max_length=512,
        blank=True,
        help_text="TikTok profile URL or @handle.",
    )
    youtube = models.CharField(
        max_length=512,
        blank=True,
        help_text="YouTube channel or video URL.",
    )

    class Meta:
        db_table = "users_user"
