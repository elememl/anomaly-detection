import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = PACKAGE_ROOT.parent

DASHBOARD_LOG_PATH = Path(os.environ.get("DASHBOARD_LOG_PATH", str(PROJECT_ROOT / "data" / "stream_log.jsonl")))
DASHBOARD_REFRESH_SECONDS = float(os.environ.get("DASHBOARD_REFRESH_SECONDS", "2"))
DASHBOARD_WINDOW = int(os.environ.get("DASHBOARD_WINDOW", "60"))
