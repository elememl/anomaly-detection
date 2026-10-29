import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent
ARTIFACTS_DIR = PACKAGE_ROOT / "artifacts"

FEATURES = ("temperature", "humidity", "sound_volume")

ANOMALY_BIND = os.environ.get("ANOMALY_BIND", "127.0.0.1:5000")
ANOMALY_WORKERS = int(os.environ.get("ANOMALY_WORKERS", "2"))
ANOMALY_MODEL_PATH = Path(os.environ.get("ANOMALY_MODEL_PATH", str(ARTIFACTS_DIR / "model.joblib")))
ANOMALY_DATA_PATH = Path(os.environ.get("ANOMALY_DATA_PATH", str(PROJECT_ROOT / "data" / "train.csv")))
ANOMALY_CONTAMINATION = float(os.environ.get("ANOMALY_CONTAMINATION", "0.05"))
ANOMALY_SEED = int(os.environ.get("ANOMALY_SEED", "42"))
ANOMALY_LOG_LEVEL = os.environ.get("ANOMALY_LOG_LEVEL", "INFO").upper()
