import csv
import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from anomaly_detection.config import (
    ANOMALY_CONTAMINATION,
    ANOMALY_DATA_PATH,
    ANOMALY_MODEL_PATH,
    ANOMALY_SEED,
    ARTIFACTS_DIR,
    FEATURES,
)

LOGGER = logging.getLogger(__name__)


def _parse_label(value: object) -> bool:
    text = str(value).strip().lower()
    if text in ("true", "1"):
        return True
    if text in ("false", "0"):
        return False
    raise ValueError(f"is_anomaly must be boolean, got {value!r}")


def read_rows(path: Path) -> list[dict[str, object]]:
    """Load feature columns and optional is_anomaly labels from CSV."""
    if not path.is_file():
        raise FileNotFoundError(f"training CSV not found: {path}")
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        missing = [name for name in FEATURES if name not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV missing columns {missing}: {path}")
        rows: list[dict[str, object]] = []
        for raw in reader:
            row: dict[str, object] = {name: float(raw[name]) for name in FEATURES}
            if "is_anomaly" in raw and raw["is_anomaly"] != "":
                row["is_anomaly"] = _parse_label(raw["is_anomaly"])
            rows.append(row)
    if not rows:
        raise ValueError(f"CSV has no data rows: {path}")
    return rows


def fit_model(rows: list[dict[str, object]]) -> IsolationForest:
    """Fit IsolationForest on feature columns only; labels are not used."""
    matrix = np.array([[row[name] for name in FEATURES] for row in rows], dtype=float)
    model = IsolationForest(contamination=ANOMALY_CONTAMINATION, random_state=ANOMALY_SEED)
    model.fit(matrix)
    return model


def detection_rate(model: IsolationForest, rows: list[dict[str, object]]) -> float | None:
    """Fraction of labelled-fault rows flagged as outliers, if labels exist."""
    injected = [row for row in rows if row.get("is_anomaly") is True]
    if not injected:
        return None
    matrix = np.array([[row[name] for name in FEATURES] for row in injected], dtype=float)
    flags = model.predict(matrix)
    return float(np.mean(flags == -1))


def main() -> None:
    """Fit IsolationForest from the training CSV and write the model file."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_rows(ANOMALY_DATA_PATH)
    model = fit_model(rows)
    joblib.dump(model, ANOMALY_MODEL_PATH)
    rate = detection_rate(model, rows)
    n_injected = sum(1 for row in rows if row.get("is_anomaly") is True)
    LOGGER.info(
        "trained n_samples=%s n_labelled_faults=%s contamination=%s detection_rate=%s",
        len(rows),
        n_injected,
        ANOMALY_CONTAMINATION,
        f"{rate:.3f}" if rate is not None else "n/a",
    )
    LOGGER.info("model=%s data=%s", ANOMALY_MODEL_PATH, ANOMALY_DATA_PATH)


if __name__ == "__main__":
    main()
