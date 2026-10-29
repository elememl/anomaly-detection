import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard import config

APP_PATH = str(Path(__file__).resolve().parent.parent / "dashboard" / "app.py")


def _line(index: int, is_anomaly: bool | None) -> str:
    return json.dumps(
        {
            "timestamp": f"2026-08-22T10:00:{index:02d}+00:00",
            "injected_fault": bool(is_anomaly),
            "fault_mode": "overheat" if is_anomaly else None,
            "scored": is_anomaly is not None,
            "anomaly_score": None if is_anomaly is None else (0.7 if is_anomaly else 0.3),
            "is_anomaly": is_anomaly,
            "error": None if is_anomaly is not None else "Connection refused",
            "temperature": 34.0 if is_anomaly else 22.0,
            "humidity": 45.0,
            "sound_volume": 60.0,
        }
    )


@pytest.fixture()
def log_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "stream_log.jsonl"
    monkeypatch.setattr(config, "DASHBOARD_LOG_PATH", path)
    return path


def test_app_renders_charts_and_metrics(log_path) -> None:
    log_path.write_text("\n".join(_line(i, i % 4 == 0) for i in range(8)) + "\n")
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert app.metric[0].value == "8"
    assert app.metric[1].value == "2"
    assert app.metric[2].value == "25.0%"
    assert not app.warning


def test_unscored_items_raise_a_warning(log_path) -> None:
    lines = [_line(0, False), _line(1, True), _line(2, None), _line(3, None)]
    log_path.write_text("\n".join(lines) + "\n")
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert app.metric[0].value == "4"
    # Rate counts scored items only: one anomaly out of two scored.
    assert app.metric[2].value == "50.0%"
    assert "2 of the last 4 items are unscored" in app.warning[0].value


def test_all_unscored_shows_no_rate(log_path) -> None:
    log_path.write_text("\n".join(_line(i, None) for i in range(3)) + "\n")
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert app.metric[2].value == "n/a"


def test_app_waits_when_no_events(log_path) -> None:
    app = AppTest.from_file(APP_PATH).run()
    assert not app.exception
    assert "Waiting for stream events" in app.info[0].value
