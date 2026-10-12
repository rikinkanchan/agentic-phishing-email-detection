# CEAS evaluation

## Source and scope

Source: https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset/data
File: CEAS_08.csv. Target: supplied binary dataset labels, not independently
confirmed phishing labels.

## Method

SHA-256 assignment groups matching case-folded, whitespace-normalised
subject/body content. Training/validation/test sizes are 23,410/7,801/7943.
No matching normalised content crossed into the test split.
Similar templates and corpus-specific patterns can still cross splits.

TF-IDF uses up to 20,000 features, word unigrams/bigrams, min_df=2 and
sublinear term frequency. Logistic Regression uses liblinear, C=1,
max_iter=1000 and random_state=42. Features use subjects and bodies.

Validation classifier accuracy: 99.5%.
Validation classifier F1: 99.6%.

## Held-out test

| Metric | Classifier | Rules |
|---|---:|---:|
| Precision | 99.5% | 57.5% |
| Recall | 99.6% | 68.8% |
| F1 | 99.5% | 62.6% |
| Accuracy | 99.5% | 54.0% |


Classifier: TP=4431, FP=23, TN=3469, FN=20.
Rules: TP=3064, FP=2268, TN=1224, FN=1387.

Rules count suspicious as positive and inconclusive as not flagged.
Inconclusive is not a finding of legitimacy. Dataset metadata has no
Reply-To column. Evaluation scans full bodies, unlike the bounded interface.

Model SHA-256: ae5398644402c9eeae8b0489206694c39871801c98df53b0acc1a48cc6a16f9a
Test-file SHA-256: 68e61b26efbf35496ff7b5973d7b7a530b972d17118621d8e135119ada16e70b

## Generalisation check

A fresh ordinary meeting email produced label 1 with a 63.6% score.
A fresh credential-request example produced label 1 with a 73.6% score.
These two examples are diagnostic checks, not a benchmark.
Observed learned terms suggest spam-topic and mailing-list associations.

## Agent integration

The classifier is advisory. Rule verdicts and template explanations remain
separate. One observed run passed 3/3 workflow cases with eight checks each.
Observed durations: ordinary 6.9s, suspicious 4.3s, injection sample 4.1s.
These are single-run measurements, not performance guarantees.
The links_opened flag is a consistency check, not independent network monitoring.

## Reproduction

Run prepare_dataset.py, evaluate_dataset_baseline.py and train_classifier.py.
Use evaluate_agent.py with Ollama running.
Run evaluate_test.py only after fixing the method.
Raw datasets and trained models are excluded from Git; aggregate reports are included.
