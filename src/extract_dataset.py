import zipfile
import os

zip_path = "data/cap-sleep-database-1.0.0.zip"
extract_to = "data/raw_audio"

os.makedirs(extract_to, exist_ok=True)

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_to)

print("✅ Dataset extracted successfully to:", extract_to)
