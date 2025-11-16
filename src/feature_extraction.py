import os
import librosa
import numpy as np
import pandas as pd
from tqdm import tqdm

# ✅ Path to your dataset
AUDIO_DIR = "data/raw_wav"
OUTPUT_CSV = "data/features.csv"

def extract_features(file_path):
    try:
        # Load first 30 seconds for uniformity
        y, sr = librosa.load(file_path, duration=30)
        if y.ndim > 1:
            y = librosa.to_mono(y)

        # Audio features
        mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        rms = np.mean(librosa.feature.rms(y=y))

        # Combine all into one array
        return np.hstack([mfcc, zcr, centroid, bandwidth, rolloff, rms])

    except Exception as e:
        print(f"⚠️ Error processing {file_path}: {e}")
        return None


def main():
    wav_files = []
    for root, _, files in os.walk(AUDIO_DIR):
        for f in files:
            if f.endswith(".wav"):
                wav_files.append(os.path.join(root, f))

    print(f"🎧 Found {len(wav_files)} audio files in {AUDIO_DIR}")

    features = []
    for path in tqdm(wav_files, desc="Extracting features"):
        feat = extract_features(path)
        if feat is not None:
            features.append(feat)

    columns = [f"mfcc_{i}" for i in range(13)] + ["zcr", "centroid", "bandwidth", "rolloff", "rms"]
    df = pd.DataFrame(features, columns=columns)

    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Feature extraction complete! Saved as {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
