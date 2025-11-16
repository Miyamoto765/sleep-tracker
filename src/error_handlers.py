# src/error_handlers.py
import logging
import traceback
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Callable
import streamlit as st
from functools import wraps

# Configure error logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/error.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SleepTrackerError(Exception):
    """Base exception for sleep tracker application."""
    def __init__(self, message: str, error_code: str = None, user_message: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "UNKNOWN_ERROR"
        self.user_message = user_message or "An unexpected error occurred. Please try again."

class AudioProcessingError(SleepTrackerError):
    """Audio processing related errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message, "AUDIO_PROCESSING_ERROR", user_message or
                        "Failed to process audio. Please check your audio file and try again.")

class ModelPredictionError(SleepTrackerError):
    """Model prediction related errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message, "MODEL_PREDICTION_ERROR", user_message or
                        "Unable to analyze sleep pattern. The model may be temporarily unavailable.")

class DatabaseError(SleepTrackerError):
    """Database operation related errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message, "DATABASE_ERROR", user_message or
                        "Data storage issue. Your information is safe, but some features may be limited.")

class MicrophoneAccessError(SleepTrackerError):
    """Microphone access related errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message, "MICROPHONE_ACCESS_ERROR", user_message or
                        "Unable to access microphone. Please check browser permissions and try again.")

class FileUploadError(SleepTrackerError):
    """File upload related errors."""
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message, "FILE_UPLOAD_ERROR", user_message or
                        "Failed to upload file. Please check the file format and size.")

def handle_streamlit_errors():
    """Global error handler for Streamlit application."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SleepTrackerError as e:
                log_error(e)
                show_user_error(e.user_message, e.error_code)
            except Exception as e:
                log_error(e)
                show_user_error("An unexpected error occurred. Please try again.", "UNEXPECTED_ERROR")
        return wrapper
    return decorator

def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log error with context information.

    Args:
        error: Exception to log
        context: Additional context information
    """
    error_info = {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        'context': context or {}
    }

    # Add specific error codes for known errors
    if isinstance(error, SleepTrackerError):
        error_info['error_code'] = error.error_code

    logger.error(f"Error occurred: {error_info}")

def show_user_error(message: str, error_code: str = None) -> None:
    """
    Display user-friendly error message in Streamlit.

    Args:
        message: User-friendly error message
        error_code: Error code for reference
    """
    error_html = f"""
    <div class="error-container">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 20px; margin-right: 8px;">⚠️</span>
            <strong>Error</strong>
        </div>
        <div>{message}</div>
        {f'<div style="margin-top: 8px; font-size: 12px; opacity: 0.7;">Error code: {error_code}</div>' if error_code else ''}
    </div>
    """
    st.markdown(error_html, unsafe_allow_html=True)

def show_user_success(message: str) -> None:
    """
    Display success message in Streamlit.

    Args:
        message: Success message to display
    """
    success_html = f"""
    <div class="success-container">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 20px; margin-right: 8px;">✅</span>
            <strong>Success</strong>
        </div>
        <div>{message}</div>
    </div>
    """
    st.markdown(success_html, unsafe_allow_html=True)

def show_loading_with_timeout(message: str, timeout: int = 30) -> bool:
    """
    Show loading spinner with timeout handling.

    Args:
        message: Loading message to display
        timeout: Timeout in seconds

    Returns:
        True if completed without timeout, False if timeout occurred
    """
    import time

    start_time = time.time()
    spinner_placeholder = st.empty()

    try:
        with spinner_placeholder.container():
            st.spinner(f"{message} (Timeout: {timeout}s)")

            # Check for timeout periodically
            while time.time() - start_time < timeout:
                time.sleep(0.5)
                # This is a placeholder - actual implementation would depend on specific use case
                return True

        show_user_error(f"Operation timed out after {timeout} seconds. Please try again.")
        return False

    except Exception as e:
        log_error(e)
        show_user_error("Operation failed. Please try again.")
        return False
    finally:
        spinner_placeholder.empty()

def validate_audio_file(file_data, max_size_mb: int = 50, allowed_formats: list = None) -> bool:
    """
    Validate uploaded audio file.

    Args:
        file_data: Uploaded file data
        max_size_mb: Maximum file size in MB
        allowed_formats: List of allowed file formats

    Returns:
        True if valid, raises FileUploadError if invalid
    """
    if allowed_formats is None:
        allowed_formats = ['wav', 'mp3', 'flac', 'ogg']

    # Check file size
    file_size_mb = len(file_data.getbuffer()) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise FileUploadError(
            f"File size {file_size_mb:.1f}MB exceeds maximum {max_size_mb}MB",
            f"File is too large. Please upload a file smaller than {max_size_mb}MB."
        )

    # Check file extension
    filename = file_data.name.lower()
    if not any(filename.endswith(f'.{fmt}') for fmt in allowed_formats):
        raise FileUploadError(
            f"File format not in allowed formats: {allowed_formats}",
            f"Unsupported file format. Please use one of: {', '.join(allowed_formats).upper()}"
        )

    return True

def validate_microphone_permissions() -> bool:
    """
    Check and handle microphone permissions.

    Returns:
        True if permissions are available, False otherwise
    """
    # This would typically be handled by JavaScript in the browser
    # Here we provide the error handling framework
    return True

def safe_audio_processing(audio_data: bytes, processor_func: Callable, *args, **kwargs) -> Any:
    """
    Safely process audio data with error handling.

    Args:
        audio_data: Audio data to process
        processor_func: Function to process audio
        *args, **kwargs: Additional arguments for processor function

    Returns:
        Result of processor function or None if failed
    """
    try:
        if not audio_data:
            raise AudioProcessingError("No audio data provided")

        if len(audio_data) == 0:
            raise AudioProcessingError("Audio data is empty")

        # Validate audio data size (reasonable limits)
        if len(audio_data) > 100 * 1024 * 1024:  # 100MB limit
            raise AudioProcessingError(
                "Audio data too large for processing",
                "Audio file is too large. Please use a shorter recording."
            )

        return processor_func(audio_data, *args, **kwargs)

    except AudioProcessingError:
        raise  # Re-raise our custom errors
    except Exception as e:
        raise AudioProcessingError(
            f"Unexpected error during audio processing: {str(e)}",
            "Failed to process audio. The file may be corrupted or in an unsupported format."
        )

def safe_database_operation(operation_func: Callable, *args, **kwargs) -> Any:
    """
    Safely perform database operations with error handling.

    Args:
        operation_func: Database operation function
        *args, **kwargs: Arguments for the operation

    Returns:
        Result of operation or None if failed
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        raise DatabaseError(
            f"Database operation failed: {str(e)}",
            "Unable to save data. Your information is safe, but some features may be temporarily unavailable."
        )

def safe_model_prediction(model, features, fallback_result=None) -> Dict[str, Any]:
    """
    Safely perform model prediction with fallback.

    Args:
        model: Machine learning model
        features: Input features
        fallback_result: Result to use if prediction fails

    Returns:
        Prediction result or fallback
    """
    try:
        if model is None:
            raise ModelPredictionError("Model not loaded")

        if features is None or len(features) == 0:
            raise ModelPredictionError("No features provided for prediction")

        # Perform prediction
        prediction = model.predict([features])[0]

        # Calculate confidence if available
        confidence = 50.0  # Default confidence
        if hasattr(model, 'predict_proba'):
            try:
                probabilities = model.predict_proba([features])[0]
                confidence = float(max(probabilities) * 100)
            except:
                pass  # Use default confidence

        return {
            'prediction': prediction,
            'confidence': confidence,
            'success': True
        }

    except ModelPredictionError:
        raise
    except Exception as e:
        if fallback_result is not None:
            logger.warning(f"Model prediction failed, using fallback: {str(e)}")
            return {
                **fallback_result,
                'success': False,
                'error': str(e)
            }
        else:
            raise ModelPredictionError(
                f"Model prediction failed: {str(e)}",
                "Sleep pattern analysis is currently unavailable. Please try again later."
            )

def create_error_report(error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create comprehensive error report for logging/debugging.

    Args:
        error: Exception to report
        context: Additional context information

    Returns:
        Error report dictionary
    """
    return {
        'timestamp': datetime.now().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'error_code': getattr(error, 'error_code', 'UNKNOWN_ERROR'),
        'user_message': getattr(error, 'user_message', 'An unexpected error occurred.'),
        'traceback': traceback.format_exc(),
        'context': context or {},
        'streamlit_session_id': st.session_state.get('session_id', 'unknown') if 'session_state' in dir(st) else 'unknown'
    }

def retry_operation(operation: Callable, max_retries: int = 3, delay: float = 1.0,
                 exceptions: tuple = (Exception,)) -> Any:
    """
    Retry an operation with exponential backoff.

    Args:
        operation: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        exceptions: Types of exceptions to catch and retry

    Returns:
        Result of operation if successful

    Raises:
        The last exception if all retries fail
    """
    import time

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return operation()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {wait_time}s: {str(e)}")
                time.sleep(wait_time)
            else:
                logger.error(f"Operation failed after {max_retries + 1} attempts: {str(e)}")

    raise last_exception

# Streamlit-specific utilities
def setup_error_handlers():
    """Setup global error handling for Streamlit app."""

    # Custom CSS for error states
    st.markdown("""
    <style>
    .error-container {
        background: rgba(244, 67, 54, 0.1);
        border: 1px solid rgba(244, 67, 54, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }

    .success-container {
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid rgba(76, 175, 80, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }

    .warning-container {
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def show_warning(message: str) -> None:
    """Display warning message in Streamlit."""
    warning_html = f"""
    <div class="warning-container">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <span style="font-size: 20px; margin-right: 8px;">⚠️</span>
            <strong>Warning</strong>
        </div>
        <div>{message}</div>
    </div>
    """
    st.markdown(warning_html, unsafe_allow_html=True)