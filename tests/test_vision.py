from kinwatch.names import public_name, strip_ids
from kinwatch.vision import fixture_classify
from kinwatch.ring.fixtures import fixture_snapshot, FRONT_DOOR_ID


def test_never_display_device_ids():
    assert public_name("ava1.ring.device.FRONTDOOR") == "the door"
    assert "ava1.ring" not in strip_ids("camera ava1.ring.device.X fired")


def test_vision_on_privacy_safe_snapshot():
    snap = fixture_snapshot(FRONT_DOOR_ID)
    assert snap.privacy_zones_applied
    result = fixture_classify(snap)
    assert result.kind == "empty"
    assert "lock" not in result.summary.lower()
