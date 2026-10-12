import csv
import hashlib
import json
import time
import warnings
from pathlib import Path
from importlib.metadata import version

import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix
)

csv.field_size_limit(10_000_000)

def load_split(name):
    path = Path("data/processed") / f"{name}.csv"
    texts, labels, groups = [], [], set()

    with path.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            text = row["subject"] + "\n" + row["body"]
            texts.append(text)
            labels.append(int(row["label"]))
            normalised = " ".join(text.casefold().split())
            groups.add(
                hashlib.sha256(normalised.encode("utf-8")).hexdigest()
            )

    return texts, labels, groups, hashlib.sha256(path.read_bytes()).hexdigest()

print("Loading training and validation data...", flush=True)
train_x, train_y, train_groups, train_hash = load_split("train")
val_x, val_y, val_groups, val_hash = load_split("validation")

if train_groups & val_groups:
    raise SystemExit("Matching content crosses splits. Fix the splits first.")
if set(train_y) != {0, 1} or set(val_y) != {0, 1}:
    raise SystemExit("Both labels must be present in each split.")

print(f"Training emails: {len(train_x)}")
print(f"Validation emails: {len(val_x)}")

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        max_features=20000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        dtype=np.float32
    )),
    ("classifier", LogisticRegression(
        solver="liblinear",
        C=1.0,
        max_iter=1000,
        random_state=42
    ))
])

started = time.perf_counter()
print("Training TF-IDF + Logistic Regression...", flush=True)

with warnings.catch_warnings():
    warnings.simplefilter("error", ConvergenceWarning)
    model.fit(train_x, train_y)

print("Evaluating validation data...", flush=True)
predictions = model.predict(val_x)

tn, fp, fn, tp = confusion_matrix(
    val_y, predictions, labels=[0, 1]
).ravel()

metrics = {
    "precision": float(precision_score(val_y, predictions, zero_division=0)),
    "recall": float(recall_score(val_y, predictions, zero_division=0)),
    "f1": float(f1_score(val_y, predictions, zero_division=0)),
    "accuracy": float(accuracy_score(val_y, predictions))
}

summary = {
    "dataset": "CEAS_08",
    "target": "dataset labels 0/1; label 1 is not necessarily confirmed phishing",
    "method": "TF-IDF + Logistic Regression",
    "input": "subject + newline + body",
    "training_rows": len(train_x),
    "validation_rows": len(val_x),
    "training_sha256": train_hash,
    "validation_sha256": val_hash,
    "vocabulary_size": len(model.named_steps["tfidf"].vocabulary_),
    "confusion_matrix": {
        "TP": int(tp), "FP": int(fp),
        "TN": int(tn), "FN": int(fn)
    },
    **metrics,
    "seconds": round(time.perf_counter() - started, 2),
    "versions": {
        package: version(package)
        for package in ("scikit-learn", "joblib", "numpy", "scipy")
    },
    "test_split_used": False
}

Path("models").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

joblib.dump(model, "models/ceas_classifier.joblib")
Path("models/ceas_classifier_metadata.json").write_text(
    json.dumps(summary, indent=2)
)
Path("reports/validation_classifier.json").write_text(
    json.dumps(summary, indent=2)
)

ignore = Path(".gitignore")
text = ignore.read_text() if ignore.exists() else ""
if "models/" not in text.splitlines():
    ignore.write_text(text.rstrip() + "\nmodels/\n")

requirements = Path("requirements.txt")
lines = requirements.read_text().splitlines() if requirements.exists() else []
packages = ("scikit-learn", "joblib")
lines = [
    line for line in lines
    if not any(line.startswith(package + "==") for package in packages)
]
lines.extend(f"{package}=={version(package)}" for package in packages)
requirements.write_text("\n".join(lines) + "\n")

print("\n--- Validation comparison ---")
baseline_path = Path("reports/validation_baseline.json")
baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {}

for name, score in metrics.items():
    previous = baseline.get(name)
    comparison = f" | Rules: {previous:.1%}" if previous is not None else ""
    print(f"{name.capitalize()}: {score:.1%}{comparison}")

print(f"\nTP={tp}, FP={fp}, TN={tn}, FN={fn}")
print(f"Time: {summary['seconds']:.1f} seconds")
print("Model saved: models/ceas_classifier.joblib")
print("Results saved: reports/validation_classifier.json")
print("Test split remains untouched.")
