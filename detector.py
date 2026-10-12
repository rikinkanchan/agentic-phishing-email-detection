from sender_checks import analyse_sender
import re
import ipaddress
from urllib.parse import urlsplit

def analyse_email(text):
    findings = analyse_sender(text)

    checks = [
        (
            r"\b(urgent|immediately|within 24 hours|account suspended)\b",
            "Urgency or pressure language detected."
        ),
        (
            r"\b(verify your account|confirm your password|enter your password|send your otp)\b",
            "Account verification or sensitive-information request detected."
        ),
    ]

    for pattern, explanation in checks:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            findings.append(f'{explanation} Evidence: "{match.group(0)}"')

    links = re.findall(r"https?://[^\s<>\"']+", text, re.IGNORECASE)

    for link in dict.fromkeys(links):
        link = link.rstrip(".,;!?)")
        try:
            parsed = urlsplit(link)
            host = parsed.hostname
            if not host:
                findings.append(f"Malformed web link: {link}")
                continue

            if parsed.scheme.lower() == "http":
                findings.append(f"Link uses unencrypted HTTP: {link}")

            try:
                ipaddress.ip_address(host)
            except ValueError:
                pass
            else:
                findings.append(f"Link uses an IP address as its host: {link}")

            if parsed.username is not None:
                findings.append(f"Link contains user information before its host: {link}")

        except ValueError:
            findings.append(f"Could not parse web link: {link}")


    return {
        "verdict": "suspicious" if findings else "inconclusive",
        "findings": findings,
        "links_opened": False,
        "limitation": "Rule-based checks do not authenticate the sender or prove legitimacy."
    }

if __name__ == "__main__":
    import json

    print("Paste an email. Type END on a separate line.")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)

    text = "\n".join(lines)
    if text.strip():
        print(json.dumps(analyse_email(text), indent=2))
    else:
        print("No email provided.")
