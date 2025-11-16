# app/views/upload.py
import os
from datetime import datetime
import streamlit as st
import pandas as pd
import joblib
import numpy as np
from pydub import AudioSegment
import librosa
import matplotlib.pyplot as plt
from src.feature_extraction import extract_features

# Paths (adjust if your project uses different structure)
MODEL_PATH = "models/rf_model.joblib"
SCALER_PATH = "models/scaler.joblib"
META_PATH = "models/meta_feature_cols.joblib"
UPLOAD_DIR = "data/uploads"
HISTORY_CSV = "data/upload_history.csv"

# ensure dirs
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(HISTORY_CSV), exist_ok=True)

@st.cache_resource
def load_model():
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    meta = joblib.load(META_PATH)
    return model, scaler, meta.get("feature_columns", None)

def append_history_row(row: dict):
    df_row = pd.DataFrame([row])
    if not os.path.exists(HISTORY_CSV):
        df_row.to_csv(HISTORY_CSV, index=False)
    else:
        df_row.to_csv(HISTORY_CSV, mode="a", header=False, index=False)

# mapper (simple, mirror analytics mapping)
def _map_prediction_to_label(pred):
    if pd.isna(pred):
        return "Unknown"
    try:
        # numeric -> int mapping
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

def sidebar_history_widget(max_items: int = 6):
    st.sidebar.header("Upload history")
    if os.path.exists(HISTORY_CSV):
        df_hist = pd.read_csv(HISTORY_CSV)
        if df_hist.shape[0] == 0:
            st.sidebar.info("No uploads yet.")
            return
        recent = df_hist.sort_values("timestamp", ascending=False).head(max_items)
        for _, r in recent.iterrows():
            ts = r.get("timestamp")
            fn = r.get("filename")
            pred = r.get("label", r.get("prediction", ""))
            score = r.get("sleep_score", "")
            if pd.isna(score):
                score = ""
            st.sidebar.write(f"**{fn}** — {pred} ({int(score) if score!='' else ''}%)")
            st.sidebar.caption(str(ts))
    else:
        st.sidebar.info("No uploads yet. Upload a .wav or .mp3 to get started.")

def render():
    st.markdown('<div class="page-content fade-in">', unsafe_allow_html=True)
    st.markdown("## 🎵 Upload audio & predict sleep stage")
    st.markdown(
        "Add a short recording (30–60s). Supported: WAV, MP3, FLAC, OGG. "
        "The app extracts acoustic features and predicts a sleep-stage cluster."
    )

    model, scaler, feature_cols = load_model()

    sidebar_history_widget()

    uploaded = st.file_uploader("Upload an audio file", type=["wav", "mp3", "flac", "ogg"])
    if uploaded is None:
        st.info("Upload a WAV/MP3 to see predictions.")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Save uploaded file to uploads dir
    ext = uploaded.name.split(".")[-1].lower()
    safe_fn = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded.name}"
    saved_path = os.path.join(UPLOAD_DIR, safe_fn)
    with open(saved_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.success(f"Saved uploaded file: `{safe_fn}`")
    st.audio(saved_path)

    # Convert compressed formats to WAV for librosa if required
    proc_path = saved_path
    if ext in ("mp3", "flac", "ogg"):
        st.info("Converting to WAV for robust processing...")
        wav_path = saved_path.rsplit(".", 1)[0] + ".wav"
        try:
            sound = AudioSegment.from_file(saved_path)
            sound.export(wav_path, format="wav")
            proc_path = wav_path
        except Exception as e:
            st.error(f"Conversion failed: {e}")
            st.markdown('</div>', unsafe_allow_html=True)
            return

    with st.spinner("Extracting features and running model..."):
        try:
            feats = extract_features(proc_path)  # dict or list depending on implementation
            # align to feature_cols
            if isinstance(feats, dict) and feature_cols:
                row_feats = [feats.get(c, np.nan) for c in feature_cols]
            elif isinstance(feats, (list, tuple)) and feature_cols:
                row_feats = list(feats)[: len(feature_cols)]
            else:
                if isinstance(feats, dict):
                    row_feats = list(feats.values())
                else:
                    row_feats = list(feats)

            X_df = pd.DataFrame([row_feats], columns=feature_cols) if feature_cols else pd.DataFrame([row_feats])
            Xs = scaler.transform(X_df)
            pred_raw = model.predict(Xs)[0]
            # convert pred_raw to a string for saving (keep raw)
            pred_str = str(pred_raw)

            # compute confidence / sleep_score
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(Xs)[0]
                score = float(proba.max() * 100)
            else:
                # fallback heuristic: map class to a rough score if you want,
                # for now fallback to 50 if unknown
                score = 50.0

            # get normalized label
            label = _map_prediction_to_label(pred_raw)

            # show results
            st.markdown("### 🧠 Sleep Score")
            st.success(f"Sleep score: **{int(score)}/100** (label: **{label}**)")
            st.metric("Confidence", f"{int(score)}%")
            st.markdown("### 🔎 Feature snapshot (top)")
            st.dataframe(X_df.T.head(12))

            # plot MFCCs
            st.markdown("### 🎶 MFCC Spectrum")
            try:
                audio, sr = librosa.load(proc_path, sr=None)
                mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
                plt.figure(figsize=(10, 4))
                librosa.display.specshow(mfccs, x_axis="time", sr=sr)
                plt.colorbar(format="%+2.0f dB")
                plt.title("MFCCs")
                st.pyplot(plt)
                plt.clf()
            except Exception as e:
                st.error(f"Error plotting MFCC: {e}")

            # save history row
            row = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "filename": safe_fn,
                "filepath": proc_path,
                "prediction": pred_str,
                "label": label,
                "sleep_score": float(score),
            }
            append_history_row(row)
            st.success("Saved to upload history. (prediction, label, sleep_score)")

            # keep last in session for quick access
            st.session_state["last_upload"] = row

        except Exception as e:
            st.error(f"Processing failed: {e}")

    st.markdown('</div>', unsafe_allow_html=True)
