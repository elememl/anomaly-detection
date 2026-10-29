import altair as alt
import pandas as pd
import streamlit as st

from dashboard.config import DASHBOARD_LOG_PATH, DASHBOARD_REFRESH_SECONDS, DASHBOARD_WINDOW
from dashboard.events import ANOMALY, NORMAL, STATUSES, UNSCORED, read_events, sensor_series, time_x

NORMAL_COLOR = "#8fb8de"
ANOMALY_COLOR = "#e4572e"
UNSCORED_COLOR = "#b0b0b0"
STATUS_SCALE = alt.Scale(domain=list(STATUSES), range=[NORMAL_COLOR, ANOMALY_COLOR, UNSCORED_COLOR])


def score_chart(frame: pd.DataFrame) -> alt.LayerChart:
    """Anomaly score over time with flagged items highlighted."""
    scored = frame[frame["status"] != UNSCORED]
    base = alt.Chart(scored).encode(x=time_x())
    line = base.mark_line(color=NORMAL_COLOR, opacity=0.7).encode(y=alt.Y("anomaly_score:Q", title="anomaly score"))
    points = base.mark_circle(size=110).encode(
        y="anomaly_score:Q",
        color=alt.Color("status:N", scale=STATUS_SCALE, legend=alt.Legend(title="status")),
        tooltip=[alt.Tooltip("timestamp:T", format="%H:%M:%S"), "anomaly_score:Q", "status:N", "fault_mode:N"],
    )
    return (line + points).properties(height=260)


def sensor_chart(frame: pd.DataFrame) -> alt.Chart:
    """Raw sensor readings over time, one row per sensor."""
    return (
        alt.Chart(sensor_series(frame))
        .mark_circle(size=45)
        .encode(
            x=time_x(),
            y=alt.Y("value:Q", title=None).scale(zero=False),
            color=alt.Color("status:N", scale=STATUS_SCALE, legend=None),
            row=alt.Row("sensor:N", title=None),
            tooltip=[alt.Tooltip("timestamp:T", format="%H:%M:%S"), "sensor:N", "value:Q", "status:N"],
        )
        .properties(height=110)
    )


def render_summary(frame: pd.DataFrame) -> None:
    """Show rolling counters for the current window."""
    counts = frame["status"].value_counts()
    flagged = int(counts.get(ANOMALY, 0))
    scored = flagged + int(counts.get(NORMAL, 0))
    left, middle, right = st.columns(3)
    left.metric("Last sample size", len(frame))
    middle.metric("Anomalies", flagged)
    rate = f"{flagged / scored:.1%}" if scored else "n/a"
    right.metric("Anomaly rate", rate)


@st.fragment(run_every=DASHBOARD_REFRESH_SECONDS)
def render() -> None:
    """Redraw the whole page from the latest events on disk."""
    frame = read_events(DASHBOARD_LOG_PATH, DASHBOARD_WINDOW)
    if frame.empty:
        st.info(f"Waiting for stream events in {DASHBOARD_LOG_PATH}. Start the simulator.")
        return
    render_summary(frame)
    unscored = int((frame["status"] == UNSCORED).sum())
    if unscored:
        st.warning(f"{unscored} of the last {len(frame)} items are unscored. The detection API is not answering.")
    st.altair_chart(score_chart(frame), width="stretch")
    st.altair_chart(sensor_chart(frame), width="stretch")
    st.subheader("Recent items")
    recent = frame.sort_values("timestamp", ascending=False).head(15)
    st.dataframe(recent, width="stretch", hide_index=True)


st.set_page_config(page_title="Production anomaly monitor", layout="wide")
st.title("Production anomaly monitor")
st.caption(f"Rolling window of {DASHBOARD_WINDOW} items, refreshing every {DASHBOARD_REFRESH_SECONDS:g}s")
render()
