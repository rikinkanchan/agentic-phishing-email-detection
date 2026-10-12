from detector import analyse_email
from sender_checks import analyse_sender

def inspect_sender(email_text):
    return {
        "findings": analyse_sender(email_text),
        "limitation": "These checks do not authenticate the sender."
    }

def inspect_email(email_text):
    result = dict(analyse_email(email_text))
    result["checks_performed"] = [
        "From and Reply-To address checks",
        "Scan for configured suspicious wording",
        "Scan for HTTP/HTTPS links and inspect their URL structure"
    ]
    result["interpretation"] = (
        "These checks ran even when findings is empty. "
        "Links were scanned as text, not opened. "
        "An empty findings list does not prove legitimacy."
    )
    return result

TOOLS = {
    "inspect_sender": inspect_sender,
    "inspect_email": inspect_email,
}

def run_tool(name, email_text):
    if name not in TOOLS:
        raise ValueError(f"Unknown tool: {name}")
    return TOOLS[name](email_text)
