# src/audio_processor.py
import os
import io
import base64
import numpy as np
import librosa
import soundfile as sf
from typing import Optional, Tuple, Dict, Any
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    """Real-time audio processing pipeline for sleep pattern analysis."""

    def __init__(self, sample_rate: int = 22050, chunk_duration: float = 5.0):
        """
        Initialize audio processor.

        Args:
            sample_rate: Target sample rate for audio processing
            chunk_duration: Duration in seconds for processing chunks
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_samples = int(sample_rate * chunk_duration)
        self.audio_buffer = []

    def process_audio_chunk(self, audio_chunk: np.ndarray) -> Dict[str, Any]:
        """
        Process a chunk of audio data and extract features.

        Args:
            audio_chunk: Audio data as numpy array

        Returns:
            Dictionary containing extracted features and metadata
        """
        try:
            # Ensure audio is mono
            if audio_chunk.ndim > 1:
                audio_chunk = librosa.to_mono(audio_chunk)

            # Resample if necessary
            if len(audio_chunk) < self.chunk_samples:
                # Pad if too short
                audio_chunk = np.pad(audio_chunk, (0, self.chunk_samples - len(audio_chunk)))
            elif len(audio_chunk) > self.chunk_samples:
                # Truncate if too long
                audio_chunk = audio_chunk[:self.chunk_samples]

            # Extract features
            features = self._extract_features(audio_chunk)

            return {
                'features': features,
                'timestamp': datetime.now().isoformat(),
                'duration': len(audio_chunk) / self.sample_rate,
                'sample_rate': self.sample_rate,
                'samples_processed': len(audio_chunk)
            }

        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return {
                'features': None,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _extract_features(self, audio: np.ndarray) -> Dict[str, float]:
        """Extract comprehensive audio features for sleep analysis."""
        features = {}

        try:
            # MFCC features
            mfccs = librosa.feature.mfcc(y=audio, sr=self.sample_rate, n_mfcc=13)
            for i in range(13):
                features[f'mfcc_{i}'] = np.mean(mfccs[i])
                features[f'mfcc_{i}_std'] = np.std(mfccs[i])

            # Spectral features
            features['zero_crossing_rate'] = np.mean(librosa.feature.zero_crossing_rate(audio))
            features['spectral_centroid'] = np.mean(librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate))
            features['spectral_bandwidth'] = np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=self.sample_rate))
            features['spectral_rolloff'] = np.mean(librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate))
            features['spectral_flatness'] = np.mean(librosa.feature.spectral_flatness(y=audio))

            # Energy and RMS
            features['rms'] = np.mean(librosa.feature.rms(y=audio))
            features['energy'] = np.sum(audio ** 2)

            # Tonnetz (harmonic content)
            tonnetz = librosa.feature.tonnetz(y=audio, sr=self.sample_rate)
            for i in range(tonnetz.shape[0]):
                features[f'tonnetz_{i}'] = np.mean(tonnetz[i])

            # Chroma features
            chroma = librosa.feature.chroma(y=audio, sr=self.sample_rate)
            for i in range(chroma.shape[0]):
                features[f'chroma_{i}'] = np.mean(chroma[i])

            # Tempo and rhythm features
            tempo, beats = librosa.beat.beat_track(y=audio, sr=self.sample_rate)
            features['tempo'] = tempo
            features['beat_count'] = len(beats)

            # Additional spectral contrast
            contrast = librosa.feature.spectral_contrast(y=audio, sr=self.sample_rate)
            for i in range(contrast.shape[0]):
                features[f'spectral_contrast_{i}'] = np.mean(contrast[i])

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return empty features if extraction fails
            return {}

        return features

    def process_base64_audio(self, base64_data: str) -> Optional[Tuple[np.ndarray, int]]:
        """
        Convert base64 audio data to numpy array.

        Args:
            base64_data: Base64 encoded audio data

        Returns:
            Tuple of (audio_array, sample_rate) or None if failed
        """
        try:
            # Decode base64
            audio_bytes = base64.b64decode(base64_data)

            # Create in-memory file
            audio_io = io.BytesIO(audio_bytes)

            # Load with librosa
            audio, sr = librosa.load(audio_io, sr=self.sample_rate)

            return audio, sr

        except Exception as e:
            logger.error(f"Error processing base64 audio: {e}")
            return None

    def save_audio_chunk(self, audio_chunk: np.ndarray, filename: str, output_dir: str = "data/recordings") -> Optional[str]:
        """
        Save audio chunk to file.

        Args:
            audio_chunk: Audio data as numpy array
            filename: Output filename
            output_dir: Directory to save to

        Returns:
            Path to saved file or None if failed
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)

            # Save using soundfile
            sf.write(filepath, audio_chunk, self.sample_rate)

            return filepath

        except Exception as e:
            logger.error(f"Error saving audio chunk: {e}")
            return None

    def add_to_buffer(self, audio_chunk: np.ndarray) -> bool:
        """
        Add audio chunk to internal buffer.

        Args:
            audio_chunk: Audio data to add to buffer

        Returns:
            True if buffer is ready for processing, False otherwise
        """
        self.audio_buffer.append(audio_chunk)

        # Check if buffer has enough data
        total_samples = sum(len(chunk) for chunk in self.audio_buffer)
        return total_samples >= self.chunk_samples

    def get_buffered_audio(self) -> Optional[np.ndarray]:
        """
        Get concatenated audio from buffer and clear buffer.

        Returns:
            Concatenated audio array or None if buffer is empty
        """
        if not self.audio_buffer:
            return None

        try:
            # Concatenate all chunks
            full_audio = np.concatenate(self.audio_buffer)

            # Clear buffer
            self.audio_buffer = []

            return full_audio

        except Exception as e:
            logger.error(f"Error getting buffered audio: {e}")
            self.audio_buffer = []
            return None

    def clear_buffer(self):
        """Clear the internal audio buffer."""
        self.audio_buffer = []

class StreamingAudioProcessor:
    """Enhanced processor for real-time streaming audio analysis."""

    def __init__(self, processor: AudioProcessor):
        self.processor = processor
        self.processing_queue = []
        self.results_history = []
        self.is_processing = False

    def add_stream_chunk(self, audio_chunk: np.ndarray) -> bool:
        """
        Add streaming audio chunk for processing.

        Args:
            audio_chunk: Audio chunk from stream

        Returns:
            True if chunk was added successfully
        """
        return self.processor.add_to_buffer(audio_chunk)

    def process_buffer(self) -> Optional[Dict[str, Any]]:
        """
        Process current buffer if ready.

        Returns:
            Processing result or None if buffer not ready
        """
        if not self.processor.add_to_buffer(np.array([])):  # Check buffer status
            return None

        audio_data = self.processor.get_buffered_audio()
        if audio_data is None:
            return None

        result = self.processor.process_audio_chunk(audio_data)
        if 'error' not in result:
            self.results_history.append(result)

        return result

    def get_recent_results(self, count: int = 5) -> list:
        """Get the most recent processing results."""
        return self.results_history[-count:]

    def clear_history(self):
        """Clear processing history."""
        self.results_history = []

# Global processor instance
_audio_processor = None
_streaming_processor = None

def get_audio_processor() -> AudioProcessor:
    """Get or create global audio processor instance."""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor

def get_streaming_processor() -> StreamingAudioProcessor:
    """Get or create global streaming processor instance."""
    global _streaming_processor
    if _streaming_processor is None:
        _streaming_processor = StreamingAudioProcessor(get_audio_processor())
    return _streaming_processor

def validate_audio_data(audio_data: np.ndarray) -> Tuple[bool, str]:
    """
    Validate audio data for processing.

    Args:
        audio_data: Audio array to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if audio_data is None or len(audio_data) == 0:
        return False, "Audio data is empty"

    if len(audio_data) < 1000:  # Very short audio
        return False, "Audio duration too short (< 0.05s)"

    if np.all(audio_data == 0):  # Silent audio
        return False, "Audio contains only silence"

    if np.max(np.abs(audio_data)) > 1.0:  # Clipping
        return False, "Audio may be clipped (values > 1.0)"

    return True, ""