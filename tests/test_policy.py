from datetime import datetime
from zoneinfo import ZoneInfo

from kinwatch.models import Policy
from kinwatch.policy import in_quiet_hours


def test_quiet_hours_overnight_window():
    policy = Policy(quiet_hours_start="21:00", quiet_hours_end="07:00")
    night = datetime(2026, 10, 12, 2, 11, tzinfo=ZoneInfo("America/Los_Angeles"))
    noon = datetime(2026, 10, 12, 12, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
    assert in_quiet_hours(policy, night, "America/Los_Angeles")
    assert not in_quiet_hours(policy, noon, "America/Los_Angeles")
