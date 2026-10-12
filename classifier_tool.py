from pathlib import Path
from functools import lru_cache
from email import policy
from email.parser import Parser
import joblib

MODEL_PATH = Path(__file__).resolve().parent / "models/ceas_classifier.joblib"

@lru_cache(maxsize=1)
def get_model():
    if not MODEL_PATH.exists():
        raise ValueError("Classifier model is missing. Run train_classifier.py.")
    return joblib.load(MODEL_PATH)

def classify_content(email_text):
    message = Parser(policy=policy.default).parsestr(email_text)
    body_part = message.get_body(preferencelist=("plain",))
    if body_part is None:
        raise ValueError("Classifier requires a plain-text email body.")

    body = body_part.get_content()
    if not isinstance(body, str) or not body.strip():
        raise ValueError("No readable body supplied.")

    subject = str(message.get("Subject", ""))
    text = subject + "\n" + body

    model = get_model()
    predicted = int(model.predict([text])[0])
    classes = list(model.classes_)
    score = float(model.predict_proba([text])[0][classes.index(1)])

    return {
        "tool": "classify_content",
        "predicted_dataset_label": predicted,
        "label_1_model_score": round(score, 4),
        "training_dataset": "CEAS_08",
        "input_used": "subject and plain-text body",
        "interpretation": (
            "Prediction of the CEAS dataset label, not a verified phishing verdict."
        ),
        "limitations": [
            "Label 1 includes spam; it is not exclusively confirmed phishing.",
            "Model scores are not calibrated guarantees.",
            "An ordinary meeting example was incorrectly assigned label 1.",
            "Label 0 does not establish email safety."
        ]
    }
