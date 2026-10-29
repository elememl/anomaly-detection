import json
import urllib.error

from sensor_simulator import simulator as simulator_module
from sensor_simulator.sensors import FEATURES

READING = {"temperature": 22.0, "humidity": 45.0, "sound_volume": 60.0}
RESULT = {"anomaly_score": 0.42, "is_anomaly": True}


def test_event_carries_truth_and_verdict() -> None:
    event = simulator_module.build_event(READING, True, "moisture", RESULT)
    assert event["injected_fault"] is True
    assert event["fault_mode"] == "moisture"
    assert event["scored"] is True
    assert event["is_anomaly"] is True
    assert event["anomaly_score"] == 0.42
    assert event["error"] is None
    for name in FEATURES:
        assert event[name] == READING[name]


def test_unscored_event_keeps_reading_and_truth() -> None:
    event = simulator_module.build_event(READING, True, "overheat", None, "connection refused")
    assert event["scored"] is False
    assert event["anomaly_score"] is None
    assert event["is_anomaly"] is None
    assert event["error"] == "connection refused"
    assert event["injected_fault"] is True
    for name in FEATURES:
        assert event[name] == READING[name]


def test_append_writes_one_json_line(tmp_path, monkeypatch) -> None:
    path = tmp_path / "stream_log.jsonl"
    monkeypatch.setattr(simulator_module, "SENSOR_LOG_PATH", path)
    simulator_module.append_event(simulator_module.build_event(READING, False, None, RESULT))
    simulator_module.append_event(simulator_module.build_event(READING, False, None, RESULT))
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["fault_mode"] is None


def test_stream_records_items_while_api_is_down(tmp_path, monkeypatch) -> None:
    path = tmp_path / "stream_log.jsonl"
    monkeypatch.setattr(simulator_module, "SENSOR_LOG_PATH", path)
    monkeypatch.setattr(simulator_module, "SENSOR_INTERVAL_SECONDS", 0)

    def refuse(reading: dict) -> dict:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(simulator_module, "post_reading", refuse)

    ticks = {"n": 0}

    def stop_after_three(_seconds: float) -> None:
        ticks["n"] += 1
        if ticks["n"] >= 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(simulator_module.time, "sleep", stop_after_three)
    try:
        simulator_module.run_forever()
    except KeyboardInterrupt:
        pass

    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(events) == 3
    assert all(event["scored"] is False for event in events)
    assert all(event["anomaly_score"] is None for event in events)
    assert all("Connection refused" in event["error"] for event in events)
