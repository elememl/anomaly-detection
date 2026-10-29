import random

import joblib
import pytest
from flask.testing import FlaskClient

from anomaly_detection import app as app_module
from anomaly_detection.config import FEATURES
from anomaly_detection.train import fit_model

INLIER = {name: 0.0 for name in FEATURES}
FAR_OUTLIER = {name: 50.0 for name in FEATURES}


def _inlier_rows() -> list[dict[str, object]]:
    rng = random.Random(0)
    rows: list[dict[str, object]] = []
    for _ in range(500):
        rows.append(
            {
                "temperature": rng.gauss(0.0, 0.1),
                "humidity": rng.gauss(0.0, 0.1),
                "sound_volume": rng.gauss(0.0, 0.1),
                "is_anomaly": False,
            }
        )
    return rows


@pytest.fixture()
def trained_client(tmp_path, monkeypatch: pytest.MonkeyPatch) -> FlaskClient:
    model = fit_model(_inlier_rows())
    model_path = tmp_path / "model.joblib"
    joblib.dump(model, model_path)
    monkeypatch.setattr(app_module, "ANOMALY_MODEL_PATH", model_path)
    monkeypatch.setattr(app_module, "_model", None)
    monkeypatch.setattr(app_module, "_request_count", 0)
    monkeypatch.setattr(app_module, "_predict_count", 0)
    monkeypatch.setattr(app_module, "_anomaly_count", 0)
    return app_module.app.test_client()


def test_health_ok(trained_client: FlaskClient) -> None:
    response = trained_client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_inlier_is_not_anomaly(trained_client: FlaskClient) -> None:
    response = trained_client.post("/predict", json=INLIER)
    body = response.get_json()
    assert response.status_code == 200
    assert body["is_anomaly"] is False


def test_far_point_is_anomaly(trained_client: FlaskClient) -> None:
    response = trained_client.post("/predict", json=FAR_OUTLIER)
    body = response.get_json()
    assert response.status_code == 200
    assert body["is_anomaly"] is True


def test_missing_field_is_400(trained_client: FlaskClient) -> None:
    response = trained_client.post("/predict", json={"temperature": 0.0, "humidity": 0.0})
    assert response.status_code == 400
    assert "sound_volume" in response.get_json()["error"]


def test_non_numeric_field_is_400(trained_client: FlaskClient) -> None:
    response = trained_client.post(
        "/predict",
        json={"temperature": "hot", "humidity": 0.0, "sound_volume": 0.0},
    )
    assert response.status_code == 400
    assert "temperature" in response.get_json()["error"]


def test_metrics_count_predict(trained_client: FlaskClient) -> None:
    trained_client.post("/predict", json=INLIER)
    body = trained_client.get("/metrics").get_json()
    assert body["predict_count"] == 1
    assert body["request_count"] == 1
