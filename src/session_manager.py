# src/session_manager.py
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SessionManager:
    """Manages user sessions and recording persistence for the sleep tracker."""

    def __init__(self, db_path: str = "data/sleep_tracker.db"):
        """
        Initialize session manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database tables."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Recording sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS recording_sessions (
                        session_id TEXT PRIMARY KEY,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_type TEXT CHECK(session_type IN ('realtime', 'upload', 'live')) DEFAULT 'realtime',
                        status TEXT CHECK(status IN ('active', 'completed', 'error')) DEFAULT 'active',
                        duration_seconds INTEGER,
                        user_agent TEXT,
                        metadata TEXT
                    )
                ''')

                # Audio recordings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audio_recordings (
                        recording_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        filename TEXT,
                        file_path TEXT,
                        duration_seconds REAL,
                        file_size_bytes INTEGER,
                        format TEXT,
                        sample_rate INTEGER,
                        channels INTEGER,
                        metadata TEXT,
                        FOREIGN KEY (session_id) REFERENCES recording_sessions (session_id)
                    )
                ''')

                # Sleep predictions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sleep_predictions (
                        prediction_id TEXT PRIMARY KEY,
                        recording_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        predicted_stage TEXT,
                        confidence_score REAL,
                        raw_prediction TEXT,
                        model_version TEXT,
                        features_snapshot TEXT,
                        FOREIGN KEY (recording_id) REFERENCES audio_recordings (recording_id)
                    )
                ''')

                # Sleep quality metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sleep_quality_metrics (
                        metric_id TEXT PRIMARY KEY,
                        prediction_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sleep_score REAL,
                        deep_sleep_ratio REAL,
                        rem_sleep_ratio REAL,
                        light_sleep_ratio REAL,
                        wake_periods INTEGER,
                        avg_confidence REAL,
                        total_recordings INTEGER,
                        metadata TEXT,
                        FOREIGN KEY (prediction_id) REFERENCES sleep_predictions (prediction_id)
                    )
                ''')

                # User preferences table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_preferences (
                        pref_id TEXT PRIMARY KEY DEFAULT 'default',
                        theme TEXT DEFAULT 'dark',
                        auto_download BOOLEAN DEFAULT FALSE,
                        max_recordings_per_session INTEGER DEFAULT 10,
                        reminder_enabled BOOLEAN DEFAULT FALSE,
                        reminder_time TEXT,
                        privacy_mode BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON recording_sessions(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_recordings_session_id ON audio_recordings(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_predictions_recording_id ON sleep_predictions(recording_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_prediction_id ON sleep_quality_metrics(metric_id)')

                conn.commit()

        except Exception as e:
            logger.error(f"Error initializing database: {e}")

    def create_session(self, session_type: str = "realtime", metadata: Dict[str, Any] = None) -> str:
        """
        Create a new recording session.

        Args:
            session_type: Type of session ('realtime', 'upload', 'live')
            metadata: Additional session metadata

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO recording_sessions
                    (session_id, session_type, status, metadata)
                    VALUES (?, ?, 'active', ?)
                ''', (session_id, session_type, metadata_json))
                conn.commit()

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None

        return session_id

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session information.

        Args:
            session_id: Session ID to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build dynamic update query
                set_clauses = []
                values = []

                for key, value in updates.items():
                    if key == 'metadata':
                        set_clauses.append("metadata = ?")
                        values.append(json.dumps(value))
                    elif key == 'updated_at':
                        set_clauses.append("updated_at = ?")
                        values.append(value)
                    else:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)

                if set_clauses:
                    query = f"UPDATE recording_sessions SET {', '.join(set_clauses)} WHERE session_id = ?"
                    values.append(session_id)
                    cursor.execute(query, values)
                    conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False

    def complete_session(self, session_id: str, duration_seconds: int = None) -> bool:
        """
        Mark a session as completed.

        Args:
            session_id: Session ID to complete
            duration_seconds: Total duration of the session

        Returns:
            True if successful
        """
        updates = {'status': 'completed', 'updated_at': datetime.now()}
        if duration_seconds is not None:
            updates['duration_seconds'] = duration_seconds

        return self.update_session(session_id, updates)

    def add_recording(self, session_id: str, filename: str, file_path: str,
                     duration_seconds: float, file_size_bytes: int,
                     format: str, sample_rate: int, channels: int = 1,
                     metadata: Dict[str, Any] = None) -> str:
        """
        Add a new audio recording to a session.

        Args:
            session_id: Parent session ID
            filename: Original filename
            file_path: Path to stored file
            duration_seconds: Recording duration
            file_size_bytes: File size in bytes
            format: Audio format
            sample_rate: Sample rate
            channels: Number of channels
            metadata: Additional metadata

        Returns:
            Recording ID or None if failed
        """
        recording_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata or {})

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO audio_recordings
                    (recording_id, session_id, filename, file_path,
                     duration_seconds, file_size_bytes, format, sample_rate, channels, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (recording_id, session_id, filename, file_path,
                      duration_seconds, file_size_bytes, format, sample_rate, channels, metadata_json))
                conn.commit()

        except Exception as e:
            logger.error(f"Error adding recording: {e}")
            return None

        return recording_id

    def add_prediction(self, recording_id: str, predicted_stage: str, confidence_score: float,
                      raw_prediction: str, model_version: str = "1.0",
                      features_snapshot: Dict[str, Any] = None) -> str:
        """
        Add sleep prediction for a recording.

        Args:
            recording_id: Recording ID
            predicted_stage: Predicted sleep stage
            confidence_score: Confidence score (0-100)
            raw_prediction: Raw model prediction
            model_version: Model version used
            features_snapshot: Features used for prediction

        Returns:
            Prediction ID or None if failed
        """
        prediction_id = str(uuid.uuid4())
        features_json = json.dumps(features_snapshot or {})

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sleep_predictions
                    (prediction_id, recording_id, predicted_stage, confidence_score,
                     raw_prediction, model_version, features_snapshot)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (prediction_id, recording_id, predicted_stage, confidence_score,
                      raw_prediction, model_version, features_json))
                conn.commit()

        except Exception as e:
            logger.error(f"Error adding prediction: {e}")
            return None

        return prediction_id

    def get_session_history(self, limit: int = 10, session_type: str = None) -> pd.DataFrame:
        """
        Get session history with related recordings and predictions.

        Args:
            limit: Maximum number of sessions to return
            session_type: Filter by session type

        Returns:
            DataFrame with session information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT rs.*,
                           COUNT(ar.recording_id) as recording_count,
                           MAX(sp.confidence_score) as max_confidence,
                           MAX(sp.created_at) as last_prediction_time
                    FROM recording_sessions rs
                    LEFT JOIN audio_recordings ar ON rs.session_id = ar.session_id
                    LEFT JOIN sleep_predictions sp ON ar.recording_id = sp.recording_id
                '''

                if session_type:
                    query += f" WHERE rs.session_type = '{session_type}'"

                query += '''
                    GROUP BY rs.session_id
                    ORDER BY rs.created_at DESC
                    LIMIT ?
                '''

                df = pd.read_sql_query(query, conn, params=[limit])
                return df

        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return pd.DataFrame()

    def get_recent_predictions(self, hours: int = 24, limit: int = 20) -> pd.DataFrame:
        """
        Get recent sleep predictions.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of predictions to return

        Returns:
            DataFrame with predictions and related info
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT sp.*, ar.filename, ar.duration_seconds, rs.session_type
                    FROM sleep_predictions sp
                    JOIN audio_recordings ar ON sp.recording_id = ar.recording_id
                    JOIN recording_sessions rs ON ar.session_id = rs.session_id
                    WHERE sp.created_at >= datetime('now', '-{} hours')
                    ORDER BY sp.created_at DESC
                    LIMIT ?
                '''.format(hours)

                df = pd.read_sql_query(query, conn, params=[limit])
                return df

        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            return pd.DataFrame()

    def get_sleep_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get sleep statistics over time period.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with sleep statistics
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT
                        COUNT(*) as total_predictions,
                        AVG(confidence_score) as avg_confidence,
                        predicted_stage,
                        COUNT(*) as stage_count
                    FROM sleep_predictions sp
                    JOIN audio_recordings ar ON sp.recording_id = ar.recording_id
                    WHERE sp.created_at >= datetime('now', '-{} days')
                    GROUP BY predicted_stage
                '''.format(days)

                df = pd.read_sql_query(query, conn)

                stats = {
                    'total_predictions': 0,
                    'avg_confidence': 0.0,
                    'stage_distribution': {},
                    'most_common_stage': 'Unknown'
                }

                if not df.empty:
                    stats['total_predictions'] = int(df['total_predictions'].sum())
                    stats['avg_confidence'] = float(df['avg_confidence'].mean())

                    # Create stage distribution
                    for _, row in df.iterrows():
                        stats['stage_distribution'][row['predicted_stage']] = int(row['stage_count'])

                    # Find most common stage
                    if stats['stage_distribution']:
                        stats['most_common_stage'] = max(stats['stage_distribution'].items(), key=lambda x: x[1])[0]

                return stats

        except Exception as e:
            logger.error(f"Error getting sleep statistics: {e}")
            return {}

    def export_session_data(self, session_id: str, output_path: str = None) -> Optional[str]:
        """
        Export all data for a session to JSON.

        Args:
            session_id: Session ID to export
            output_path: Output file path (auto-generated if None)

        Returns:
            Path to exported file or None if failed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get session info
                session_df = pd.read_sql_query(
                    "SELECT * FROM recording_sessions WHERE session_id = ?",
                    conn, params=[session_id]
                )

                if session_df.empty:
                    return None

                # Get recordings
                recordings_df = pd.read_sql_query(
                    "SELECT * FROM audio_recordings WHERE session_id = ?",
                    conn, params=[session_id]
                )

                # Get predictions
                predictions_query = '''
                    SELECT sp.*, ar.filename
                    FROM sleep_predictions sp
                    JOIN audio_recordings ar ON sp.recording_id = ar.recording_id
                    WHERE ar.session_id = ?
                '''
                predictions_df = pd.read_sql_query(predictions_query, conn, params=[session_id])

                # Build export data
                export_data = {
                    'session': session_df.to_dict('records')[0] if not session_df.empty else {},
                    'recordings': recordings_df.to_dict('records'),
                    'predictions': predictions_df.to_dict('records'),
                    'export_timestamp': datetime.now().isoformat()
                }

                # Generate output path if not provided
                if output_path is None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    output_path = f"data/exports/session_{session_id}_{timestamp}.json"

                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)

                return output_path

        except Exception as e:
            logger.error(f"Error exporting session data: {e}")
            return None

    def cleanup_old_sessions(self, days_old: int = 90) -> int:
        """
        Clean up old sessions and related data.

        Args:
            days_old: Age in days to delete

        Returns:
            Number of sessions cleaned up
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete old sessions
                cursor.execute('''
                    DELETE FROM recording_sessions
                    WHERE created_at < datetime('now', '-{} days')
                '''.format(days_old))

                deleted_count = cursor.rowcount
                conn.commit()

                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0

# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get or create global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager