from __future__ import annotations

from celery.result import AsyncResult
from django.utils import timezone as dj_tz

from config.celery import app as celery_app


def reschedule_release_notification(
    song,
    previous_release_at,
    previous_task_id: str | None,
) -> None:
    """
    After a Song is saved, (re)schedule or cancel the fan “song is out” notification task.
    Persists ``release_notification_task_id`` via queryset.update to avoid recursive saves.
    """
    from smartlinks.models import Song
    from smartlinks.tasks import notify_fans_song_released

    new_utc = song.release_at
    prev_tid = (previous_task_id or "").strip() or None

    def revoke_if_needed() -> None:
        if prev_tid:
            AsyncResult(prev_tid, app=celery_app).revoke(terminate=False)

    if new_utc is None:
        revoke_if_needed()
        Song.objects.filter(pk=song.pk).update(release_notification_task_id="")
        song.release_notification_task_id = ""
        return

    now = dj_tz.now()
    if new_utc <= now:
        revoke_if_needed()
        Song.objects.filter(pk=song.pk).update(release_notification_task_id="")
        song.release_notification_task_id = ""
        return

    if new_utc == previous_release_at and prev_tid:
        return

    revoke_if_needed()
    async_result = notify_fans_song_released.apply_async(args=[song.pk], eta=new_utc)
    Song.objects.filter(pk=song.pk).update(release_notification_task_id=async_result.id)
    song.release_notification_task_id = async_result.id
