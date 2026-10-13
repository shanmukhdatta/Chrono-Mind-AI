"""Calendar and PATCH parity with CREATE."""
import pytest
from pydantic import ValidationError
from models.task import TaskCreate, TaskUpdate


def payload(**changes):
    value = {"title": "Read", "date": "2026-10-13",
             "start_time": "09:00", "end_time": "10:00"}
    value.update(changes)
    return value


@pytest.mark.parametrize("day", ["2026-02-30", "2026-13-01", "2026-2-3"])
def test_impossible_or_noncanonical_dates_rejected(day):
    with pytest.raises(ValidationError):
        TaskCreate(**payload(date=day))


@pytest.mark.parametrize("updates", [
    {"date": "2026-02-30"}, {"start_time": "25:00"},
    {"end_time": "12:99"}, {"importance": "root"},
    {"recurrence": "yesterday"}, {"title": " "},
    {"unrecognized": "value"}
])
def test_patch_rejects_invalid_fields(updates):
    with pytest.raises(ValidationError):
        TaskUpdate(**updates)


def test_short_task_rejected():
    with pytest.raises(ValidationError):
        TaskCreate(**payload(start_time="09:00", end_time="09:14"))


def test_valid_weekday_repeat_is_normalized():
    assert TaskCreate(**payload(recurrence="MON, Wed")).recurrence == "mon,wed"
