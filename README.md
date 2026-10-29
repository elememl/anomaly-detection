# Stream Anomaly Detection

This project simulates factory sensor readings and uses an Isolation Forest model to detect unusual values. It includes three main components:

- **Sensor simulator:** Generates temperature, humidity, and sound readings, including simulated faults.
- **Flask API:** Uses the trained Isolation Forest model to identify anomalies.
- **Streamlit dashboard:** Displays sensor readings, anomaly scores, and recent events.

The simulator sends readings to the API for prediction and saves the results in a JSONL event log. The dashboard reads this log to display the latest results.

## Installation

From the root directory, install the dependencies for each component:

```bash
cd anomaly_detection && uv sync
cd ../sensor_simulator && uv sync
cd ../dashboard && uv sync
```

Each component has its own Python environment and dependency configuration.

## Running the Project

Open three separate terminals. Run the following commands from the indicated directories.

**Terminal 1 — Prediction API**

From `anomaly_detection/`, on Linux using Gunicorn:

```bash
uv run gunicorn -c gunicorn.conf.py anomaly_detection.app:app
```


**Terminal 2 — Sensor simulator**

From `sensor_simulator/`:

```bash
uv run python -m sensor_simulator
```

**Terminal 3 — Dashboard**

From `dashboard/`:

```bash
uv run streamlit run dashboard/app.py
```

Open the dashboard at http://localhost:8501.

The dashboard refreshes every two seconds and displays the latest 60 readings, including anomaly scores, sensor measurements, and a table of recent events.


## Model Training

To regenerate the training dataset, run the following command from `sensor_simulator/`:

```bash
uv run python -m sensor_simulator.generate
```

This creates `data/train.csv`.

To train the model, run the following command from `anomaly_detection/`:

```bash
uv run python -m anomaly_detection.train
```

The trained model is saved as `artifacts/model.joblib` and loaded by the Flask API when the service starts. Restart the API after retraining to load the updated model.

## API Endpoints

The Flask API provides three endpoints:

| Endpoint | Purpose |
|---|---|
| `POST /predict` | Receives sensor values and returns an anomaly prediction |
| `GET /health` | Checks whether the model is available |
| `GET /metrics` | Returns basic service statistics |


## Monitoring and Visualization

The Streamlit dashboard shows the anomaly score over time, the three sensor measurements, and a table of recent events.

Readings are displayed using three categories:

- **Normal:** Successfully scored readings classified as normal.
- **Anomaly:** Successfully scored readings classified as anomalous.
- **Unscored:** Readings for which the prediction API did not return a result.


## Technical Notes

The three components run independently. The simulator is responsible for writing the event log, while the prediction API processes requests without storing individual sensor readings.

The API can also be run with multiple Gunicorn workers. Each worker loads its own copy of the model and maintains its own metrics, so the current implementation does not provide centralized statistics across workers.

Configuration can be adjusted through environment variables using the `ANOMALY_*`, `SENSOR_*`, and `DASHBOARD_*` prefixes.

## Tests

```bash
cd anomaly_detection && uv run pytest
cd ../sensor_simulator && uv run pytest
cd ../dashboard && uv run pytest
```
