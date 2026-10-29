import json
from pathlib import Path

import altair as alt
import pandas as pd

SENSORS = ("temperature", "humidity", "sound_volume")
COLUMNS = ("timestamp", *SENSORS, "anomaly_score", "is_anomaly", "injected_fault", "fault_mode", "status")

ANOMALY = "anomaly"
NORMAL = "normal"
UNSCORED = "unscored"
STATUSES = (NORMAL, ANOMALY, UNSCORED)


def time_x() -> alt.X:
    """Shared x encoding: clock time as HH:MM:SS, few ticks."""
    return alt.X(
        "timestamp:T",
        axis=alt.Axis(format="%H:%M:%S", tickCount=5, labelOverlap=True, title=None),
    )


def status_of(is_anomaly: object) -> str:
    """Map a stored is_anomaly value onto a display status."""
    if is_anomaly is True:
        return ANOMALY
    if is_anomaly is False:
        return NORMAL
    return UNSCORED


def read_events(path: Path, window: int) -> pd.DataFrame:
    """Load the most recent stream events written by the simulator."""
    if not path.is_file():
        return pd.DataFrame(columns=list(COLUMNS))
    with path.open() as handle:
        lines = handle.readlines()
    # A line without a trailing newline is still being written by the simulator.
    records = [json.loads(line) for line in lines[-window:] if line.endswith("\n")]
    if not records:
        return pd.DataFrame(columns=list(COLUMNS))
    frame = pd.DataFrame.from_records(records)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    frame["status"] = [status_of(record.get("is_anomaly")) for record in records]
    return frame.sort_values("timestamp").reset_index(drop=True)


def sensor_series(frame: pd.DataFrame) -> pd.DataFrame:
    """Reshape sensor columns into long form for plotting."""
    return frame.melt(
        id_vars=["timestamp", "status"],
        value_vars=list(SENSORS),
        var_name="sensor",
        value_name="value",
    )
