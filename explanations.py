def explain_findings(findings):
    if not findings:
        return (
            "The configured sender, wording and URL checks found no warning "
            "signs. The result is inconclusive and does not establish legitimacy."
        )

    explanations = [
        ("Domain mismatch:",
         "Replies would go to a different domain from the From address. "
         "This needs verification; legitimate services can also use different domains."),
        ("Urgency or pressure language",
         "Pressure language can encourage a recipient to act before checking the request."),
        ("Account verification or sensitive-information request",
         "The message contains a configured account-verification or sensitive-information phrase. "
         "Verify the request independently before providing information."),
        ("Link uses unencrypted HTTP:",
         "The URL uses HTTP, which does not provide HTTPS transport encryption. "
         "This alone does not prove phishing."),
        ("Link uses an IP address",
         "The URL uses an IP address instead of a domain name, making the destination "
         "harder to recognise. This alone does not prove phishing."),
        ("Link contains user information",
         "Text before the URL's host can make the destination misleading."),
        ("From address is missing",
         "The sender address could not be assessed from the supplied text."),
        ("Reply-To address could not",
         "The reply address could not be assessed from the supplied text."),
        ("Malformed web link:",
         "The detected link has a missing or invalid host."),
        ("Could not parse web link:",
         "The detected link could not be parsed.")
    ]

    paragraphs = []
    for finding in findings:
        reason = next(
            (reason for prefix, reason in explanations
             if finding.startswith(prefix)),
            "This configured check returned a finding that requires review."
        )
        paragraphs.append(f"{finding}\nWhy it matters: {reason}")

    paragraphs.append(
        "These findings support review, not proof of phishing. "
        "Sender authentication and link reputation were not tested."
    )
    return "\n\n".join(paragraphs)
