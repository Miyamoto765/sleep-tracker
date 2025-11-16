# src/edf_to_wav_mne.py
import os, sys
from pathlib import Path
import numpy as np
import soundfile as sf
import mne
from tqdm import tqdm

INPUT_DIR = "data/raw_audio/cap-sleep-database-1.0.0"
OUTPUT_DIR = "data/raw_wav"
KEYWORDS = ["audio","mic","snore","resp","airflow","breath"]

def find_channel(raw):
    for i, name in enumerate(raw.ch_names):
        lname = name.lower()
        if any(k in lname for k in KEYWORDS):
            return i
    return 0

def convert(edf_path, out_base_dir, channel_index=None):
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose=False)
    if channel_index is None:
        ch_idx = find_channel(raw)
    else:
        ch_idx = channel_index
    data, _ = raw[ch_idx, :]
    sig = data.ravel().astype('float32')
    # normalize
    m = max(1e-9, abs(sig).max())
    sig = sig / m * 0.99
    sr = int(raw.info['sfreq'])
    rel = os.path.relpath(edf_path, INPUT_DIR)
    base = os.path.splitext(rel)[0]
    out_dir = os.path.join(out_base_dir, os.path.dirname(base))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    safe_label = raw.ch_names[ch_idx].replace(" ", "_").replace("/", "_")
    out_name = f"{os.path.basename(base)}_ch{ch_idx}_{safe_label}.wav"
    out_path = os.path.join(out_dir, out_name)
    sf.write(out_path, sig, sr)
    return out_path

def main(channel_index=None):
    edf_files = []
    for root, _, files in os.walk(INPUT_DIR):
        for f in files:
            if f.lower().endswith(".edf"):
                edf_files.append(os.path.join(root, f))

    print(f"Found {len(edf_files)} EDF files under {INPUT_DIR}")
    if len(edf_files) == 0:
        print("No .edf files found. Check INPUT_DIR.")
        return

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    for edf in tqdm(edf_files, desc="Converting"):
        try:
            out = convert(edf, OUTPUT_DIR, channel_index=channel_index)
        except Exception as e:
            print("Error converting", edf, e)

    print(f"Done. WAVs saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    idx = None
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1])
        except:
            idx = None
    main(channel_index=idx)
