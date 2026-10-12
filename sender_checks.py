from email import policy
from email.parser import Parser
from email.utils import parseaddr

def get_domain(address):
    if address.count("@") != 1:
        return None
    local, domain = address.rsplit("@", 1)
    if not local or not domain or any(c.isspace() for c in address):
        return None
    return domain.lower()

def analyse_sender(text):
    message = Parser(policy=policy.default).parsestr(text)
    findings = []

    sender = parseaddr(str(message.get("From", "")))[1]
    reply_to = parseaddr(str(message.get("Reply-To", "")))[1]
    sender_domain = get_domain(sender)
    reply_domain = get_domain(reply_to)


    if not sender_domain:
        findings.append("From address is missing or could not be parsed.")

    if message.get("Reply-To") is not None:
        if not reply_domain:
            findings.append("Reply-To address could not be parsed.")
        elif sender_domain and sender_domain != reply_domain:
            findings.append(
                f"Domain mismatch: sender uses {sender_domain}, "
                f"but replies go to {reply_domain}."
            )

    return findings

if __name__ == "__main__":
    print("Paste email headers and body. Type END on a separate line.")
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
    if not text.strip():
        print("No email provided.")
    else:
        findings = analyse_sender(text)
        print("\n--- Sender analysis ---")
        for finding in findings:
            print(f"- {finding}")
        if not findings:
            print("No warning signs found by these sender checks.")
        print("These checks do not authenticate the sender.")
