from sensor_simulator import generate as generate_module
from sensor_simulator.sensors import FEATURES


def test_csv_schema_includes_label(tmp_path, monkeypatch) -> None:
    path = tmp_path / "train.csv"
    monkeypatch.setattr(generate_module, "SENSOR_DATA_PATH", path)
    rows = generate_module.generate_rows(n_samples=40, seed=0)
    generate_module.write_csv(rows)
    text = path.read_text()
    header = text.splitlines()[0]
    assert header == ",".join(FEATURES) + ",is_anomaly"
    assert any("True" in line for line in text.splitlines()[1:])
    assert any("False" in line for line in text.splitlines()[1:])
