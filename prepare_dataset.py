import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

csv.field_size_limit(10_000_000)

source = Path("data/raw/CEAS_08.csv")
output = Path("data/processed")
output.mkdir(parents=True, exist_ok=True)

def content_key(row):
    text = row["subject"] + "\n" + row["body"]
    normalised = " ".join(text.casefold().split())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()

with source.open(newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)
    columns = reader.fieldnames
    required = {"sender", "subject", "body", "label"}
    if not required.issubset(columns or []):
        raise SystemExit("Required columns are missing.")
    rows = list(reader)

groups = {}
for row in rows:
    if row["label"] not in {"0", "1"}:
        raise SystemExit("Unexpected label found. No split files written.")
    if not row["body"].strip():
        raise SystemExit("Empty body found. No split files written.")

    key = content_key(row)
    groups.setdefault(key, []).append(row)

for group in groups.values():
    if len({row["label"] for row in group}) > 1:
        raise SystemExit(
            "Matching content has conflicting labels. "
            "Resolve this before splitting. No split files written."
        )

splits = {"train": [], "validation": [], "test": []}

for key, group in groups.items():
    # Stable assignment based only on content, not the label.
    bucket = int(key[:8], 16) / 2**32
    name = "train" if bucket < 0.6 else "validation" if bucket < 0.8 else "test"
    splits[name].extend(group)

summary = {
    "source": str(source),
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "total_rows": len(rows),
    "normalised_content_groups": len(groups),
    "method": "SHA-256 content grouping; approximate 60/20/20 split",
    "splits": {}
}

for name, records in splits.items():
    if not records:
        raise SystemExit(f"The {name} split is empty.")

    path = output / f"{name}.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

    counts = dict(Counter(row["label"] for row in records))
    summary["splits"][name] = {
        "rows": len(records),
        "label_counts": counts
    }
    print(f"{name}: {len(records)} emails | labels: {counts}")

(output / "split_summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)

ignore = Path(".gitignore")
text = ignore.read_text() if ignore.exists() else ""
for entry in ("data/raw/", "data/processed/"):
    if entry not in text.splitlines():
        text = text.rstrip() + "\n" + entry + "\n"
ignore.write_text(text)

print(f"\nTotal: {len(rows)} emails")
print(f"Normalised content groups: {len(groups)}")
print("Dataset splits prepared and excluded from Git.")
print("Keep test.csv untouched until final evaluation.")
