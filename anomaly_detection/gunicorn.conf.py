from anomaly_detection.config import ANOMALY_BIND, ANOMALY_LOG_LEVEL, ANOMALY_WORKERS

bind = ANOMALY_BIND
workers = ANOMALY_WORKERS
accesslog = "-"
errorlog = "-"
loglevel = ANOMALY_LOG_LEVEL.lower()
