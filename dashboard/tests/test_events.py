import json

import pytest

from dashboard.events import ANOMALY, NORMAL, SENSORS, UNSCORED, read_events, sensor_series, status_of, time_x


def test_time_axis_is_hour_minute_with_few_ticks() -> None:
    axis = time_x().to_dict()["axis"]
    assert axis["format"] == "%H:%M:%S"
    assert axis["tickCount"] == 5


def _event(index: int, is_anomaly: bool | None) -> dict:
    return {
        "timestamp": f"2026-08-22T10:00:{index:02d}+00:00",
        "injected_fault": bool(is_anomaly),
        "fault_mode": "moisture" if is_anomaly else None,
        "scored": is_anomaly is not None,
        "anomaly_score": None if is_anomaly is None else (0.6 if is_anomaly else 0.3),
        "is_anomaly": is_anomaly,
        "error": None if is_anomaly is not None else "Connection refused",
        "temperature": 22.0,
        "humidity": 90.0 if is_anomaly else 45.0,
        "sound_volume": 60.0,
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [(True, ANOMALY), (False, NORMAL), (None, UNSCORED)],
)
def test_status_mapping(value: bool | None, expected: str) -> None:
    assert status_of(value) == expected


def test_missing_file_gives_empty_frame(tmp_path) -> None:
    frame = read_events(tmp_path / "absent.jsonl", window=10)
    assert frame.empty


def test_window_keeps_latest_events(tmp_path) -> None:
    path = tmp_path / "stream_log.jsonl"
    path.write_text("".join(json.dumps(_event(i, i % 5 == 0)) + "\n" for i in range(20)))
    frame = read_events(path, window=5)
    assert len(frame) == 5
    assert frame["timestamp"].is_monotonic_increasing
    assert int((frame["status"] == ANOMALY).sum()) == 1


def test_unscored_events_get_status(tmp_path) -> None:
    path = tmp_path / "stream_log.jsonl"
    path.write_text(json.dumps(_event(0, None)) + "\n" + json.dumps(_event(1, True)) + "\n")
    frame = read_events(path, window=10)
    assert list(frame["status"]) == [UNSCORED, ANOMALY]


def test_partial_trailing_line_is_ignored(tmp_path) -> None:
    path = tmp_path / "stream_log.jsonl"
    path.write_text(json.dumps(_event(0, False)) + "\n" + '{"timestamp": "2026')
    frame = read_events(path, window=10)
    assert len(frame) == 1


def test_sensor_series_is_long_form(tmp_path) -> None:
    path = tmp_path / "stream_log.jsonl"
    path.write_text(json.dumps(_event(0, True)) + "\n")
    long_frame = sensor_series(read_events(path, window=10))
    assert len(long_frame) == len(SENSORS)
    assert set(long_frame["sensor"]) == set(SENSORS)
    assert set(long_frame["status"]) == {ANOMALY}
