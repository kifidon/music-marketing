"""``upload_to`` callables for ``FileField`` / ``ImageField``."""

from __future__ import annotations

from pathlib import Path

from django.utils.text import slugify


def song_cover_upload_to(instance, filename: str) -> str:
    """
    Supabase S3 key layout: ``{user_id}/coverart/{slug}-coverart.{ext}``.

    Uses ``owner_id`` when set; otherwise ``unassigned``. Slug comes from the instance
    (set in ``Song.save()`` before the DB write when title-only).
    """
    ext = Path(filename).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"):
        ext = ".jpg"
    uid = getattr(instance, "owner_id", None) or "unassigned"
    slug = (getattr(instance, "slug", None) or "").strip()
    if not slug:
        slug = slugify(getattr(instance, "title", None) or "") or "cover"
    return f"{uid}/coverart/{slug}-coverart{ext}"
