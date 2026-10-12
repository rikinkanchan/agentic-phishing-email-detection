from email import policy
from email.parser import BytesParser

def load_eml(data):
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > 1_000_000:
        raise ValueError("Use an email file smaller than 1 MB.")

    message = BytesParser(policy=policy.default).parsebytes(data)
    body = message.get_body(preferencelist=("plain",))

    if body is None:
        raise ValueError(
            "This version requires a plain-text body. "
            "HTML-only emails are not supported yet."
        )

    text = body.get_content()
    if not isinstance(text, str) or not text.strip():
        raise ValueError("No readable plain-text body was found.")

    headers = []
    for name in ("From", "Reply-To", "Subject"):
        for value in message.get_all(name, []):
            headers.append(f"{name}: {value}")

    email_text = "\n".join(headers) + "\n\n" + text
    if len(email_text) > 6000:
        raise ValueError("The extracted email exceeds the 6,000-character limit.")

    return email_text
