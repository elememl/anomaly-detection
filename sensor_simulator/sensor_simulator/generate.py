import csv
import logging
import random

from sensor_simulator.config import SENSOR_DATA_PATH, SENSOR_N_SAMPLES, SENSOR_TRAIN_SEED
from sensor_simulator.sensors import FEATURES, sample_stream_item

LOGGER = logging.getLogger(__name__)


def generate_rows(n_samples: int, seed: int) -> list[dict[str, object]]:
    """Build labelled rows from the shop-floor sampling model."""
    rng = random.Random(seed)
    rows: list[dict[str, object]] = []
    for _ in range(n_samples):
        reading, is_anomaly, _mode = sample_stream_item(rng)
        row: dict[str, object] = {name: reading[name] for name in FEATURES}
        row["is_anomaly"] = is_anomaly
        rows.append(row)
    return rows


def write_csv(rows: list[dict[str, object]]) -> None:
    """Write features plus evaluation-only is_anomaly to SENSOR_DATA_PATH."""
    SENSOR_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(FEATURES) + ["is_anomaly"]
    with SENSOR_DATA_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    """Write a training CSV for the detection package to consume."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    rows = generate_rows(SENSOR_N_SAMPLES, SENSOR_TRAIN_SEED)
    write_csv(rows)
    n_injected = sum(1 for row in rows if row["is_anomaly"])
    LOGGER.info("wrote %s rows (%s injected faults) to %s", len(rows), n_injected, SENSOR_DATA_PATH)


if __name__ == "__main__":
    main()
