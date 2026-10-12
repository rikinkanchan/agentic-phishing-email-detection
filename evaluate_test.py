import csv
import hashlib
import json
from pathlib import Path

import joblib
from sklearn.metrics import (
    confusion_matrix, precision_score,
    recall_score, f1_score, accuracy_score
)
from detector import analyse_email

csv.field_size_limit(10_000_000)

def content_key(row):
    text = row["subject"] + "\n" + row["body"]
    normalised = " ".join(text.casefold().split())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

def read_rows(name):
    path = Path("data/processed") / f"{name}.csv"
    with path.open(newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))

metadata = json.loads(
    Path("models/ceas_classifier_metadata.json").read_text()
)

for name, field in (
    ("train", "training_sha256"),
    ("validation", "validation_sha256"),
):
    path = Path("data/processed") / f"{name}.csv"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != metadata[field]:
        raise SystemExit(f"{name} data changed since training. Stop and investigate.")

print("Checking split separation...", flush=True)
previous_keys = set()
for name in ("train", "validation"):
    previous_keys.update(content_key(row) for row in read_rows(name))

test_rows = read_rows("test")
test_keys = {content_key(row) for row in test_rows}
if previous_keys & test_keys:
    raise SystemExit("Matching content crosses into the test split.")

texts = [row["subject"] + "\n" + row["body"] for row in test_rows]
labels = [int(row["label"]) for row in test_rows]

model_path = Path("models/ceas_classifier.joblib")
model = joblib.load(model_path)

print("Evaluating saved classifier...", flush=True)
ml_predictions = model.predict(texts)

print("Evaluating rule-based detector...", flush=True)
rule_predictions = []
for row in test_rows:
    sender = " ".join(row["sender"].splitlines())
    subject = " ".join(row["subject"].splitlines())
    text = f"From: {sender}\nSubject: {subject}\n\n{row['body']}"
    result = analyse_email(text)
    rule_predictions.append(int(result["verdict"] == "suspicious"))

def measure(predictions):
    tn, fp, fn, tp = confusion_matrix(
        labels, predictions, labels=[0, 1]
    ).ravel()
    return {
        "TP": int(tp), "FP": int(fp),
        "TN": int(tn), "FN": int(fn),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "accuracy": float(accuracy_score(labels, predictions)),
    }

rules = measure(rule_predictions)
classifier = measure(ml_predictions)

report = {
    "dataset": "CEAS_08",
    "split": "test",
    "rows": len(test_rows),
    "target": "dataset label 1, not exclusively confirmed phishing",
    "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
    "test_sha256": hashlib.sha256(
        Path("data/processed/test.csv").read_bytes()
    ).hexdigest(),
    "matching_normalised_content_overlap": 0,
    "classifier": classifier,
    "rules": rules,
    "retrained": False,
    "limitations": [
        "Similar templates can still cross splits.",
        "Same-corpus testing does not establish performance on new sources.",
        "Reply-To metadata is unavailable.",
        "Full bodies were evaluated; the interface has a 6,000-character limit."
    ]
}

output = Path("reports/test_comparison.json")
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(report, indent=2))

print(f"\n--- Final CEAS test comparison: {len(test_rows)} emails ---")
for metric in ("precision", "recall", "f1", "accuracy"):
    print(
        f"{metric.capitalize()}: "
        f"Classifier {classifier[metric]:.1%} | Rules {rules[metric]:.1%}"
    )

for name, scores in (("Classifier", classifier), ("Rules", rules)):
    print(
        f"{name}: TP={scores['TP']}, FP={scores['FP']}, "
        f"TN={scores['TN']}, FN={scores['FN']}"
    )

print(f"\nSaved: {output}")
print("No training or threshold changes were performed.")
print("Results measure CEAS label classification, not universal phishing detection.")
