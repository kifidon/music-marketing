from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from smartlinks.models import Song


@receiver(pre_save, sender=Song)
def song_track_previous_release_schedule(sender, instance, **kwargs):
    if not instance.pk:
        instance._prev_release_at = None
        instance._prev_task_id = None
        return
    row = (
        Song.objects.filter(pk=instance.pk)
        .values_list("release_at", "release_notification_task_id")
        .first()
    )
    if not row:
        instance._prev_release_at = None
        instance._prev_task_id = None
        return
    instance._prev_release_at, tid = row[0], (row[1] or "").strip()
    instance._prev_task_id = tid or None


@receiver(post_save, sender=Song)
def song_reschedule_release_notification(sender, instance, **kwargs):
    uf = kwargs.get("update_fields")
    if uf is not None and set(uf) <= {"release_notification_task_id"}:
        return
    from smartlinks.release_schedule import reschedule_release_notification

    reschedule_release_notification(
        instance,
        getattr(instance, "_prev_release_at", None),
        getattr(instance, "_prev_task_id", None),
    )
