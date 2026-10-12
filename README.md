# PhishLens
## Agentic AI-Based Phishing Email Detection and Explanation System

A local email investigation prototype using Python, Streamlit,
Ollama, Qwen3 1.7B and a TF-IDF + Logistic Regression classifier.

Paste an email or upload a plain-text .eml file to review rule findings,
experimental classifier advice, evidence explanations and recommended actions.

## Features

- From and Reply-To domain checks.
- Configured suspicious wording and URL-structure checks.
- Local AI tool selection and evidence review.
- Separate rule-based verdict and CEAS classifier advice.
- A notice when the two methods flag different outcomes.
- Evidence-template explanations.
- Dashboard with agent activity, timing and JSON report download.
- Links inspected as text without opening them.

## How it works

The AI chooses from inspect_sender, inspect_email and classify_content.
Python validates tool names, prevents repeat execution and requires both
inspect_email and classify_content before accepting completion.
The agent has a six-step limit.

The final verdict comes from rules. Classifier advice predicts CEAS dataset
labels and is displayed separately. Explanations use evidence templates
because free-form model explanations contradicted findings during testing.

## Setup

Install Python and Ollama. Keep Ollama running and download the model:

```bash
ollama pull qwen3:1.7b
```

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
mkdir -p data/raw
```

Download CEAS_08.csv from the
[Kaggle dataset](https://www.kaggle.com/datasets/naserabdullahalam/phishing-email-dataset/data)
and place it in data/raw/.

Prepare the splits and train the classifier:

```bash
python prepare_dataset.py
python evaluate_dataset_baseline.py
python train_classifier.py
```

Then start the dashboard:

```bash
python -m streamlit run app.py --server.address 127.0.0.1
```

Open http://localhost:8501. Browser input does not require END.
The classifier model is created locally and excluded from Git.

## Evaluation

The dataset contains 39,154 emails. Matching normalised subject/body
content was grouped into the same split:

- Training: 23,410 emails.
- Validation: 7,801 emails.
- Held-out test: 7,943 emails.

The vocabulary and classifier were fitted on training data only.
The saved model was evaluated on the test split without retraining
or threshold changes.

### Held-out CEAS results

| Metric | Classifier | Rules |
|---|---:|---:|
| Precision | 99.5% | 57.5% |
| Recall | 99.6% | 68.8% |
| F1 | 99.5% | 62.6% |
| Accuracy | 99.5% | 54.0% |


Classifier errors: 23 false positives and 20 false negatives.

These metrics measure CEAS dataset-label classification. Label 1 includes
spam and is not exclusively confirmed phishing. They do not establish
performance on emails from arbitrary sources.

### Known failure

A fresh ordinary project-meeting email was assigned label 1 with a 63.6%
model score. This is a false alarm and demonstrates a generalisation limit.
Model scores are not calibrated probabilities of phishing.

### Agent workflow checks

```bash
python evaluate_agent.py
```

One observed run passed 3/3 samples: ordinary email, suspicious email and
an embedded prompt-injection attempt. Each passed eight checks covering
required tools, classifier advice, different-signals reporting, verdict,
findings, template explanations and the links_opened flag.

This is workflow verification, not proof of universal prompt-injection resistance.

### Final test evaluation

After fixing the method, run:

```bash
python evaluate_test.py
```

Do not tune the model against the held-out test results.
See [detailed evaluation notes](docs/CEAS_EVALUATION.md).

## Limitations

- Rules can produce false alarms and miss malicious messages.
- Inconclusive does not mean safe.
- The classifier learns CEAS spam/legitimate associations, not universal phishing indicators.
- Similar email templates may cross splits despite normalised-content grouping.
- SPF, DKIM, DMARC, link reputation and destination pages are not verified.
- Uploads require a plain-text body; HTML alternatives and attachments are not analysed.
- Dataset evaluation lacks Reply-To metadata and uses full bodies.
- The interface limits extracted text to 6,000 characters and uploads to 1,000,000 bytes.
- Missing models, model errors or the step limit can prevent completion.
- Submitted email text and tool results are sent to the local Ollama endpoint.
- Exported reports can contain email addresses and URLs from findings.

## Author

Rikin Rajesh Kanchan
