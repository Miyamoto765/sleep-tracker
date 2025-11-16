# src/train_model.py
"""
Train a RandomForest on features extracted in data/features.csv.

Behaviour:
- If features.csv contains a 'label' column -> supervised training (LabelEncoder used).
- If no 'label' present -> builds pseudo-labels using KMeans (n_clusters=3) for quick prototyping,
  then trains a RandomForest to predict those clusters. Useful as a bootstrap until you have
  ground-truth labels (recommended later).

Outputs:
- models/rf_model.joblib       -> trained sklearn RandomForest
- models/scaler.joblib         -> StandardScaler used
- models/label_encoder.joblib  -> LabelEncoder iff true labels present
- prints test accuracy and classification report
"""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

FEATURE_CSV = os.path.join("data", "features.csv")
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "rf_model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
LE_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")

os.makedirs(MODEL_DIR, exist_ok=True)

def load_features(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found. Run feature extraction first.")
    df = pd.read_csv(path)
    if df.shape[0] == 0:
        raise ValueError("features.csv is empty.")
    return df

def main():
    print("Loading features...")
    df = load_features(FEATURE_CSV)
    print(f"Features shape: {df.shape}")

    # If present, drop any non-numeric or helper columns
    # Keep columns that are numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in features.csv. Check extraction script.")
    X = df[numeric_cols].values

    y = None
    label_encoder = None

    if 'label' in df.columns:
        print("Found 'label' column -> supervised training")
        y_raw = df['label'].astype(str).values
        label_encoder = LabelEncoder()
        y = label_encoder.fit_transform(y_raw)
        joblib.dump(label_encoder, LE_PATH)
        print("Saved LabelEncoder to", LE_PATH)
    else:
        print("No 'label' column found -> using KMeans to create pseudo-labels (bootstrap).")
        n_clusters = 3
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        pseudo = km.fit_predict(X)
        # optional: save cluster centers or km if needed
        y = pseudo
        # store a simple mapping file for cluster sizes
        unique, counts = np.unique(y, return_counts=True)
        print("Cluster distribution (cluster:count):", dict(zip(unique, counts)))

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, SCALER_PATH)
    print("Saved StandardScaler to", SCALER_PATH)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, stratify=y, random_state=42
    )

    print("Training RandomForest...")
    clf = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluation
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {acc:.4f}")
    print("Classification report:")
    try:
        if label_encoder is not None:
            # show decoded labels
            labels = label_encoder.inverse_transform(sorted(np.unique(y_test)))
            print(classification_report(y_test, y_pred, target_names=[str(l) for l in labels]))
        else:
            print(classification_report(y_test, y_pred))
    except Exception:
        print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(clf, MODEL_PATH)
    print("Saved RandomForest model to", MODEL_PATH)

    # Save basic metadata about numeric columns used
    meta = {
        "feature_columns": numeric_cols
    }
    joblib.dump(meta, os.path.join(MODEL_DIR, "meta_feature_cols.joblib"))
    print("Saved feature column metadata.")

if __name__ == "__main__":
    main()
