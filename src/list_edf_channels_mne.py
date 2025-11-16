# src/list_edf_channels_mne.py
import sys
import mne

def main(path):
    raw = mne.io.read_raw_edf(path, preload=False, verbose=False)
    print(f"File: {path}")
    print("Index : Channel name (sampling_rate Hz)")
    sfreq = raw.info['sfreq']
    for idx, ch in enumerate(raw.ch_names):
        print(f"{idx:2d} : {ch!r}  | sfreq={sfreq}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/list_edf_channels_mne.py path/to/file.edf")
        sys.exit(1)
    main(sys.argv[1])
