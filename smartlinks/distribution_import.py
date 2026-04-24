"""
One-time fetch of a distro / presave smart-link page and extraction of streaming URLs.

Best-effort: parses anchor tags and raw HTML for known host patterns. No ongoing sync.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .models import MusicPlatform

# (MusicPlatform value string, host substrings that identify this platform)
_HOST_RULES: list[tuple[str, tuple[str, ...]]] = [
    (MusicPlatform.SPOTIFY.value, ("open.spotify.com", "spotify.link", "spotify.com")),
    (MusicPlatform.APPLE_MUSIC.value, ("music.apple.com", "itunes.apple.com")),
    (MusicPlatform.YOUTUBE.value, ("youtube.com", "youtu.be", "music.youtube.com")),
    (MusicPlatform.TIDAL.value, ("tidal.com", "listen.tidal.com")),
    (MusicPlatform.SOUNDCLOUD.value, ("soundcloud.com",)),
    (MusicPlatform.BANDCAMP.value, ("bandcamp.com",)),
    (
        MusicPlatform.AMAZON_MUSIC.value,
        ("music.amazon.", "amazon.com/music", "a.co"),
    ),
    (MusicPlatform.DEEZER.value, ("deezer.com", "dzr.fm")),
]

_FIELD_NAMES: dict[str, str] = {
    MusicPlatform.SPOTIFY.value: "spotify_url",
    MusicPlatform.APPLE_MUSIC.value: "apple_music_url",
    MusicPlatform.YOUTUBE.value: "youtube_url",
    MusicPlatform.TIDAL.value: "tidal_url",
    MusicPlatform.SOUNDCLOUD.value: "soundcloud_url",
    MusicPlatform.BANDCAMP.value: "bandcamp_url",
    MusicPlatform.AMAZON_MUSIC.value: "amazon_music_url",
    MusicPlatform.DEEZER.value: "deezer_url",
}

_URL_IN_TEXT_RE = re.compile(
    r"https?://[^\s\"'<>\\]+",
    re.IGNORECASE,
)


def _normalize_url(url: str, base: str) -> str | None:
    url = (url or "").strip()
    if not url or url.startswith(("javascript:", "mailto:", "tel:")):
        return None
    joined = urljoin(base, url)
    parsed = urlparse(joined)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    # Trim common trailing junk from regex captures
    joined = joined.rstrip(").,]}>'\"")
    if len(joined) > 2048:
        return None
    return joined


def _classify_url(url: str) -> str | None:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    for platform, fragments in _HOST_RULES:
        if any(fr in host for fr in fragments):
            return platform
    return None


def _collect_hrefs(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[str] = []
    for tag in soup.find_all(["a", "link", "area"]):
        href = tag.get("href")
        if href:
            n = _normalize_url(href, page_url)
            if n:
                out.append(n)
        for attr in ("data-href", "data-url", "data-link", "data-store"):
            v = tag.get(attr)
            if v:
                n = _normalize_url(v, page_url)
                if n:
                    out.append(n)
    return out


def _collect_regex_urls(html: str, page_url: str) -> list[str]:
    out: list[str] = []
    for m in _URL_IN_TEXT_RE.finditer(html):
        n = _normalize_url(m.group(0), page_url)
        if n:
            out.append(n)
    return out


def extract_streaming_urls(html: str, page_url: str) -> dict[str, str]:
    """Return map MusicPlatform value -> first canonical URL found per platform."""
    candidates = _collect_hrefs(html, page_url) + _collect_regex_urls(html, page_url)
    seen: dict[str, str] = {}
    for url in candidates:
        plat = _classify_url(url)
        if plat and plat not in seen:
            seen[plat] = url
    return seen


def scrape_streaming_from_url(page_url: str, timeout: int = 20) -> dict[str, str]:
    """
    GET page_url (follow redirects), return platform -> url for known stores.
    Raises requests.RequestException on network errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; MusicMarketingBot/1.0; +personal import; "
            "requests + BeautifulSoup)"
        ),
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(
        page_url,
        headers=headers,
        timeout=timeout,
        allow_redirects=True,
    )
    resp.raise_for_status()
    final_url = str(resp.url)
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if "html" not in ctype and "text/" not in ctype:
        raise ValueError(f"Unexpected content type: {ctype or 'unknown'}")
    text = resp.text
    if not text.strip():
        raise ValueError("Empty response body")
    return extract_streaming_urls(text, final_url)


def apply_extracted_to_song(song, extracted: dict[str, str], *, overwrite: bool = True) -> list[str]:
    """
    Set URL fields on song from extracted map. If overwrite is False, only set blank fields.
    Returns list of platform labels that were applied.
    """
    applied: list[str] = []
    for plat, url in extracted.items():
        field = _FIELD_NAMES.get(plat)
        if not field:
            continue
        current = getattr(song, field, "") or ""
        if not overwrite and current:
            continue
        setattr(song, field, url)
        try:
            applied.append(MusicPlatform(plat).label)
        except ValueError:
            applied.append(plat)
    return applied
