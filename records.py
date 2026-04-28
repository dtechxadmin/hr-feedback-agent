"""
records.py — Feedback record store for the HR feedback agent POC.

Designed to show a CPO what the *data* looks like, not just that a record
was created. Each submission captures enough metadata to surface themes,
track response status, and demonstrate a closed feedback loop.

Why JSON file:
  Persists across Streamlit reruns. Open records.json mid-demo to show
  a live record. Easy to explain: "In production this writes to Culture Amp,
  Lattice, or your HRIS via API — same tool pattern, different endpoint."
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

RECORDS_FILE = Path("records.json")

VALID_CATEGORIES = [
    "culture",
    "management",
    "onboarding",
    "benefits",
    "dei",
    "workload",
    "policy",
    "recognition",
    "general",
]

VALID_SENTIMENTS = ["positive", "constructive", "concern", "urgent"]


def _load() -> dict:
    if RECORDS_FILE.exists():
        return json.loads(RECORDS_FILE.read_text())
    return {"feedback": []}


def _save(data: dict):
    RECORDS_FILE.write_text(json.dumps(data, indent=2, default=str))


def _new_id() -> str:
    return f"FBK-{uuid.uuid4().hex[:6].upper()}"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def submit_feedback(
    feedback_text: str,
    category: str = "general",
    sentiment: str = "constructive",
    visibility: str = "anonymous_to_manager",
    employee_name: str = "anonymous",
    employee_id: str = None,
    email: str = None,
    department: str = None,
    follow_up_ok: bool = False,
) -> dict:
    """
    Submit a feedback record.

    Parameters
    ----------
    feedback_text   The actual feedback content.
    category        Topic area — culture, management, onboarding, etc.
    sentiment       Tone signal — positive, constructive, concern, urgent.
    visibility      'anonymous_to_manager' = HR knows, manager does not.
                    'named' = both HR and manager see the employee's name.
    employee_name   Always populated from SSO — controls what manager sees.
    employee_id     Always stored from SSO for HR accountability.
    email           Always stored from SSO for HR accountability.
    department      Populated from SSO — helps HR route the feedback.
    follow_up_ok    If True and visibility is 'named', HR may reach out.
    """
    if category not in VALID_CATEGORIES:
        category = "general"
    if sentiment not in VALID_SENTIMENTS:
        sentiment = "constructive"

    record = {
        "id": _new_id(),
        "submitted_at": _now(),
        "visibility": visibility,
        "employee_name": employee_name,
        "employee_id": employee_id,
        "email": email,
        "department": department or "not specified",
        "category": category,
        "sentiment": sentiment,
        "feedback": feedback_text,
        "follow_up_ok": follow_up_ok if visibility == "named" else False,
        "status": "received",
        "hr_notes": "",
        "action_taken": "",
    }

    data = _load()
    data["feedback"].append(record)
    _save(data)

    visibility_note = {
        "anonymous_to_manager": (
            "Your identity is known to HR but will not be shared with your manager."
        ),
        "named": (
            "Your name will be visible to both HR and your manager."
        ),
    }

    return {
        "success": True,
        "record_id": record["id"],
        "message": (
            f"Feedback submitted — record ID **{record['id']}**. "
            f"{visibility_note.get(visibility, '')} "
            f"The HR team reviews all submissions within 3 business days."
        ),
    }


def get_feedback_summary() -> dict:
    """
    Return a summary of all feedback for the demo's 'HR dashboard' view.
    In a real system this would be a CPO-facing analytics endpoint.
    """
    data = _load()
    records = data["feedback"]

    if not records:
        return {"success": True, "message": "No feedback submitted yet.", "summary": {}}

    by_category = {}
    by_sentiment = {}
    by_status = {}

    for r in records:
        by_category[r["category"]] = by_category.get(r["category"], 0) + 1
        by_sentiment[r["sentiment"]] = by_sentiment.get(r["sentiment"], 0) + 1
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    return {
        "success": True,
        "total": len(records),
        "by_category": by_category,
        "by_sentiment": by_sentiment,
        "by_status": by_status,
        "message": (
            f"{len(records)} feedback submission(s) on record. "
            f"Categories: {by_category}. "
            f"Sentiment breakdown: {by_sentiment}."
        ),
    }


def get_feedback_by_category(category: str) -> dict:
    """Retrieve all feedback records for a given category."""
    data = _load()
    matches = [r for r in data["feedback"] if r["category"] == category.lower()]
    if not matches:
        return {
            "success": True,
            "message": f"No feedback found in the '{category}' category.",
            "records": [],
        }
    display = []
    for r in matches:
        display.append({
            "id": r["id"],
            "submitted_at": r["submitted_at"],
            "sentiment": r["sentiment"],
            "visibility": r["visibility"],
            "feedback": r["feedback"],
            "status": r["status"],
        })
    return {
        "success": True,
        "message": f"Found {len(matches)} submission(s) in the '{category}' category.",
        "records": display,
    }