import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent

SENSOR_API_URL = os.environ.get("SENSOR_API_URL", "http://127.0.0.1:5000")
SENSOR_INTERVAL_SECONDS = float(os.environ.get("SENSOR_INTERVAL_SECONDS", "1.0"))
SENSOR_SEED = os.environ.get("SENSOR_SEED")
SENSOR_N_SAMPLES = int(os.environ.get("SENSOR_N_SAMPLES", "2000"))
SENSOR_DATA_PATH = Path(os.environ.get("SENSOR_DATA_PATH", str(PROJECT_ROOT / "data" / "train.csv")))
SENSOR_TRAIN_SEED = int(os.environ.get("SENSOR_TRAIN_SEED", "42"))
SENSOR_LOG_PATH = Path(os.environ.get("SENSOR_LOG_PATH", str(PROJECT_ROOT / "data" / "stream_log.jsonl")))
