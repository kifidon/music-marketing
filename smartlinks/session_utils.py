UNLOCKS_KEY = "smartlinks_unlock_fan_by_song"


def fan_id_for_song(request, song_id: int) -> int | None:
    raw = request.session.get(UNLOCKS_KEY, {})
    val = raw.get(str(song_id))
    return int(val) if val is not None else None


def set_fan_unlock_for_song(request, song_id: int, fan_id: int) -> None:
    data = dict(request.session.get(UNLOCKS_KEY, {}))
    data[str(song_id)] = fan_id
    request.session[UNLOCKS_KEY] = data
    request.session.modified = True


def clear_fan_unlock_for_song(request, song_id: int) -> None:
    """Remove gate-unlock for one song (e.g. testing the email modal again)."""
    data = dict(request.session.get(UNLOCKS_KEY, {}))
    data.pop(str(song_id), None)
    request.session[UNLOCKS_KEY] = data
    request.session.modified = True
