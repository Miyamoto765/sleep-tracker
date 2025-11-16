# app/views/analytics.py
import os
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
from src.session_manager import get_session_manager
import numpy as np

HISTORY_CSV = "data/upload_history.csv"
REALTIME_HISTORY_CSV = "data/realtime_history.csv"

CANONICAL_LABELS = ["Wake", "Light sleep", "Deep sleep", "REM"]
LABEL_COLORS = {
    "Wake": "#88c9ff",
    "Light sleep": "#0f66c2",
    "Deep sleep": "#ffb6c1",
    "REM": "#ff4d4f",
    "Unknown": "#7f8c8d",
}

def _ensure_sleep_score_column(df: pd.DataFrame) -> pd.DataFrame:
    if "sleep_score" in df.columns:
        df["sleep_score"] = pd.to_numeric(df["sleep_score"], errors="coerce")
    elif "score" in df.columns:
        df["sleep_score"] = pd.to_numeric(df["score"], errors="coerce")
    else:
        df["sleep_score"] = pd.Series([None] * len(df))
    df["sleep_score"] = df["sleep_score"].apply(lambda x: None if pd.isna(x) else float(max(0.0, min(100.0, x))))
    return df

def _map_prediction_to_label(pred):
    if pd.isna(pred):
        return "Unknown"
    # numeric case
    try:
        if isinstance(pred, (int, float)) and not isinstance(pred, bool):
            ival = int(pred)
            return {0: "Wake", 1: "Light sleep", 2: "Deep sleep", 3: "REM"}.get(ival, "Unknown")
    except Exception:
        pass
    s = str(pred).strip().lower()
    if s.isdigit():
        ival = int(s)
        return {0: "Wake", 1: "Light sleep", 2: "Deep sleep", 3: "REM"}.get(ival, "Unknown")
    if "rem" in s:
        return "REM"
    if "deep" in s:
        return "Deep sleep"
    if "light" in s:
        return "Light sleep"
    if "wake" in s or "awake" in s:
        return "Wake"
    return "Unknown"

def render():
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)
    st.header("📊 Analytics — Upload history & trends")

    if not os.path.exists(HISTORY_CSV):
        st.info("No upload history found. Upload an audio file first to populate analytics.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    try:
        df = pd.read_csv(HISTORY_CSV)
    except Exception as e:
        st.error(f"Failed to read history CSV: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        df["timestamp"] = pd.NaT

    df = _ensure_sleep_score_column(df)

    # Build label column (prefer 'label' if present, else map from prediction)
    if "label" in df.columns and df["label"].notna().any():
        df["label"] = df["label"].apply(lambda x: _map_prediction_to_label(x) if pd.notna(x) else "Unknown")
    elif "prediction" in df.columns:
        df["label"] = df["prediction"].apply(_map_prediction_to_label)
    else:
        df["label"] = "Unknown"

    # Sidebar: debug controls
    st.sidebar.header("Filters & debug")
    show_debug = st.sidebar.checkbox("Show debug info (raw values)", value=False)
    if show_debug:
        st.sidebar.subheader("Raw prediction values")
        if "prediction" in df.columns:
            st.sidebar.write(df["prediction"].value_counts(dropna=False).to_dict())
        else:
            st.sidebar.write("No 'prediction' column found")
        st.sidebar.subheader("Derived labels")
        st.sidebar.write(df["label"].value_counts(dropna=False).to_dict())

    # Filters
    min_date = df["timestamp"].min()
    max_date = df["timestamp"].max()
    if pd.isna(min_date) or pd.isna(max_date):
        min_date = datetime.today()
        max_date = datetime.today()
    date_range = st.sidebar.date_input("Date range", value=(min_date.date(), max_date.date()))
    all_labels = sorted(df["label"].dropna().unique().tolist())
    selected_labels = st.sidebar.multiselect("Labels", options=all_labels, default=all_labels)

    # apply
    df_filtered = df.copy()
    if date_range and len(date_range) == 2:
        start, end = date_range
        if start:
            df_filtered = df_filtered[df_filtered["timestamp"] >= pd.to_datetime(start)]
        if end:
            df_filtered = df_filtered[df_filtered["timestamp"] <= pd.to_datetime(end) + pd.Timedelta(days=1)]
    if selected_labels:
        df_filtered = df_filtered[df_filtered["label"].isin(selected_labels)]

    if df_filtered.shape[0] == 0:
        st.info("No records matching filters.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # summary metrics
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        st.metric("Uploads", str(len(df_filtered)))
    with col2:
        mean_score = df_filtered["sleep_score"].dropna()
        mean_score_val = int(mean_score.mean()) if not mean_score.empty else "N/A"
        st.metric("Mean Sleep Score", f"{mean_score_val}/100")
    with col3:
        most_common = df_filtered["label"].mode().iloc[0] if not df_filtered["label"].mode().empty else "N/A"
        st.metric("Most common label", most_common)

    st.markdown("---")

    # Build pie: ensure canonical labels included even if count 0
    counts = [int(df_filtered[df_filtered["label"] == lab].shape[0]) for lab in CANONICAL_LABELS]
    extras = [lab for lab in df_filtered["label"].unique() if lab not in CANONICAL_LABELS]
    ext_counts = [int(df_filtered[df_filtered["label"] == lab].shape[0]) for lab in extras]

    display_labels = CANONICAL_LABELS + extras
    display_counts = counts + ext_counts

    pie_df = pd.DataFrame({"label": display_labels, "count": display_counts})

    if pie_df["count"].sum() == 0:
        st.info("No labelled records to show in cluster distribution.")
    else:
        color_map = {lbl: LABEL_COLORS.get(lbl, "#6c7a89") for lbl in display_labels}
        fig_pie = px.pie(pie_df, names="label", values="count", title="Predicted cluster distribution (labels)", hole=0.35, color="label", color_discrete_map=color_map)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label", sort=False)
        st.plotly_chart(fig_pie, use_container_width=True, height=450)

    st.markdown("---")

    # Average sleep_score per label
    score_by_label = df_filtered.groupby("label")["sleep_score"].mean().reset_index().sort_values("sleep_score", ascending=False)
    if score_by_label.shape[0] > 0:
        fig_bar = px.bar(score_by_label, x="sleep_score", y="label", orientation="h", labels={"sleep_score": "Average sleep score", "label": ""}, title="Average sleep score by label", color="label", color_discrete_map=color_map)
        fig_bar.update_layout(xaxis_range=[0,100], showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, height=320)
    else:
        st.info("No sleep_score values to compute averages.")

    st.markdown("---")

    # time series: sleep_score
    if "sleep_score" in df_filtered.columns and df_filtered["sleep_score"].notna().any():
        df_time = df_filtered.dropna(subset=["timestamp"]).copy().sort_values("timestamp")
        fig_line = px.line(df_time, x="timestamp", y="sleep_score", color="label", markers=True, labels={"timestamp": "Time", "sleep_score": "Sleep score (%)"}, title="Sleep score timeline", color_discrete_map=color_map)
        fig_line.update_yaxes(range=[0,100])
        st.plotly_chart(fig_line, use_container_width=True, height=360)
    else:
        st.info("No sleep_score values found to plot timeline.")

    st.markdown("---")
    st.subheader("Recent uploads")
    show_cols = ["timestamp","filename","label","sleep_score","prediction","filepath"]
    available = [c for c in show_cols if c in df_filtered.columns]
    recent_table = df_filtered.sort_values("timestamp", ascending=False)[available].head(20).reset_index(drop=True)
    if "sleep_score" in recent_table.columns:
        recent_table["sleep_score"] = recent_table["sleep_score"].apply(lambda x: f"{int(x)}" if pd.notna(x) else "")
    st.dataframe(recent_table)

    st.markdown('</div>', unsafe_allow_html=True)
