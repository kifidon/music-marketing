from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from smartlinks.upload_paths import song_cover_upload_to


class MusicPlatform(models.TextChoices):
    SPOTIFY = "spotify", "Spotify"
    APPLE_MUSIC = "apple_music", "Apple Music"
    YOUTUBE = "youtube", "YouTube"
    TIDAL = "tidal", "Tidal"
    SOUNDCLOUD = "soundcloud", "SoundCloud"
    BANDCAMP = "bandcamp", "Bandcamp"
    AMAZON_MUSIC = "amazon_music", "Amazon Music"
    DEEZER = "deezer", "Deezer"


class LandingTemplate(models.TextChoices):
    MODERN = "modern", "Modern"
    MINIMAL = "minimal", "Minimal"


class Song(models.Model):
    """One smart-link landing page per song."""

    title = models.CharField(max_length=255)
    description = models.TextField(
        blank=True,
        help_text="Optional. Shown on the minimal landing template under the artist line.",
    )
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    cover_art = models.ImageField(
        upload_to=song_cover_upload_to,
        max_length=512,
        help_text="Stored under your account in S3 when configured (see AWS_* env vars).",
    )
    accent_color = models.CharField(
        max_length=7,
        default="#6366f1",
        help_text="Hex color for the landing template (e.g. #7c3aed).",
    )
    landing_template = models.CharField(
        max_length=16,
        choices=LandingTemplate.choices,
        default=LandingTemplate.MODERN,
        help_text="Choose which smart-link layout to render for this song.",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="songs",
        help_text="Account whose artist name and social links appear on this landing page.",
    )

    # TextField (not URLField): distro smart links can exceed URLField limits and the admin
    # URLInput adds maxlength; TEXT stores the full string in Postgres/SQLite.
    _link = {"blank": True}
    spotify_url = models.TextField(
        **_link,
        help_text="Spotify presave / listen link — e.g. Toolost or Feature.fm smart URL "
        "(api.ffm.to/…), or open.spotify.com / spotify.link when you have them.",
    )
    apple_music_url = models.TextField(**_link)
    youtube_url = models.TextField(**_link)
    tidal_url = models.TextField(**_link)
    soundcloud_url = models.TextField(**_link)
    bandcamp_url = models.TextField(**_link)
    amazon_music_url = models.TextField(**_link)
    deezer_url = models.TextField(**_link)

    distribution_source_url = models.TextField(
        **_link,
        help_text="Last smart-link / distro page you imported from (set automatically).",
    )
    import_from_smart_link = models.TextField(
        **_link,
        help_text="One-time: paste a distro / presave smart link, save the song, and we "
        "pull streaming URLs from that page into the fields above (then clear this).",
    )

    is_published = models.BooleanField(default=True)

    release_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="UTC instant when the track is “out” (for display / future use).",
    )
    release_timezone = models.CharField(
        max_length=64,
        default="UTC",
        help_text="IANA zone for how the release time was chosen (for future email copy).",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "songs"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "song"
            slug = base
            n = 0
            while Song.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("smartlinks:landing", kwargs={"slug": self.slug})

    def platform_links(self):
        """List of (MusicPlatform, url) for platforms that have a URL."""
        fields = [
            (MusicPlatform.SPOTIFY, self.spotify_url),
            (MusicPlatform.APPLE_MUSIC, self.apple_music_url),
            (MusicPlatform.YOUTUBE, self.youtube_url),
            (MusicPlatform.TIDAL, self.tidal_url),
            (MusicPlatform.SOUNDCLOUD, self.soundcloud_url),
            (MusicPlatform.BANDCAMP, self.bandcamp_url),
            (MusicPlatform.AMAZON_MUSIC, self.amazon_music_url),
            (MusicPlatform.DEEZER, self.deezer_url),
        ]
        return [(p, u.strip()) for p, u in fields if (u or "").strip()]

    def url_for_platform(self, platform: str) -> str | None:
        mapping = {
            MusicPlatform.SPOTIFY: self.spotify_url,
            MusicPlatform.APPLE_MUSIC: self.apple_music_url,
            MusicPlatform.YOUTUBE: self.youtube_url,
            MusicPlatform.TIDAL: self.tidal_url,
            MusicPlatform.SOUNDCLOUD: self.soundcloud_url,
            MusicPlatform.BANDCAMP: self.bandcamp_url,
            MusicPlatform.AMAZON_MUSIC: self.amazon_music_url,
            MusicPlatform.DEEZER: self.deezer_url,
        }
        raw = mapping.get(platform) or ""
        raw = raw.strip()
        return raw or None


class Fan(models.Model):
    """Opted-in listener; unique email. first_song is the song they first Forever Saved on."""

    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=255)
    preferred_platform = models.CharField(
        max_length=32,
        choices=MusicPlatform.choices,
    )
    first_song = models.ForeignKey(
        Song,
        on_delete=models.PROTECT,
        related_name="first_time_fans",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "fans"

    def __str__(self):
        return self.email


class LandingPageView(models.Model):
    """Raw landing loads for open rate / traffic."""

    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="landing_views")
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    referrer = models.CharField(max_length=512, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_landing_page_views"
        indexes = [
            models.Index(fields=["song", "created_at"]),
        ]


class OutboundLinkClick(models.Model):
    """Click through to a streaming platform (after unlock)."""

    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="outbound_clicks")
    fan = models.ForeignKey(Fan, on_delete=models.CASCADE, related_name="outbound_clicks")
    platform = models.CharField(max_length=32, choices=MusicPlatform.choices)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_outbound_link_clicks"
        indexes = [
            models.Index(fields=["song", "created_at"]),
            models.Index(fields=["song", "platform"]),
        ]


class FanGateSubmission(models.Model):
    """Optional: record each gate submit (fan may already exist — email unique updates)."""

    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="gate_submissions")
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_fan_gate_submissions"
        indexes = [models.Index(fields=["song", "created_at"])]


class SupabaseWatchdog(models.Model):
    """
    Singleton-style row (``pk=1``) toggled by ``GET /pet-supabase/`` so an external pinger
    can keep the Supabase project from idling.
    """

    flag = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "supabase_watchdog"
        verbose_name = "Supabase watchdog"

    def __str__(self):
        return f"SupabaseWatchdog(flag={self.flag})"
