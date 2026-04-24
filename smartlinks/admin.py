from django import forms
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html

from .distribution_import import apply_extracted_to_song, scrape_streaming_from_url
from .models import (
    Fan,
    FanGateSubmission,
    LandingPageView,
    OutboundLinkClick,
    Song,
)

_LONG_LINK_FIELDS = (
    "spotify_url",
    "apple_music_url",
    "youtube_url",
    "tidal_url",
    "soundcloud_url",
    "bandcamp_url",
    "amazon_music_url",
    "deezer_url",
    "distribution_source_url",
    "import_from_smart_link",
)


class SongAdminForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        wide = forms.TextInput(
            attrs={
                "style": "width:100%;max-width:100%;box-sizing:border-box;",
                "spellcheck": "false",
                "autocomplete": "off",
            }
        )
        for name in _LONG_LINK_FIELDS:
            if name in self.fields:
                self.fields[name].widget = wide


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    form = SongAdminForm
    list_display = (
        "title",
        "slug",
        "accent_color",
        "is_published",
        "link_count",
        "view_count",
        "click_count",
        "first_fans",
        "landing_link",
        "created_at",
    )
    list_filter = ("is_published",)
    search_fields = ("title", "slug")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "preview_link_display")
    fieldsets = (
        (None, {"fields": ("title", "slug", "cover_art", "accent_color", "is_published")}),
        (
            "Import from distro / presave page",
            {
                "description": "Paste a one-off smart link (e.g. Toolost). On save we fetch the page "
                "and fill the streaming URL fields below. Cleared after a successful import.",
                "fields": ("import_from_smart_link", "distribution_source_url"),
            },
        ),
        ("Streaming links", {"fields": (
            "spotify_url",
            "apple_music_url",
            "youtube_url",
            "tidal_url",
            "soundcloud_url",
            "bandcamp_url",
            "amazon_music_url",
            "deezer_url",
        )}),
        ("Meta", {"fields": ("preview_link_display", "created_at", "updated_at")}),
    )

    @admin.display(description="Platforms")
    def link_count(self, obj: Song):
        return len(obj.platform_links())

    @admin.display(description="Views")
    def view_count(self, obj: Song):
        return obj.landing_views.count()

    @admin.display(description="Clicks")
    def click_count(self, obj: Song):
        return obj.outbound_clicks.count()

    @admin.display(description="First-time fans")
    def first_fans(self, obj: Song):
        return obj.first_time_fans.count()

    @admin.display(description="Public URL")
    def landing_link(self, obj: Song):
        url = reverse("smartlinks:landing", kwargs={"slug": obj.slug})
        return format_html('<a href="{}" target="_blank">Open</a>', url)

    @admin.display(description="Landing page preview")
    def preview_link_display(self, obj: Song):
        if not obj.pk:
            return "—"
        url = reverse("smartlinks:landing", kwargs={"slug": obj.slug})
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    def save_model(self, request, obj, form, change):
        import_url = (obj.import_from_smart_link or "").strip()
        if import_url:
            try:
                extracted = scrape_streaming_from_url(import_url)
            except Exception as exc:
                self.message_user(
                    request,
                    f"Could not fetch or read that page: {exc}",
                    level=messages.ERROR,
                )
                return super().save_model(request, obj, form, change)
            if not extracted:
                self.message_user(
                    request,
                    "No known streaming store links were found in the HTML. "
                    "You can still paste URLs manually.",
                    level=messages.WARNING,
                )
                return super().save_model(request, obj, form, change)
            applied = apply_extracted_to_song(obj, extracted, overwrite=True)
            obj.distribution_source_url = import_url[:2048]
            obj.import_from_smart_link = ""
            self.message_user(
                request,
                "Imported links: " + ", ".join(applied),
                level=messages.SUCCESS,
            )
        super().save_model(request, obj, form, change)


@admin.register(Fan)
class FanAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "preferred_platform", "first_song", "created_at")
    list_filter = ("preferred_platform",)
    search_fields = ("email", "name")
    readonly_fields = ("created_at",)


@admin.register(LandingPageView)
class LandingPageViewAdmin(admin.ModelAdmin):
    list_display = ("song", "session_key", "created_at", "referrer_short")
    list_filter = ("song",)
    date_hierarchy = "created_at"
    readonly_fields = ("song", "session_key", "referrer", "user_agent", "created_at")

    @admin.display(description="Referrer")
    def referrer_short(self, obj):
        return (obj.referrer[:80] + "…") if len(obj.referrer) > 80 else obj.referrer


@admin.register(OutboundLinkClick)
class OutboundLinkClickAdmin(admin.ModelAdmin):
    list_display = ("song", "fan", "platform", "created_at")
    list_filter = ("platform", "song")
    date_hierarchy = "created_at"
    readonly_fields = ("song", "fan", "platform", "created_at")


@admin.register(FanGateSubmission)
class FanGateSubmissionAdmin(admin.ModelAdmin):
    list_display = ("song", "email", "created_at")
    list_filter = ("song",)
    date_hierarchy = "created_at"
    readonly_fields = ("song", "email", "created_at")
