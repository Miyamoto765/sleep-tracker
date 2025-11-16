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

def load_all_data():
    """Load and combine data from all sources."""
    dfs = []

    # Load upload history
    if os.path.exists(HISTORY_CSV):
        try:
            # Try reading with error handling for malformed CSV
            df_upload = pd.read_csv(HISTORY_CSV, on_bad_lines='skip', engine='python')
            if not df_upload.empty:
                df_upload['data_source'] = 'upload'
                dfs.append(df_upload)
        except Exception as e:
            try:
                # Fallback: try with skip bad lines
                df_upload = pd.read_csv(HISTORY_CSV, on_bad_lines='skip', sep=',', quoting=1, skipinitialspace=True)
                if not df_upload.empty:
                    df_upload['data_source'] = 'upload'
                    dfs.append(df_upload)
            except Exception as e2:
                st.warning(f"Failed to read upload history: {e}. Attempting manual fix...")
                # Last resort: try to fix manually
                try:
                    with open(HISTORY_CSV, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    # Clean lines - remove lines with wrong field count
                    header = lines[0] if lines else None
                    if header:
                        expected_fields = len(header.split(','))
                        clean_lines = [header]
                        for line in lines[1:]:
                            if len(line.split(',')) == expected_fields:
                                clean_lines.append(line)
                        if len(clean_lines) > 1:
                            import io
                            df_upload = pd.read_csv(io.StringIO(''.join(clean_lines)))
                            df_upload['data_source'] = 'upload'
                            dfs.append(df_upload)
                except Exception as e3:
                    st.error(f"Could not recover upload history: {e3}")

    # Load real-time history
    if os.path.exists(REALTIME_HISTORY_CSV):
        try:
            # Try reading with error handling for malformed CSV
            df_realtime = pd.read_csv(REALTIME_HISTORY_CSV, on_bad_lines='skip', engine='python')
            if not df_realtime.empty:
                df_realtime['data_source'] = 'realtime'
                # Rename columns to match upload format
                if 'confidence' in df_realtime.columns:
                    df_realtime = df_realtime.rename(columns={'confidence': 'sleep_score'})
                if 'prediction' in df_realtime.columns:
                    df_realtime = df_realtime.rename(columns={'prediction': 'label'})
                dfs.append(df_realtime)
        except Exception as e:
            try:
                # Fallback: try with skip bad lines
                df_realtime = pd.read_csv(REALTIME_HISTORY_CSV, on_bad_lines='skip', sep=',', quoting=1, skipinitialspace=True)
                if not df_realtime.empty:
                    df_realtime['data_source'] = 'realtime'
                    if 'confidence' in df_realtime.columns:
                        df_realtime = df_realtime.rename(columns={'confidence': 'sleep_score'})
                    if 'prediction' in df_realtime.columns:
                        df_realtime = df_realtime.rename(columns={'prediction': 'label'})
                    dfs.append(df_realtime)
            except Exception as e2:
                st.warning(f"Failed to read real-time history: {e2}")

    # Load database data
    try:
        session_manager = get_session_manager()
        # Convert 90 days to hours (90 * 24 = 2160 hours)
        df_db = session_manager.get_recent_predictions(hours=2160, limit=100)
        if not df_db.empty:
            df_db['data_source'] = 'database'
            # Rename columns to match format
            df_db = df_db.rename(columns={
                'predicted_stage': 'label',
                'confidence_score': 'sleep_score'
            })
            if 'created_at' in df_db.columns:
                df_db = df_db.rename(columns={'created_at': 'timestamp'})
            dfs.append(df_db)
    except Exception as e:
        st.warning(f"Could not load database data: {e}")

    # Combine all data
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True, sort=False)
    else:
        combined_df = pd.DataFrame()

    return combined_df

def create_advanced_charts(df):
    """Create advanced analytics charts."""
    if df.empty:
        return

    st.markdown("### 📈 Advanced Sleep Pattern Analysis")

    # Create tabs for different chart types
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🌊 Trends", "🎯 Patterns", "📅 Calendar"])

    with tab1:
        create_overview_charts(df)

    with tab2:
        create_trend_charts(df)

    with tab3:
        create_pattern_charts(df)

    with tab4:
        create_calendar_charts(df)

def create_overview_charts(df):
    """Create overview dashboard charts."""
    col1, col2 = st.columns(2)

    with col1:
        # Enhanced pie chart with subplots - ensure all canonical labels are shown
        st.subheader("Sleep Stage Distribution")
        
        # Ensure all canonical labels are included even with 0 counts
        stage_counts = df['label'].value_counts()
        
        # Create a series with all canonical labels, initializing to 0
        all_stages = pd.Series(0, index=CANONICAL_LABELS)
        
        # Update with actual counts
        for label, count in stage_counts.items():
            if label in CANONICAL_LABELS:
                all_stages[label] = count
        
        # Add any extra labels not in canonical list (like "Unknown")
        for label in stage_counts.index:
            if label not in CANONICAL_LABELS:
                all_stages[label] = stage_counts[label]
        
        # Filter: show all canonical labels even if 0, plus any non-canonical with data
        # But pie charts don't display 0 values well, so show canonical with min 0.1 if 0
        display_stages = all_stages.copy()
        for label in CANONICAL_LABELS:
            if display_stages[label] == 0:
                display_stages[label] = 0.1  # Small value to show in chart
        
        # Remove the small placeholder if no actual data exists for canonical labels
        if all_stages[CANONICAL_LABELS].sum() == 0 and len([l for l in stage_counts.index if l not in CANONICAL_LABELS]) > 0:
            # Only show non-canonical labels if no canonical data
            display_stages = all_stages[all_stages > 0]
        elif all_stages[CANONICAL_LABELS].sum() > 0:
            # Show all canonical labels, replacing 0.1 placeholders with 0
            display_stages = all_stages[all_stages.index.isin(CANONICAL_LABELS) | (all_stages > 0)]
            # Set any remaining 0.1 placeholders back to 0
            for label in CANONICAL_LABELS:
                if display_stages[label] == 0.1 and label not in stage_counts.index:
                    display_stages[label] = 0

        # Filter out pure zeros for pie chart (they don't display)
        display_stages = display_stages[display_stages > 0]

        fig = go.Figure(data=[go.Pie(
            labels=display_stages.index.tolist(),
            values=display_stages.values.tolist(),
            hole=0.3,
            marker_colors=[LABEL_COLORS.get(label, "#6c7a89") for label in display_stages.index]
        )])

        # Add legend with all canonical labels even if not in chart
        fig.update_traces(textposition="inside", textinfo="percent+label",
                        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>")
        fig.update_layout(
            showlegend=True, 
            height=400,
            legend=dict(
                title="Sleep Stages",
                itemsizing="constant"
            )
        )
        st.plotly_chart(fig, width='stretch', key="overview_pie_chart_tab1")
        
        # Show info if any canonical stages are missing
        missing_stages = [label for label in CANONICAL_LABELS if label not in display_stages.index]
        if missing_stages:
            st.caption(f"💡 Note: {', '.join(missing_stages)} stages not yet recorded")

    with col2:
        # Confidence distribution
        st.subheader("Confidence Score Distribution")
        if 'sleep_score' in df.columns:
            fig = px.histogram(df, x='sleep_score', nbins=20,
                             title="Distribution of Confidence Scores",
                             color='label', color_discrete_map=LABEL_COLORS)
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch', key="confidence_distribution_tab1")
        else:
            st.info("No confidence score data available.")

    # Summary metrics row
    st.markdown("#### 📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_recordings = len(df)
        st.metric("Total Recordings", total_recordings)

    with col2:
        if 'sleep_score' in df.columns:
            avg_confidence = df['sleep_score'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.1f}%")

    with col3:
        if len(df) > 0:
            most_common = df['label'].mode().iloc[0] if not df['label'].mode().empty else 'N/A'
            st.metric("Most Common Stage", most_common)

    with col4:
        if 'timestamp' in df.columns and df['timestamp'].notna().any():
            days_active = df['timestamp'].dt.date.nunique()
            st.metric("Active Days", days_active)

def create_trend_charts(df):
    """Create trend analysis charts."""
    if 'timestamp' not in df.columns or df['timestamp'].isna().all():
        st.warning("No timestamp data available for trend analysis.")
        return

    df_time = df.dropna(subset=['timestamp']).copy()
    df_time = df_time.sort_values('timestamp')

    # Confidence over time with scatter plot
    st.subheader("Sleep Score Trends")
    if 'sleep_score' in df_time.columns:
        fig = px.scatter(df_time, x='timestamp', y='sleep_score',
                        color='label', size='sleep_score',
                        title="Confidence Score Trends Over Time",
                        color_discrete_map=LABEL_COLORS)

        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch', key="sleep_score_trends")

    # Daily/hourly patterns
    col1, col2 = st.columns(2)

    with col1:
        # Hourly distribution
        df_time['hour'] = df_time['timestamp'].dt.hour
        hourly_counts = df_time.groupby(['hour', 'label']).size().reset_index(name='count')

        fig_hourly = px.bar(hourly_counts, x='hour', y='count', color='label',
                           title="Recording Distribution by Hour",
                           color_discrete_map=LABEL_COLORS)
        fig_hourly.update_layout(height=350)
        st.plotly_chart(fig_hourly, width='stretch', key="hourly_distribution")

    with col2:
        # Day of week distribution
        df_time['day_name'] = df_time['timestamp'].dt.day_name()
        day_counts = df_time['day_name'].value_counts()

        fig_day = px.bar(x=day_counts.index, y=day_counts.values,
                        title="Recordings by Day of Week",
                        labels={'x': 'Day of Week', 'y': 'Number of Recordings'})
        fig_day.update_layout(height=350)
        st.plotly_chart(fig_day, width='stretch', key="day_of_week_distribution")

def create_pattern_charts(df):
    """Create pattern recognition charts."""
    st.subheader("Sleep Pattern Analysis")

    # Create correlation matrix if we have numeric features
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 1:
        correlation_matrix = df[numeric_cols].corr()

        fig = px.imshow(correlation_matrix,
                       title="Feature Correlation Matrix",
                       color_continuous_scale="RdBu",
                       aspect="auto")
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch', key="correlation_matrix")

    # Sleep stage transitions (if we have sequential data)
    if 'timestamp' in df.columns and len(df) > 1:
        df_sorted = df.sort_values('timestamp')

        # Create transition matrix
        stages = df_sorted['label'].unique()
        transition_matrix = pd.DataFrame(0, index=stages, columns=stages)

        for i in range(len(df_sorted) - 1):
            current_stage = df_sorted.iloc[i]['label']
            next_stage = df_sorted.iloc[i + 1]['label']
            if current_stage in stages and next_stage in stages:
                transition_matrix.loc[current_stage, next_stage] += 1

        if transition_matrix.sum().sum() > 0:
            st.subheader("Sleep Stage Transition Patterns")
            fig = px.imshow(transition_matrix,
                           title="Sleep Stage Transition Heatmap",
                           labels=dict(x="Next Stage", y="Current Stage", color="Transitions"),
                           color_continuous_scale="Viridis")
            fig.update_layout(height=400)
            st.plotly_chart(fig, width='stretch', key="transition_heatmap")

def create_calendar_charts(df):
    """Create calendar-based visualizations."""
    st.subheader("Calendar View")

    if 'timestamp' not in df.columns or df['timestamp'].isna().all():
        st.warning("No timestamp data available for calendar view.")
        return

    df_time = df.dropna(subset=['timestamp']).copy()
    df_time['date'] = df_time['timestamp'].dt.date
    df_time['week'] = df_time['timestamp'].dt.isocalendar().week
    df_time['day_of_week'] = df_time['timestamp'].dt.dayofweek

    # Weekly heatmap
    weekly_counts = df_time.groupby(['week', 'day_of_week', 'label']).size().reset_index(name='count')

    pivot_data = weekly_counts.pivot_table(index='week', columns='day_of_week', values='count', aggfunc='sum', fill_value=0)

    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    # Reindex to ensure all 7 days are present in columns, even if empty
    all_days = range(7)  # 0-6 for Monday-Sunday
    pivot_data = pivot_data.reindex(columns=all_days, fill_value=0)
    # Now safely rename columns
    pivot_data.columns = day_names

    fig = px.imshow(pivot_data.T,
                   title="Weekly Recording Heatmap",
                   labels=dict(x="Week", y="Day of Week", color="Recordings"),
                   color_continuous_scale="Blues",
                   aspect="auto")
    fig.update_layout(height=300)
    st.plotly_chart(fig, width='stretch', key="weekly_heatmap")

    # Monthly summary
    df_time['month'] = df_time['timestamp'].dt.to_period('M')
    monthly_stats = df_time.groupby('month').agg({
        'label': 'count',
        'sleep_score': 'mean' if 'sleep_score' in df_time.columns else lambda x: 0
    }).rename(columns={'label': 'recordings'})

    if not monthly_stats.empty:
        st.subheader("Monthly Summary")
        monthly_stats.index = monthly_stats.index.astype(str)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=monthly_stats.index,
            y=monthly_stats['recordings'],
            name='Recordings',
            marker_color='#4CAF50'
        ))

        if 'sleep_score' in monthly_stats.columns:
            fig.add_trace(go.Scatter(
                x=monthly_stats.index,
                y=monthly_stats['sleep_score'],
                mode='lines+markers',
                name='Avg Confidence',
                yaxis='y2',
                line=dict(color='#FF6B6B')
            ))

        fig.update_layout(
            title="Monthly Recording Trends",
            yaxis=dict(title="Number of Recordings"),
            yaxis2=dict(title="Avg Confidence (%)", overlaying='y', side='right'),
            height=400
        )
        st.plotly_chart(fig, width='stretch', key="monthly_trends")

def render():
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)
    st.header("📊 Advanced Sleep Analytics Dashboard")

    # Load all data sources
    df = load_all_data()

    if df.empty:
        st.info("No sleep data found. Upload audio files or use real-time recording to populate analytics.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Process timestamp column
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

    # Sidebar: enhanced filters
    st.sidebar.header("🔍 Analytics Filters")

    # Data source filter
    if 'data_source' in df.columns:
        data_sources = df['data_source'].unique().tolist()
        selected_sources = st.sidebar.multiselect("Data Sources", options=data_sources, default=data_sources)
    else:
        selected_sources = df['data_source'].unique() if 'data_source' in df.columns else ['all']

    # Debug controls
    with st.sidebar.expander("🔧 Debug Options"):
        show_debug = st.checkbox("Show debug info", value=False)
        if show_debug:
            st.subheader("Data Sources")
            if 'data_source' in df.columns:
                st.write(df['data_source'].value_counts().to_dict())
            st.subheader("Label Distribution")
            st.write(df["label"].value_counts(dropna=False).to_dict())

    # Date range filter
    if df["timestamp"].notna().any():
        min_date = df["timestamp"].min().date()
        max_date = df["timestamp"].max().date()
    else:
        min_date = datetime.today().date()
        max_date = datetime.today().date()

    date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date))
    all_labels = sorted(df["label"].dropna().unique().tolist())
    selected_labels = st.sidebar.multiselect("Sleep Stages", options=all_labels, default=all_labels)

    # Apply filters
    df_filtered = df.copy()

    # Filter by data source
    if 'data_source' in df.columns and selected_sources:
        df_filtered = df_filtered[df_filtered["data_source"].isin(selected_sources)]

    # Filter by date range
    if date_range and len(date_range) == 2:
        start, end = date_range
        if start:
            df_filtered = df_filtered[df_filtered["timestamp"] >= pd.to_datetime(start)]
        if end:
            df_filtered = df_filtered[df_filtered["timestamp"] <= pd.to_datetime(end) + pd.Timedelta(days=1)]

    # Filter by labels
    if selected_labels:
        df_filtered = df_filtered[df_filtered["label"].isin(selected_labels)]

    if df_filtered.shape[0] == 0:
        st.warning("No records matching current filters.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Advanced analytics section (includes overview charts in Overview tab)
    create_advanced_charts(df_filtered)

    st.markdown("---")

    # Original charts section (keep for compatibility)
    st.subheader("📋 Detailed Analysis")

    # Sleep stage distribution - ensure all canonical labels are shown
    counts = [int(df_filtered[df_filtered["label"] == lab].shape[0]) for lab in CANONICAL_LABELS]
    extras = [lab for lab in df_filtered["label"].unique() if lab not in CANONICAL_LABELS]
    ext_counts = [int(df_filtered[df_filtered["label"] == lab].shape[0]) for lab in extras]

    display_labels = CANONICAL_LABELS + extras
    display_counts = counts + ext_counts

    pie_df = pd.DataFrame({"label": display_labels, "count": display_counts})

    if pie_df["count"].sum() > 0:
        color_map = {lbl: LABEL_COLORS.get(lbl, "#6c7a89") for lbl in display_labels}
        fig_pie = px.pie(pie_df, names="label", values="count",
                         title="Sleep Stage Distribution", hole=0.35,
                         color="label", color_discrete_map=color_map)
        fig_pie.update_traces(textposition="inside", textinfo="percent+label", sort=False)
        st.plotly_chart(fig_pie, width='stretch', height=400, key="detailed_pie_chart")
    else:
        # Show empty state with all canonical labels
        empty_pie_df = pd.DataFrame({"label": CANONICAL_LABELS, "count": [0] * len(CANONICAL_LABELS)})
        color_map = {lbl: LABEL_COLORS.get(lbl, "#6c7a89") for lbl in CANONICAL_LABELS}
        fig_pie = px.pie(empty_pie_df, names="label", values="count",
                         title="Sleep Stage Distribution (No Data Yet)", hole=0.35,
                         color="label", color_discrete_map=color_map)
        fig_pie.update_traces(textposition="inside", textinfo="label")
        st.plotly_chart(fig_pie, width='stretch', height=400, key="detailed_pie_chart_empty")

    # Average confidence by stage
    if "sleep_score" in df_filtered.columns:
        score_by_label = df_filtered.groupby("label")["sleep_score"].mean().reset_index().sort_values("sleep_score", ascending=False)
        if score_by_label.shape[0] > 0:
            fig_bar = px.bar(score_by_label, x="sleep_score", y="label", orientation="h",
                           labels={"sleep_score": "Average Confidence Score", "label": "Sleep Stage"},
                           title="Average Confidence by Sleep Stage",
                           color="label", color_discrete_map=LABEL_COLORS)
            fig_bar.update_layout(xaxis_range=[0,100], showlegend=False, height=300)
            st.plotly_chart(fig_bar, width='stretch', key="avg_confidence_bar")

    # Time series analysis
    if "sleep_score" in df_filtered.columns and df_filtered["sleep_score"].notna().any():
        df_time = df_filtered.dropna(subset=["timestamp"]).copy().sort_values("timestamp")
        if not df_time.empty:
            fig_line = px.line(df_time, x="timestamp", y="sleep_score", color="label",
                              markers=True,
                              labels={"timestamp": "Time", "sleep_score": "Confidence Score (%)"},
                              title="Confidence Score Timeline",
                              color_discrete_map=LABEL_COLORS)
            fig_line.update_yaxes(range=[0,100], height=300)
            st.plotly_chart(fig_line, width='stretch', key="confidence_timeline")

    # Recent recordings table
    with st.expander("📊 Recent Recordings", expanded=False):
        show_cols = ["timestamp","filename","label","sleep_score","data_source","prediction","filepath"]
        available = [c for c in show_cols if c in df_filtered.columns]
        recent_table = df_filtered.sort_values("timestamp", ascending=False)[available].head(20).reset_index(drop=True)

        if "sleep_score" in recent_table.columns:
            recent_table["sleep_score"] = recent_table["sleep_score"].apply(lambda x: f"{int(x)}%" if pd.notna(x) else "")
        if "timestamp" in recent_table.columns:
            recent_table["timestamp"] = recent_table["timestamp"].dt.strftime('%Y-%m-%d %H:%M')

        st.dataframe(recent_table, width='stretch')

    # Export functionality
    with st.expander("💾 Export Options"):
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Export to CSV"):
                csv_data = df_filtered.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"sleep_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

        with col2:
            if st.button("Export to JSON"):
                json_data = df_filtered.to_json(orient='records', date_format='iso', indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"sleep_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    st.markdown('</div>', unsafe_allow_html=True)
