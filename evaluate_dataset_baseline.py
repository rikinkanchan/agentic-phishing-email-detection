import csv
import json
import time
from pathlib import Path
from collections import Counter
from detector import analyse_email

csv.field_size_limit(10_000_000)
source = Path("data/processed/validation.csv")
counts = Counter()
findings = Counter()
errors = 0
total = 0
started = time.perf_counter()

def header_value(value):
    return " ".join((value or "").splitlines())

with source.open(newline="", encoding="utf-8-sig") as file:
    for row in csv.DictReader(file):
        total += 1
        text = (
            f"From: {header_value(row['sender'])}\n"
            f"Subject: {header_value(row['subject'])}\n\n"
            f"{row['body']}"
        )

        try:
            result = analyse_email(text)
            actual = int(row["label"])
            predicted = int(result["verdict"] == "suspicious")

            outcome = {
                (1, 1): "TP",
                (0, 1): "FP",
                (0, 0): "TN",
                (1, 0): "FN",
            }[(actual, predicted)]
            counts[outcome] += 1

            for finding in result["findings"]:
                category = finding.split(" Evidence:", 1)[0]
                category = category.split(":", 1)[0]
                findings[category] += 1

        except Exception:
            errors += 1

tp, fp, tn, fn = (counts[key] for key in ("TP", "FP", "TN", "FN"))
evaluated = tp + fp + tn + fn
precision = tp / (tp + fp) if tp + fp else 0
recall = tp / (tp + fn) if tp + fn else 0
f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
accuracy = (tp + tn) / evaluated if evaluated else 0

summary = {
    "dataset": "CEAS_08",
    "split": "validation",
    "method": "existing rule-based baseline",
    "positive_prediction": "suspicious",
    "target": "dataset label 1; not necessarily confirmed phishing",
    "rows": total,
    "evaluated": evaluated,
    "errors": errors,
    "confusion_matrix": {
        "TP": tp, "FP": fp, "TN": tn, "FN": fn
    },
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "accuracy": accuracy,
    "finding_counts": dict(findings),
    "seconds": round(time.perf_counter() - started, 2),
    "limitations": [
        "Reply-To metadata is unavailable.",
        "Full bodies are scanned without the interface's character limit.",
        "Inconclusive is counted as not flagged, not proven legitimate.",
        "Metrics exclude processing errors; coverage is reported separately."
    ]
}

output = Path("reports/validation_baseline.json")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(summary, indent=2))

print("\n--- CEAS validation baseline ---")
print(f"Evaluated: {evaluated}/{total} | Errors: {errors}")
print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")
print(f"Precision: {precision:.1%}")
print(f"Recall: {recall:.1%}")
print(f"F1: {f1:.1%}")
print(f"Accuracy: {accuracy:.1%}")
print(f"\nSaved aggregate results to {output}")
print("Dataset-label evaluation, not confirmed phishing accuracy.")
print("The test split was not used.")
