from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseServerError, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from .forms import FanOptInForm
from .models import (
    Fan,
    FanGateSubmission,
    LandingTemplate,
    LandingPageView,
    MusicPlatform,
    OutboundLinkClick,
    Song,
    SupabaseWatchdog,
)
from .session_utils import clear_fan_unlock_for_song, fan_id_for_song, set_fan_unlock_for_song

# Static paths under staticfiles (use with {% static %} on the landing template).
_LANDING_LOGO_BY_PLATFORM = {
    MusicPlatform.SPOTIFY.value: "smartlinks/logos/spotify.png",
    MusicPlatform.APPLE_MUSIC.value: "smartlinks/logos/apple_music.png",
    MusicPlatform.YOUTUBE.value: "smartlinks/logos/youtube.png",
    MusicPlatform.TIDAL.value: "smartlinks/logos/tidal.png",
    MusicPlatform.SOUNDCLOUD.value: "smartlinks/logos/soundcloud.png",
    MusicPlatform.BANDCAMP.value: None,
    MusicPlatform.AMAZON_MUSIC.value: "smartlinks/logos/amazon_music.png",
    MusicPlatform.DEEZER.value: "smartlinks/logos/deezer.png",
}


def _artist_display(song: Song) -> str:
    """Public name for minimal landing: owner.artist_name, else full name, else username."""
    o = song.owner
    if o is None:
        return ""
    if (getattr(o, "artist_name", "") or "").strip():
        return o.artist_name.strip()
    full = (o.get_full_name() or "").strip()
    return full or o.get_username()


def _owner_social_links(song: Song) -> list[dict]:
    """Instagram / TikTok / YouTube when the song owner saved full URLs on their profile."""
    o = song.owner
    if o is None:
        return []
    out: list[dict] = []
    pairs = (
        ("instagram", "Instagram", (o.instagram or "").strip()),
        ("tiktok", "TikTok", (o.tiktok or "").strip()),
        ("youtube", "YouTube", (o.youtube or "").strip()),
    )
    for key, label, url in pairs:
        if url:
            out.append({"key": key, "label": label, "url": url})
    return out


def _platform_rows(song: Song) -> list[dict]:
    return [
        {
            "platform": platform,
            "url": url,
            "logo": _LANDING_LOGO_BY_PLATFORM.get(platform.value),
        }
        for platform, url in song.platform_links()
    ]


def _log_landing_view(request, song: Song) -> None:
    if not request.session.session_key:
        request.session.save()
    LandingPageView.objects.create(
        song=song,
        session_key=request.session.session_key or "",
        referrer=(request.META.get("HTTP_REFERER") or "")[:512],
        user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:256],
    )


def _wants_json(request) -> bool:
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept


@ensure_csrf_cookie
@require_http_methods(["GET", "HEAD"])
def landing(request, slug: str):
    song = get_object_or_404(
        Song.objects.select_related("owner"),
        slug=slug,
        is_published=True,
    )
    reset_q = (request.GET.get("reset_gate") or "").strip()
    if reset_q:
        allow = False
        if settings.DEBUG and reset_q == "1":
            allow = True
        elif settings.SMARTLINKS_RESET_GATE_SECRET and reset_q == settings.SMARTLINKS_RESET_GATE_SECRET:
            allow = True
        if allow:
            clear_fan_unlock_for_song(request, song.id)
            return redirect("smartlinks:landing", slug=slug)
    _log_landing_view(request, song)
    template_name = (
        "smartlinks/landing_minimal.html"
        if song.landing_template == LandingTemplate.MINIMAL
        else "smartlinks/landing.html"
    )
    recent_releases = list(
        Song.objects.filter(is_published=True)
        .select_related("owner")
        .exclude(pk=song.pk)
        .order_by("-created_at")[:2]
    )
    return render(
        request,
        template_name,
        {
            "song": song,
            "artist_display": _artist_display(song),
            "owner_social_links": _owner_social_links(song),
            "platform_rows": _platform_rows(song),
            "gate_unlocked": bool(fan_id_for_song(request, song.id)),
            "recent_releases": recent_releases,
        },
    )


@require_http_methods(["GET", "POST", "HEAD"])
def go_platform(request, slug: str, platform: str):
    song = get_object_or_404(Song, slug=slug, is_published=True)
    if platform not in MusicPlatform.values:
        raise Http404("Unknown platform")
    dest = (song.url_for_platform(platform) or "").strip()
    if not dest:
        raise Http404("This platform is not linked for this song")

    fan_id = fan_id_for_song(request, song.id)
    if request.method == "POST":
        form = FanOptInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].strip().lower()
            FanGateSubmission.objects.create(song=song, email=email)
            fan, created = Fan.objects.get_or_create(
                email=email,
                defaults={
                    "name": form.cleaned_data["name"].strip(),
                    "preferred_platform": platform,
                    "first_song": song,
                },
            )
            if not created:
                Fan.objects.filter(pk=fan.pk).update(
                    name=form.cleaned_data["name"].strip(),
                    preferred_platform=platform,
                )
                fan.refresh_from_db()
            set_fan_unlock_for_song(request, song.id, fan.id)
            OutboundLinkClick.objects.create(song=song, fan=fan, platform=platform)
            if _wants_json(request):
                return JsonResponse({"ok": True, "redirect": dest})
            return HttpResponseRedirect(dest)
        if _wants_json(request):
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return render(
            request,
            "smartlinks/fan_gate.html",
            {
                "song": song,
                "platform": platform,
                "dest_label": dict(MusicPlatform.choices).get(platform, platform),
                "outbound_url": dest,
                "form": form,
            },
            status=400,
        )

    # GET
    if fan_id:
        fan = get_object_or_404(Fan, pk=fan_id)
        OutboundLinkClick.objects.create(song=song, fan=fan, platform=platform)
        return HttpResponseRedirect(dest)

    form = FanOptInForm()
    return render(
        request,
        "smartlinks/fan_gate.html",
        {
            "song": song,
            "platform": platform,
            "dest_label": dict(MusicPlatform.choices).get(platform, platform),
            "outbound_url": dest,
            "form": form,
        },
    )


@login_required
def dashboard(request):
    qs = (
        Song.objects.all()
        .annotate(
            view_count=Count("landing_views", distinct=False),
            click_count=Count("outbound_clicks", distinct=False),
            first_fan_count=Count("first_time_fans", distinct=True),
        )
        .order_by("-created_at")
    )
    return render(
        request,
        "smartlinks/dashboard.html",
        {"songs": qs},
    )


@require_GET
def pet_supabase(request):
    """
    Toggles ``SupabaseWatchdog`` row pk=1 (boolean + ``updated_at``). Intended for UptimeRobot:
    responds with plain ``ok`` and 200 on success, 500 on failure.
    """
    try:
        row, _ = SupabaseWatchdog.objects.get_or_create(pk=1, defaults={"flag": False})
        row.flag = not row.flag
        row.save()
    except Exception:
        return HttpResponseServerError("error", content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")


def home(request):
    if request.user.is_authenticated:
        return redirect("smartlinks:dashboard")
    return render(request, "smartlinks/home.html")
