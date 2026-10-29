import logging
import time
from collections import deque
from typing import Any

import joblib
import numpy as np
from flask import Flask, jsonify, request
from sklearn.ensemble import IsolationForest

from anomaly_detection.config import ANOMALY_LOG_LEVEL, ANOMALY_MODEL_PATH, FEATURES

LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

_model: IsolationForest | None = None
_request_count = 0
_predict_count = 0
_anomaly_count = 0
_last_latency_ms = 0.0
_last_scores: deque[float] = deque(maxlen=20)


def configure_logging() -> None:
    """Send worker logs to stdout; gunicorn does not configure the root logger."""
    logging.basicConfig(level=ANOMALY_LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def load_model() -> IsolationForest:
    """Load the IsolationForest from disk."""
    if not ANOMALY_MODEL_PATH.is_file():
        raise FileNotFoundError(f"model file not found: {ANOMALY_MODEL_PATH}")
    loaded = joblib.load(ANOMALY_MODEL_PATH)
    if not isinstance(loaded, IsolationForest):
        raise TypeError(f"expected IsolationForest, got {type(loaded)!r}")
    return loaded


def get_model() -> IsolationForest:
    """Return the process-local model, loading it once."""
    global _model
    if _model is None:
        _model = load_model()
        LOGGER.info("model loaded from %s", ANOMALY_MODEL_PATH)
    return _model


def reading_from_payload(payload: object) -> dict[str, float]:
    """Validate a JSON object into the three sensor features."""
    if not isinstance(payload, dict):
        raise ValueError(f"payload must be a JSON object, got {payload!r}")
    reading: dict[str, float] = {}
    for name in FEATURES:
        if name not in payload:
            raise ValueError(f"missing field: {name!r}")
        raw = payload[name]
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"field {name!r} must be numeric, got {raw!r}") from exc
        if value != value:
            raise ValueError(f"field {name!r} must be numeric, got {raw!r}")
        reading[name] = value
    return reading


def score_reading(model: IsolationForest, reading: dict[str, float]) -> dict[str, Any]:
    """Return anomaly_score (higher = more anomalous) and IsolationForest's outlier flag."""
    matrix = np.array([[reading[name] for name in FEATURES]], dtype=float)
    raw_score = float(model.score_samples(matrix)[0])
    prediction = int(model.predict(matrix)[0])
    return {
        "anomaly_score": -raw_score,
        "is_anomaly": prediction == -1,
    }


@app.route("/health", methods=["GET"])
def health() -> Any:
    """Report whether this worker can score requests."""
    try:
        get_model()
    except FileNotFoundError as exc:
        return jsonify({"status": "unhealthy", "error": str(exc)}), 503
    return jsonify({"status": "ok"})


@app.route("/metrics", methods=["GET"])
def metrics() -> Any:
    """Return process-local counters (not shared across gunicorn workers)."""
    return jsonify(
        {
            "request_count": _request_count,
            "predict_count": _predict_count,
            "anomaly_count": _anomaly_count,
            "last_latency_ms": _last_latency_ms,
            "last_scores": list(_last_scores),
        }
    )


@app.route("/predict", methods=["POST"])
def predict() -> Any:
    """Score one sensor reading."""
    global _request_count, _predict_count, _anomaly_count, _last_latency_ms
    _request_count += 1
    started = time.perf_counter()
    payload = request.get_json(silent=True)
    try:
        reading = reading_from_payload(payload)
        model = get_model()
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 503
    result = score_reading(model, reading)
    _predict_count += 1
    if result["is_anomaly"]:
        _anomaly_count += 1
    _last_latency_ms = (time.perf_counter() - started) * 1000.0
    _last_scores.append(result["anomaly_score"])
    log = LOGGER.warning if result["is_anomaly"] else LOGGER.info
    log(
        "predict anomaly_score=%.4f is_anomaly=%s latency_ms=%.2f reading=%s",
        result["anomaly_score"],
        result["is_anomaly"],
        _last_latency_ms,
        reading,
    )
    return jsonify(result)


configure_logging()
