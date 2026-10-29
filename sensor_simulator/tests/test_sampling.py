import random

import pytest

from sensor_simulator.sensors import FAULT_MODES, FAULT_RATE, FEATURES, apply_fault, sample_stream_item


def test_payload_has_three_features() -> None:
    rng = random.Random(0)
    reading, _injected, _mode = sample_stream_item(rng)
    assert tuple(reading.keys()) == FEATURES
    for name in FEATURES:
        assert isinstance(reading[name], float)


def test_payload_has_no_label() -> None:
    rng = random.Random(1)
    reading, _injected, _mode = sample_stream_item(rng)
    assert "is_anomaly" not in reading


def test_unknown_fault_mode_raises() -> None:
    with pytest.raises(ValueError, match="spark"):
        apply_fault({"temperature": 22.0, "humidity": 45.0, "sound_volume": 60.0}, "spark")


def test_fault_rate_wiring() -> None:
    rng = random.Random(0)
    n = 4000
    injected = 0
    modes: set[str] = set()
    for _ in range(n):
        _reading, is_fault, mode = sample_stream_item(rng)
        if is_fault:
            injected += 1
            assert mode in FAULT_MODES
            modes.add(mode)
        else:
            assert mode is None
    rate = injected / n
    assert abs(rate - FAULT_RATE) < 0.02
    assert modes == set(FAULT_MODES)
