# Agentic AI-Based Phishing Email Detection and Explanation System

A local prototype that examines emails for phishing warning signs.
A Qwen3 1.7B agent running through Ollama selects analysis tools,
reviews their evidence and decides when to finish.

The verdict comes from rule-based checks. Displayed explanations
use evidence templates after testing revealed contradictions in
the model's generated explanations.

## Features

- Paste email headers and body into a Streamlit interface.
- Upload .eml files containing a plain-text body.
- Check From and Reply-To domain differences.
- Detect configured urgency and sensitive-information phrases.
- Inspect URL text for HTTP, IP-address hosts and user information.
- Display findings, explanations, recommended actions and agent activity.
- Analyse links without opening them.

## Setup

Install Python and Ollama, then download the model:

```bash
ollama pull qwen3:1.7b
```

Inside the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Keep Ollama running and start the interface:

```bash
python -m streamlit run app.py --server.address 127.0.0.1
```

Open http://localhost:8501.

## Evaluation

Run the synthetic detector evaluation:

```bash
python evaluate_baseline.py
```

Eight hand-written fictional samples produced:

- True positives: 3
- False positives: 2
- True negatives: 2
- False negatives: 1
- Precision: 60%
- Recall: 75%
- F1: 66.7%

These are demonstration results, not estimates of real-world performance.
For evaluation, "inconclusive" counts as not flagged, not proven legitimate.

Run the agent workflow tests with Ollama running:

```bash
python evaluate_agent.py
```

One observed run passed all 3 workflow tests: ordinary email,
suspicious email and a prompt-injection sample.
This measures workflow consistency, not detection accuracy or
general resistance to prompt injection.

## Limitations

- Rules can flag legitimate emails and miss phishing emails.
- Verdicts are suspicious or inconclusive; neither proves legitimacy.
- Sender authentication and link reputation are not tested.
- HTML bodies and attachments are not analysed.
- Uploaded files must be at most 1,000,000 bytes.
- Extracted email text is limited to 6,000 characters.
- The agent has a four-step limit and can fail to finish.
- Broader evaluation on independently labelled emails is still needed.

## Architecture

Streamlit input → email text → AI tool-selection loop →
Python analysis tools → rule-based verdict and template explanations.
