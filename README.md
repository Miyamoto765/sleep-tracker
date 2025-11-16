# Sleep Tracker

A Streamlit-based application for sleep data analysis using EDF (European Data Format) files and machine learning.

## Project Structure

```
sleep-tracker/
├── app/                          # Main Streamlit application
│   ├── streamlit_app.py         # Main entry point
│   ├── ui.py                    # UI components
│   └── views/                   # Application views
│       ├── home.py              # Home page
│       ├── analytics.py         # Analytics dashboard
│       ├── logger.py            # Data logging
│       └── upload.py            # File upload interface
├── src/                          # Data processing scripts
│   ├── feature_extraction.py    # Extract features from EDF files
│   ├── train_model.py           # Model training
│   ├── edf_to_wav_mne.py        # EDF to WAV conversion
│   └── extract_dataset.py       # Dataset extraction
├── python/                       # Utility scripts
│   └── serial_reader.py         # Serial data reading
├── models/                       # Trained ML models
├── data/                         # Data storage
│   ├── raw_audio/               # Raw EDF files
│   ├── raw_wav/                 # Converted WAV files
│   └── uploads/                 # User uploads
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sleep-tracker.git
cd sleep-tracker
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
streamlit run app/streamlit_app.py
```

## Features

- Upload and process EDF sleep data files
- Extract features from sleep recordings
- Machine learning-based sleep analysis
- Interactive analytics dashboard
- Data visualization and statistics

## Requirements

- Python 3.8+
- Streamlit
- MNE (for EDF file processing)
- scikit-learn
- pandas
- numpy

## License

[Add your license here]

## Auto-sync (optional)

This repository includes a small PowerShell helper and a scheduled task to auto-fetch and fast-forward-pull
remote changes into your local copy when it is clean and strictly behind the remote. This is intended for
environments where you want remote changes to appear locally automatically (for example CI agents or single-user
workstations).

- Script path: `scripts/autopull.ps1`
- Scheduled task: `SleepTracker_AutoGitPull` (runs every 5 minutes)

How it works
- The script fetches `origin`, checks whether your current branch is clean and strictly behind the upstream, and
	performs `git pull --ff-only` only in that safe case. If you have uncommitted changes, or branches have diverged,
	it skips the pull to avoid accidental conflicts or data loss.

Quick manual test
1. Run once and show output in console:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . 'C:\Users\ahmed\OneDrive\Desktop\sleep-tracker\scripts\autopull.ps1'; Run-Once }"
```

2. To run the script continuously (background) use the scheduled task (already created) or run the script directly:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\ahmed\OneDrive\Desktop\sleep-tracker\scripts\autopull.ps1"
```

Log file
- The script appends diagnostic lines to `scripts/autopull.log` inside the repository.

If you'd like different behavior (auto-stash/pop, automatic merges, or different polling interval), please let me
know and I can adjust the script accordingly.
