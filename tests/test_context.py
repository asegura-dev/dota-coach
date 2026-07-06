"""Tests for voice preferences: default is to speak everything."""

from dota_coach.gamedata.context import should_speak


def test_unset_event_is_spoken_by_default() -> None:
    # With no preferences, every event is spoken.
    assert should_speak({}, "low_health") is True


def test_event_set_to_false_is_silenced() -> None:
    assert should_speak({"leveled_up": False}, "leveled_up") is False


def test_event_set_to_true_is_spoken() -> None:
    assert should_speak({"low_health": True}, "low_health") is True


def test_silencing_one_event_does_not_affect_others() -> None:
    prefs = {"leveled_up": False}
    # leveled_up is silenced, but low_health still defaults to spoken.
    assert should_speak(prefs, "leveled_up") is False
    assert should_speak(prefs, "low_health") is True