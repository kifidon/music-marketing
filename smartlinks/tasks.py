from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def notify_fans_song_released(self, song_id: int) -> None:
    """
    Runs at ``Song.release_at``. Email every fan that this song is out.

    TODO: Implement email delivery (respect unsubscribes, template, fan query per song).
    """
    from smartlinks.models import Song

    try:
        Song.objects.get(pk=song_id)
    except Song.DoesNotExist:
        logger.warning("notify_fans_song_released: song id=%s missing", song_id)
        return
    # TODO: query fans for this song and send email.
    logger.info("notify_fans_song_released placeholder for song_id=%s", song_id)
    Song.objects.filter(pk=song_id).update(release_notification_task_id="")
