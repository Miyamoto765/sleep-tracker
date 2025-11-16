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
