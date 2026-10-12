from detector import analyse_email

# Hand-written fictional samples, not a real-world benchmark.
# Each tuple contains: name, phishing label, email text.
samples = [
    ("Normal meeting", False,
     "From: team@university.example\n\nMeeting on Friday at 3 PM."),

    ("Normal HTTPS link", False,
     "From: library@university.example\n\n"
     "Course reading: https://university.example/reading"),

    ("Legitimate urgency", False,
     "From: team@university.example\n\n"
     "Urgent: tomorrow's meeting has moved to Room 2."),

    ("Legitimate external Reply-To", False,
     "From: events@university.example\n"
     "Reply-To: bookings@venue.example\n\n"
     "Our event venue manages booking replies."),

    ("Phishing with password request", True,
     "From: alerts@bank.example\n\n"
     "Enter your password here: http://192.0.2.10/login"),

    ("Phishing with mismatched reply", True,
     "From: alerts@bank.example\n"
     "Reply-To: support@account-help.example\n\n"
     "Reply with your account details."),

    ("Phishing with urgency", True,
     "From: support@account-help.example\n\n"
     "Urgent! Verify your account immediately."),

    ("Phishing missed by current rules", True,
     "From: payroll@salary-help.example\n\n"
     "Your salary statement is ready. Sign in at "
     "https://salary-help.example/access"),
]

tp = fp = tn = fn = 0

for name, is_phishing, text in samples:
    result = analyse_email(text)
    flagged = result["verdict"] == "suspicious"

    if is_phishing and flagged:
        tp += 1
        outcome = "TP: phishing sample flagged"
    elif not is_phishing and flagged:
        fp += 1
        outcome = "FP: legitimate sample flagged"
    elif is_phishing and not flagged:
        fn += 1
        outcome = "FN: phishing sample missed"
    else:
        tn += 1
        outcome = "TN: legitimate sample not flagged"

    print(f"{name}: {outcome}")

precision = tp / (tp + fp) if tp + fp else 0
recall = tp / (tp + fn) if tp + fn else 0
f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

print("\n--- Synthetic baseline evaluation ---")
print(f"Samples: {len(samples)}")
print(f"TP={tp}, FP={fp}, TN={tn}, FN={fn}")
print(f"Precision: {precision:.1%}")
print(f"Recall: {recall:.1%}")
print(f"F1: {f1:.1%}")
print("\nThese metrics cover only eight hand-written samples.")
print("They do not estimate real-world detection performance.")
print("'Inconclusive' is counted as not flagged, not as proven legitimate.")
print("This evaluates the rule-based detector, not the AI agent.")
