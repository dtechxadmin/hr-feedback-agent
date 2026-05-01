"""
faq.py — HR FAQ knowledge base, scoped to feedback and culture topics.

Keeping this narrow on purpose: the demo story is about the feedback loop,
not about being a general HR encyclopedia. A CPO will probe culture and
trust questions more than PTO accrual math.
"""

FAQ_ENTRIES = [
    {
        "keywords": ["anonymous", "anonymity", "confidential", "see my name", "who can see"],
        "question": "Is my feedback confidential?",
        "answer": (
            "Your feedback can be submitted in one of two ways, and you choose which at the time "
            "of submission:\n\n"
            "Confidential — HR will have your name on record for accountability, but your manager "
            "will not see it. This is the default for sensitive topics like manager feedback, "
            "culture, and workload.\n\n"
            "Shared — Both HR and your manager will see your name on the feedback. This is a good "
            "option when you want your manager to be part of the conversation.\n\n"
            "Either way, HR always retains your identity. This is to ensure feedback is used "
            "responsibly and cannot be submitted in bad faith."
        ),
    },
    {
        "keywords": ["what happens", "does anything happen", "does feedback get read", "acted on", "ignored"],
        "question": "What actually happens after I submit feedback?",
        "answer": (
            "Every submission is reviewed by the HR team within 3 business days. "
            "Feedback is categorized, tagged, and surfaced to the relevant leader — "
            "your direct manager for team-level themes, the CPO for org-wide patterns. "
            "Each quarter, HR publishes a summary of themes and actions taken. "
            "You won't receive a personal reply to anonymous submissions, but you will "
            "see the aggregate response in the quarterly update."
        ),
    },
    {
        "keywords": ["pulse", "pulse survey", "survey", "how often", "frequency"],
        "question": "How often are pulse surveys sent?",
        "answer": (
            "Pulse surveys go out every 6 weeks — 5 questions, takes under 2 minutes. "
            "Participation is voluntary but strongly encouraged; aggregate results are "
            "shared back to the full team within 2 weeks of close. "
            "Ad-hoc feedback (like submitting through this assistant) is always open "
            "and goes directly into the same review queue as pulse responses."
        ),
    },
    {
        "keywords": ["retaliation", "fear", "safe", "trust", "worried", "consequence"],
        "question": "Will I face consequences for giving negative feedback?",
        "answer": (
            "Retaliation for submitting feedback — positive or negative — is a policy violation "
            "and grounds for disciplinary action. Confidential submissions are designed specifically "
            "to make this a non-issue. If you ever feel you've experienced retaliation after "
            "submitting feedback, report it directly to the HR Manager or through "
            "your organization's ethics reporting channel."
        ),
    },
    {
        "keywords": ["manager", "my manager", "feedback about manager", "report manager"],
        "question": "Can I give feedback about my manager?",
        "answer": (
            "Yes — and this is one of the most valuable inputs the HR team receives. "
            "Manager feedback submitted here goes to the HR Business Partner for your team, "
            "not to your manager directly. It's aggregated with other signals before any "
            "conversation happens. Submit anonymously if you prefer — the content matters "
            "more than the attribution."
        ),
    },
    {
        "keywords": ["performance review", "review", "upward feedback", "360"],
        "question": "Is this the same as the performance review process?",
        "answer": (
            "No — this is a separate, always-on channel. Performance reviews happen twice "
            "a year and involve structured evaluations tied to compensation. "
            "This feedback tool is informal and continuous — use it whenever something "
            "comes up rather than waiting for a review cycle. The two channels feed "
            "different processes, but HR looks at both when spotting patterns."
        ),
    },
]


def lookup_faq(query: str) -> str:
    """Keyword-based FAQ lookup. Returns best match or a warm fallback."""
    query_lower = query.lower()
    for entry in FAQ_ENTRIES:
        if any(kw in query_lower for kw in entry["keywords"]):
            return f"**{entry['question']}**\n\n{entry['answer']}"
    return (
        "I don't have a specific entry for that question. "
        "You can reach the HR team directly at hr@company.com — "
        "they respond within one business day."
    )