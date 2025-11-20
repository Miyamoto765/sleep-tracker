# app/views/realtime.py
import os
import time
import base64
import io
import streamlit as st
import numpy as np
import pandas as pd
import joblib
import librosa
import matplotlib.pyplot as plt
from datetime import datetime
from src.feature_extraction import extract_features
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../python'))
try:
    from sensor_manager import SensorManager
except ImportError:
    SensorManager = None

# Configuration
MODEL_PATH = "models/rf_model.joblib"
SCALER_PATH = "models/scaler.joblib"
META_PATH = "models/meta_feature_cols.joblib"
RECORDINGS_DIR = "data/recordings"
HISTORY_CSV = "data/realtime_history.csv"

# Ensure directories exist
os.makedirs(RECORDINGS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(HISTORY_CSV), exist_ok=True)

@st.cache_resource
def load_model():
    """Load the trained sleep prediction model and related components."""
    try:
        model = joblib.load(MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        meta = joblib.load(META_PATH)
        return model, scaler, meta.get("feature_columns", None)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None, None

def save_realtime_recording(audio_data, filename, prediction, confidence):
    """Save recording data and results to history."""
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "filename": filename,
        "prediction": prediction,
        "confidence": confidence,
        "recording_type": "realtime"
    }

    df_row = pd.DataFrame([row])
    if not os.path.exists(HISTORY_CSV):
        df_row.to_csv(HISTORY_CSV, index=False)
    else:
        df_row.to_csv(HISTORY_CSV, mode="a", header=False, index=False)

def map_prediction_to_label(pred):
    """Map numerical prediction to sleep stage labels."""
    if pd.isna(pred):
        return "Unknown"
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

def audio_recorder_component():
    """Custom audio recorder component using JavaScript."""
    # HTML for audio recording with Web Audio API
    audio_recorder_html = """
    <div id="audio-recorder" style="padding: 20px; border: 2px dashed #4CAF50; border-radius: 10px; text-align: center; background-color: rgba(76, 175, 80, 0.1);">
        <h3>🎤 Real-time Audio Recorder</h3>
        <button id="startRecord" style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer;">Start Recording</button>
        <button id="stopRecord" style="background-color: #f44336; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer; disabled;">Stop Recording</button>
        <button id="pauseRecord" style="background-color: #ff9800; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer; disabled;">Pause Recording</button>
        <button id="resumeRecord" style="background-color: #2196F3; color: white; padding: 10px 20px; border: none; border-radius: 5px; margin: 5px; cursor: pointer; disabled;">Resume Recording</button>

        <div id="recordingStatus" style="margin-top: 10px; font-weight: bold;"></div>
        <div id="audioVisualization" style="margin-top: 15px; height: 100px; background-color: rgba(255,255,255,0.1); border-radius: 5px; position: relative;">
            <canvas id="waveformCanvas" width="100%" height="100" style="width: 100%; height: 100%;"></canvas>
        </div>
        <audio id="audioPlayback" controls style="width: 100%; margin-top: 10px; display: none;"></audio>
    </div>

    <script>
    (function() {
        let mediaRecorder;
        let audioChunks = [];
        let audioContext;
        let analyser;
        let microphone;
        let javascriptNode;
        let recordingStartTime;
        let isPaused = false;
        let animationId;

        const startBtn = document.getElementById('startRecord');
        const stopBtn = document.getElementById('stopRecord');
        const pauseBtn = document.getElementById('pauseRecord');
        const resumeBtn = document.getElementById('resumeRecord');
        const statusDiv = document.getElementById('recordingStatus');
        const audioElement = document.getElementById('audioPlayback');
        const canvas = document.getElementById('waveformCanvas');
        const canvasCtx = canvas.getContext('2d');

        // Set canvas size
        function resizeCanvas() {
            canvas.width = canvas.offsetWidth;
            canvas.height = 100;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        function updateStatus(message, color = '#4CAF50') {
            statusDiv.innerHTML = `<span style="color: ${color};">${message}</span>`;
        }

        function drawWaveform() {
            if (!analyser) return;

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            function draw() {
                if (!isPaused && mediaRecorder && mediaRecorder.state === 'recording') {
                    animationId = requestAnimationFrame(draw);

                    analyser.getByteTimeDomainData(dataArray);

                    canvasCtx.fillStyle = 'rgba(255,255,255,0.1)';
                    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

                    canvasCtx.lineWidth = 2;
                    canvasCtx.strokeStyle = '#4CAF50';
                    canvasCtx.beginPath();

                    const sliceWidth = canvas.width * 1.0 / bufferLength;
                    let x = 0;

                    for(let i = 0; i < bufferLength; i++) {
                        const v = dataArray[i] / 128.0;
                        const y = v * canvas.height / 2;

                        if(i === 0) {
                            canvasCtx.moveTo(x, y);
                        } else {
                            canvasCtx.lineTo(x, y);
                        }

                        x += sliceWidth;
                    }

                    canvasCtx.lineTo(canvas.width, canvas.height / 2);
                    canvasCtx.stroke();
                }
            }
            draw();
        }

        function startRecording() {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioContext.createAnalyser();
                    microphone = audioContext.createMediaStreamSource(stream);
                    javascriptNode = audioContext.createScriptProcessor(2048, 1, 1);

                    analyser.smoothingTimeConstant = 0.8;
                    analyser.fftSize = 1024;

                    microphone.connect(analyser);
                    analyser.connect(javascriptNode);
                    javascriptNode.connect(audioContext.destination);

                    mediaRecorder = new MediaRecorder(stream);
                    audioChunks = [];
                    recordingStartTime = Date.now();

                    mediaRecorder.ondataavailable = event => {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const audioUrl = URL.createObjectURL(audioBlob);
                        audioElement.src = audioUrl;
                        audioElement.style.display = 'block';

                        // Convert to base64 and send to Streamlit
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64data = reader.result.split(',')[1];
                            window.parent.postMessage({
                                type: 'streamlit:setComponentValue',
                                key: 'audio_data',
                                value: base64data
                            }, '*');
                        };
                        reader.readAsDataURL(audioBlob);

                        // Stop all tracks
                        stream.getTracks().forEach(track => track.stop());

                        // Cleanup audio nodes
                        microphone.disconnect();
                        analyser.disconnect();
                        javascriptNode.disconnect();
                        audioContext.close();
                    };

                    mediaRecorder.start();
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                    pauseBtn.disabled = false;

                    updateStatus('🔴 Recording... Speak clearly into your microphone', '#f44336');
                    drawWaveform();

                    // Update recording duration
                    const durationInterval = setInterval(() => {
                        if (mediaRecorder && mediaRecorder.state === 'recording' && !isPaused) {
                            const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                            updateStatus(`🔴 Recording... ${duration}s - Speak clearly into your microphone`, '#f44336');
                        } else {
                            clearInterval(durationInterval);
                        }
                    }, 1000);
                })
                .catch(err => {
                    console.error('Error accessing microphone:', err);
                    updateStatus('❌ Error: Microphone access denied. Please allow microphone permissions.', '#f44336');
                });
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
                startBtn.disabled = false;
                stopBtn.disabled = true;
                pauseBtn.disabled = true;
                resumeBtn.disabled = true;
                isPaused = false;
                updateStatus('⏹️ Recording stopped. Processing...', '#ff9800');
            }
        }

        function pauseRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording' && !isPaused) {
                mediaRecorder.pause();
                isPaused = true;
                pauseBtn.disabled = true;
                resumeBtn.disabled = false;
                updateStatus('⏸️ Recording paused', '#ff9800');
            }
        }

        function resumeRecording() {
            if (mediaRecorder && mediaRecorder.state === 'paused' && isPaused) {
                mediaRecorder.resume();
                isPaused = false;
                pauseBtn.disabled = false;
                resumeBtn.disabled = true;
                updateStatus('🔴 Recording resumed', '#4CAF50');
                drawWaveform();
            }
        }

        // Event listeners
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        pauseBtn.addEventListener('click', pauseRecording);
        resumeBtn.addEventListener('click', resumeRecording);
    })();
    </script>
    """

    return audio_recorder_html

def display_realtime_history():
    """Display recent real-time recording history in sidebar."""
    st.sidebar.header("🎤 Real-time History")
    if os.path.exists(HISTORY_CSV):
        df_hist = pd.read_csv(HISTORY_CSV)
        if df_hist.shape[0] == 0:
            st.sidebar.info("No real-time recordings yet.")
            return
        recent = df_hist.sort_values("timestamp", ascending=False).head(5)
        for _, r in recent.iterrows():
            ts = r.get("timestamp")
            pred = r.get("prediction", "")
            conf = r.get("confidence", "")
            st.sidebar.write(f"**{pred}** ({conf}%)")
            st.sidebar.caption(str(ts))
    else:
        st.sidebar.info("No real-time recordings yet. Start recording to see history.")

def process_audio_data(audio_base64, model, scaler, feature_cols):
    """Process base64 audio data and predict sleep stage."""
    try:
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64)

        # Save to temporary file
        temp_filename = f"realtime_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        temp_path = os.path.join(RECORDINGS_DIR, temp_filename)

        with open(temp_path, "wb") as f:
            f.write(audio_bytes)

        # Extract features
        features = extract_features(temp_path)

        if features is None:
            return None, None, None, None

        # Align to feature columns
        if isinstance(features, (list, np.ndarray)) and feature_cols:
            row_feats = list(features)[:len(feature_cols)]
        elif isinstance(features, dict) and feature_cols:
            row_feats = [features.get(c, np.nan) for c in feature_cols]
        else:
            row_feats = list(features) if isinstance(features, (list, np.ndarray)) else list(features.values())

        X_df = pd.DataFrame([row_feats], columns=feature_cols) if feature_cols else pd.DataFrame([row_feats])
        Xs = scaler.transform(X_df)
        pred_raw = model.predict(Xs)[0]

        # Calculate confidence
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(Xs)[0]
            confidence = float(proba.max() * 100)
        else:
            confidence = 50.0

        label = map_prediction_to_label(pred_raw)

        return temp_path, temp_filename, label, confidence

    except Exception as e:
        st.error(f"Error processing audio: {e}")
        return None, None, None, None

def render():
    """Render the real-time recording page."""
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 🎤 Real-time Sleep Pattern Analysis")
    st.markdown("Record your audio directly in the browser for instant sleep pattern analysis.")

    # Load model
    model, scaler, feature_cols = load_model()
    if model is None:
        st.error("Unable to load prediction model. Please check model files.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    display_realtime_history()

    # Sensor Connection Section
    st.markdown("### 🔌 Sensor Connection Status")
    
    # Initialize sensor manager in session state
    if 'sensor_manager' not in st.session_state:
        if SensorManager:
            st.session_state.sensor_manager = SensorManager()
        else:
            st.session_state.sensor_manager = None
    
    sensor_manager = st.session_state.sensor_manager
    
    if sensor_manager is None:
        st.warning("⚠️ Sensor Manager not available. Please ensure pyserial is installed: `pip install pyserial`")
    else:
        # Scan for available ports
        with st.expander("🔍 Scan & Connect Sensors", expanded=True):
            # Single-column layout — Arduino UNO only
            col1 = st.columns(1)[0]
            
            with col1:
                st.subheader("Arduino UNO")
                st.caption("Sensors: MAX30102 (PPG), MPU6050 (Motion), MAX4466 (Sound Level)")
                
                if st.button("🔍 Scan Ports", key="scan_arduino"):
                    ports = sensor_manager.scan_ports()
                    if ports:
                        st.session_state.arduino_ports = [p['device'] for p in ports]
                        st.session_state.arduino_port_info = {p['device']: p['description'] for p in ports}
                    else:
                        st.warning("No serial ports found")
                
                if 'arduino_ports' in st.session_state and st.session_state.arduino_ports:
                    selected_arduino = st.selectbox(
                        "Select Arduino Port:",
                        options=st.session_state.arduino_ports,
                        key="arduino_port_select",
                        format_func=lambda x: f"{x} - {st.session_state.arduino_port_info.get(x, 'Unknown')}"
                    )
                    
                    col_conn1, col_conn2 = st.columns(2)
                    with col_conn1:
                        if st.button("🔌 Connect Arduino", key="connect_arduino"):
                            if sensor_manager.connect_arduino(selected_arduino):
                                st.success(f"Connected to {selected_arduino}")
                                sensor_manager.start()
                                st.rerun()
                            else:
                                st.error("Failed to connect")
                    
                    with col_conn2:
                        if st.button("❌ Disconnect Arduino", key="disconnect_arduino"):
                            sensor_manager.stop()
                                st.success("Disconnected")
                                st.rerun()
        
        # Sensor Status Display
        st.markdown("#### 📊 Sensor Status")
        
        if sensor_manager:
            sensor_status = sensor_manager.get_sensor_status()
            latest_data = sensor_manager.get_latest_data()
            
            # Create status cards (UNO sensors only)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                max30102_status = sensor_status['MAX30102']['connected']
                status_color = "🟢" if max30102_status else "🔴"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 24px; text-align: center;">{status_color}</div>
                    <div style="text-align: center; font-weight: 600;">MAX30102</div>
                    <div style="text-align: center; font-size: 12px; color: #aaa;">PPG Sensor</div>
                    <div style="text-align: center; margin-top: 8px;">
                        <span style="color: {'#4CAF50' if max30102_status else '#f44336'};">
                            {'Connected' if max30102_status else 'Disconnected'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if max30102_status and latest_data['ppg']['bpm'] > 0:
                    st.caption(f"BPM: {int(latest_data['ppg']['beat_avg'])}")
            
            with col2:
                mpu6050_status = sensor_status['MPU6050']['connected']
                status_color = "🟢" if mpu6050_status else "🔴"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 24px; text-align: center;">{status_color}</div>
                    <div style="text-align: center; font-weight: 600;">MPU6050</div>
                    <div style="text-align: center; font-size: 12px; color: #aaa;">Motion Sensor</div>
                    <div style="text-align: center; margin-top: 8px;">
                        <span style="color: {'#4CAF50' if mpu6050_status else '#f44336'};">
                            {'Connected' if mpu6050_status else 'Disconnected'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if mpu6050_status:
                    motion = np.sqrt(latest_data['motion']['accel_x']**2 + 
                                   latest_data['motion']['accel_y']**2 + 
                                   latest_data['motion']['accel_z']**2)
                    st.caption(f"Motion: {motion:.2f} g")
            
            with col3:
                mic_status = sensor_status['MAX4466']['connected']
                status_color = "🟢" if mic_status else "🔴"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 24px; text-align: center;">{status_color}</div>
                    <div style="text-align: center; font-weight: 600;">MAX4466</div>
                    <div style="text-align: center; font-size: 12px; color: #aaa;">Sound Level Mic</div>
                    <div style="text-align: center; margin-top: 8px;">
                        <span style="color: {'#4CAF50' if mic_status else '#f44336'};">
                            {'Connected' if mic_status else 'Disconnected'}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Show sensor data if connected
            if any(status['connected'] for status in sensor_status.values()):
                st.markdown("---")
                st.markdown("#### 📈 Live Sensor Data")
                
                data_col1, data_col2 = st.columns(2)
                
                with data_col1:
                    if max30102_status:
                        st.markdown("**PPG Sensor (MAX30102)**")
                        st.metric("Heart Rate", f"{int(latest_data['ppg']['beat_avg'])} BPM" if latest_data['ppg']['beat_avg'] > 0 else "N/A")
                        st.metric("IR Value", f"{latest_data['ppg']['ir']:,}")
                        st.metric("Red Value", f"{latest_data['ppg']['red']:,}")
                
                with data_col2:
                    if mpu6050_status:
                        st.markdown("**Motion Sensor (MPU6050)**")
                        st.metric("Temperature", f"{latest_data['motion']['temp']:.1f}°C")
                        st.metric("Accel X", f"{latest_data['motion']['accel_x']:.2f} g")
                        st.metric("Accel Y", f"{latest_data['motion']['accel_y']:.2f} g")
                        st.metric("Accel Z", f"{latest_data['motion']['accel_z']:.2f} g")
        
        st.markdown("---")

    # Live Recording Section (no upload tab - upload is in navigation)
    st.markdown("### 🎤 Browser Microphone Recording")
    st.markdown("Click 'Start Recording' to begin capturing audio from your microphone for real-time sleep pattern analysis.")

    # Control Arduino recording if connected
    if sensor_manager and sensor_manager.arduino_serial and sensor_manager.arduino_serial.is_open:
        rec_col1, rec_col2 = st.columns(2)
        with rec_col1:
            if st.button("🔴 Start Arduino Recording", key="start_arduino_rec"):
                if sensor_manager.start_recording():
                    st.success("Arduino recording started - OLED will show recording status")
                else:
                    st.error("Failed to start Arduino recording")
        with rec_col2:
            if st.button("⏹️ Stop Arduino Recording", key="stop_arduino_rec"):
                if sensor_manager.stop_recording():
                    st.success("Arduino recording stopped")
                else:
                    st.error("Failed to stop Arduino recording")

    # Render audio recorder component
    st.components.v1.html(audio_recorder_component(), height=300)

    # Get audio data from component
    audio_data = st.session_state.get('audio_data', None)
    
    # Auto-start Arduino recording when browser recording starts
    if audio_data and sensor_manager:
        if sensor_manager.arduino_serial and sensor_manager.arduino_serial.is_open:
            sensor_manager.start_recording()

    if audio_data:
        st.success("Audio recorded successfully! Processing...")

        with st.spinner("Analyzing audio for sleep patterns..."):
            temp_path, filename, prediction, confidence = process_audio_data(
                audio_data, model, scaler, feature_cols
            )

            if prediction:
                # Display results
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Predicted Sleep Stage", prediction)
                with col2:
                    st.metric("Confidence", f"{int(confidence)}%")

                # Sleep score visualization
                st.markdown("### 🧠 Sleep Analysis Results")

                # Create gauge chart for confidence
                fig, ax = plt.subplots(figsize=(8, 3))
                ax.barh([0], [confidence], height=0.3, color='#4CAF50', alpha=0.7)
                ax.set_xlim(0, 100)
                ax.set_xlabel('Confidence Score (%)')
                ax.set_title(f'Stage Prediction Confidence: {prediction}')
                ax.set_yticks([])
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)

                # Audio playback
                if temp_path and os.path.exists(temp_path):
                    st.markdown("### 🎶 Your Recording")
                    st.audio(temp_path)

                    # Save to history
                    save_realtime_recording(audio_data, filename, prediction, confidence)

                    # Clear audio data from session
                    if 'audio_data' in st.session_state:
                        del st.session_state['audio_data']

            else:
                st.error("Failed to process audio. Please try recording again.")

    # Add tips section
    with st.expander("💡 Tips for Best Results"):
        st.markdown("""
        - **Environment**: Record in a quiet environment for better accuracy
        - **Duration**: Record for 15-60 seconds for optimal analysis
        - **Distance**: Keep your device 6-12 inches from your mouth
        - **Speaking**: Speak naturally or record breathing/snoring patterns
        - **Consistency**: Try to record at the same time each night
        """)

    st.markdown('</div>', unsafe_allow_html=True)