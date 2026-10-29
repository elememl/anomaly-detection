import json
import logging
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from sensor_simulator.config import SENSOR_API_URL, SENSOR_INTERVAL_SECONDS, SENSOR_LOG_PATH, SENSOR_SEED
from sensor_simulator.sensors import FEATURES, sample_stream_item

LOGGER = logging.getLogger(__name__)


def predict_url() -> str:
    """Return the scoring endpoint from SENSOR_API_URL."""
    return SENSOR_API_URL.rstrip("/") + "/predict"


def post_reading(reading: dict[str, float]) -> dict:
    """POST one reading and return the parsed JSON body."""
    payload = {name: reading[name] for name in FEATURES}
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        predict_url(),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def build_event(
    reading: dict[str, float],
    injected: bool,
    mode: str | None,
    result: dict | None,
    error: str | None = None,
) -> dict:
    """Combine one reading, its local ground truth, and the API verdict if there was one."""
    scored = result is not None
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "injected_fault": injected,
        "fault_mode": mode,
        "scored": scored,
        "anomaly_score": result["anomaly_score"] if scored else None,
        "is_anomaly": result["is_anomaly"] if scored else None,
        "error": error,
    }
    event.update({name: reading[name] for name in FEATURES})
    return event


def append_event(event: dict) -> None:
    """Append one JSON line to the shared stream log the dashboard reads."""
    SENSOR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SENSOR_LOG_PATH.open("a") as handle:
        handle.write(json.dumps(event) + "\n")


def make_rng() -> random.Random:
    """Build the stream RNG from SENSOR_SEED when set."""
    if SENSOR_SEED is None:
        return random.Random()
    return random.Random(int(SENSOR_SEED))


def run_forever(rng: random.Random | None = None) -> None:
    """Sample, score if the API answers, and record every item until interrupted."""
    stream_rng = rng if rng is not None else make_rng()
    while True:
        reading, injected, mode = sample_stream_item(stream_rng)
        try:
            result = post_reading(reading)
        except (urllib.error.URLError, TimeoutError) as exc:
            event = build_event(reading, injected, mode, None, str(exc))
            LOGGER.warning("unscored: %s reading=%s", exc, reading)
        else:
            event = build_event(reading, injected, mode, result)
            LOGGER.info(
                "injected_fault=%s fault_mode=%s is_anomaly=%s anomaly_score=%s reading=%s",
                injected,
                mode,
                result["is_anomaly"],
                result["anomaly_score"],
                reading,
            )
        append_event(event)
        time.sleep(SENSOR_INTERVAL_SECONDS)


def main() -> None:
    """Start the continuous sensor stream."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    LOGGER.info("posting to %s interval=%ss log=%s", predict_url(), SENSOR_INTERVAL_SECONDS, SENSOR_LOG_PATH)
    run_forever()
