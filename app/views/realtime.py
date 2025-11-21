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

# Import safe_rerun from ui module
from app.ui import safe_rerun

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

                    updateStatus('🔴 Recording...', '#f44336');
                    drawWaveform();

                    // Update recording duration
                    const durationInterval = setInterval(() => {
                        if (mediaRecorder && mediaRecorder.state === 'recording' && !isPaused) {
                            const duration = Math.floor((Date.now() - recordingStartTime) / 1000);
                            updateStatus(`🔴 Recording... ${duration}s`, '#f44336');
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
                            with st.spinner("Connecting to Arduino..."):
                                success, error_msg = sensor_manager.connect_arduino(selected_arduino)
                                if success:
                                    st.success(f"Connected to {selected_arduino}")
                                    # Start reading thread
                                    sensor_manager.start()
                                    # Small delay to ensure status is read
                                    time.sleep(0.3)
                                    safe_rerun()
                                else:
                                    st.error(f"❌ Connection failed: {error_msg}")
                                    st.info("💡 **Troubleshooting tips:**\n"
                                           "- Make sure the Arduino is plugged in\n"
                                           "- Check if another program is using the port\n"
                                           "- Try unplugging and replugging the Arduino\n"
                                           "- Verify the correct port is selected")
                    
                    with col_conn2:
                        if st.button("❌ Disconnect Arduino", key="disconnect_arduino"):
                            sensor_manager.stop()
                            st.success("Disconnected")
                            safe_rerun()
        
        # Sensor Status Display
        st.markdown("#### 📊 Sensor Status")
        
        if sensor_manager:
            # Check if reading thread is running
            if sensor_manager.arduino_serial and sensor_manager.arduino_serial.is_open:
                if not sensor_manager.running:
                    # Thread not running, start it
                    sensor_manager.start()
            
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
                
                # Real-time update indicator
                update_indicator_col1, update_indicator_col2 = st.columns([3, 1])
                with update_indicator_col1:
                    st.markdown("#### 📈 Live Sensor Data (Arduino UNO)")
                with update_indicator_col2:
                    current_time = datetime.now().strftime("%H:%M:%S")
                    # Check if we have recent data
                    has_recent_data = any(
                        status['last_update'] and 
                        (datetime.now() - status['last_update']).total_seconds() < 5
                        for status in sensor_status.values()
                    )
                    status_icon = "🟢" if has_recent_data else "🟡"
                    st.caption(f"{status_icon} Last update: {current_time}")
                    
                    # Debug info
                    if sensor_manager.arduino_serial and sensor_manager.arduino_serial.is_open:
                        if sensor_manager.running:
                            st.caption("✅ Reading thread active")
                        else:
                            st.caption("⚠️ Reading thread not running")
                            if st.button("🔄 Restart Reading Thread", key="restart_thread"):
                                sensor_manager.start()
                                safe_rerun()
                        
                        # Show buffer status
                        try:
                            bytes_waiting = sensor_manager.arduino_serial.in_waiting
                            if bytes_waiting > 0:
                                st.caption(f"📊 {bytes_waiting} bytes waiting in buffer")
                            else:
                                st.caption("📊 No data in buffer")
                        except:
                            pass
                        
                        # Test data reception
                        if st.button("🔍 Test Data Reception", key="test_data"):
                            try:
                                if sensor_manager.arduino_serial.in_waiting > 0:
                                    test_line = sensor_manager.arduino_serial.readline().decode('utf-8', errors='ignore').strip()
                                    st.success(f"✅ Data received: {test_line[:100]}")
                                else:
                                    st.warning("⚠️ No data waiting in buffer. Make sure Arduino is sending data.")
                            except Exception as e:
                                st.error(f"❌ Error reading: {str(e)}")
                
                
                data_col1, data_col2 = st.columns(2)
                
                with data_col1:
                    if max30102_status:
                        st.markdown("**PPG Sensor (MAX30102)**")
                        # Show values - check both beat_avg and bpm
                        beat_avg_val = latest_data.get('ppg', {}).get('beat_avg', 0)
                        bpm_val = latest_data.get('ppg', {}).get('bpm', 0)
                        # Show BPM if available
                        if beat_avg_val > 0:
                            heart_rate_display = f"{int(beat_avg_val)} BPM"
                        elif bpm_val > 0:
                            heart_rate_display = f"{int(bpm_val)} BPM"
                        else:
                            heart_rate_display = "N/A"
                        st.metric("Heart Rate", heart_rate_display)
                        breathing_rate = latest_data.get('ppg', {}).get('breathing_rate', 0)
                        st.metric(
                            "Breathing Rate",
                            f"{breathing_rate:.1f} breaths/min" if breathing_rate > 0 else "N/A",
                        )
                        
                
                with data_col2:
                    if mpu6050_status:
                        st.markdown("**Motion Sensor (MPU6050)**")
                        accel_x = latest_data.get('motion', {}).get('accel_x', 0)
                        accel_y = latest_data.get('motion', {}).get('accel_y', 0)
                        accel_z = latest_data.get('motion', {}).get('accel_z', 0)
                        st.metric("Accel X", f"{accel_x:.2f} g")
                        st.metric("Accel Y", f"{accel_y:.2f} g")
                        st.metric("Accel Z", f"{accel_z:.2f} g")
                        movement = latest_data.get('motion', {}).get('movement_level', 0)
                        st.metric("Movement Level", f"{movement:.3f} g")
                        

                # Arduino-derived sleep stage summary
                st.markdown("#### 🧠 Sleep Stage (Arduino Sensors)")
                sleep_stage = latest_data.get("sleep_stage", "Unknown")
                noise_level = latest_data.get("audio", {}).get("noise_level", 0)
                stage_col1, stage_col2 = st.columns(2)
                with stage_col1:
                    st.metric("Current Sleep Stage", sleep_stage)
                with stage_col2:
                    st.metric("Noise Level (MAX4466)", f"{noise_level} / 1000")
        
        st.markdown("---")

    # Live Recording Section (laptop/PC microphone)
    st.markdown("### 🎤 Browser Microphone Recording")
    st.markdown(
        "Click 'Start Recording' to begin capturing audio from your **computer's microphone** "
        "for real-time sleep pattern analysis. (This is separate from the Arduino MAX4466 mic.)"
    )

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

    # Real-time auto-refresh for Arduino sensor data
    auto_refresh = st.sidebar.checkbox("🔄 Enable Real-time Updates", value=True, 
                                       help="Automatically refresh sensor data every second")
    
    if auto_refresh:
        try:
            # Check if sensors are connected before refreshing
            should_refresh = False
            if sensor_manager:
                sensor_status = sensor_manager.get_sensor_status()
                should_refresh = any(status['connected'] for status in sensor_status.values())
            
            if should_refresh:
                # Use Streamlit's built-in auto-refresh mechanism
                time.sleep(1)
                safe_rerun()
        except Exception as e:
            # If there's an error, don't crash - just skip the refresh
            st.sidebar.warning(f"Auto-refresh error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

