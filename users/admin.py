from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    search_fields = ("username", "email", "first_name", "last_name", "artist_name")

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Regional", {"fields": ("timezone",)}),
        (
            "Artist profile",
            {"fields": ("artist_name", "instagram", "tiktok", "youtube")},
        ),
    )
