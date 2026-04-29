"""
auth.py — Mock SSO session for the HR feedback agent.

Simulates what an enterprise SSO provider (Okta, Azure AD) would inject
after authenticating the employee. In production, this dict would be
populated from the SSO token payload — the agent never asks for it.

To demo a different employee, change CURRENT_USER_ID before running.
"""

MOCK_SSO_USERS = {
    "E100001": {
        "employee_id": "E100001",
        "full_name": "Alex Rivera",
        "email": "a.rivera@company.com",
        "department": "Engineering",
        "title": "Software Engineer",
    },
    "E100002": {
        "employee_id": "E100002",
        "full_name": "Jordan Lee",
        "email": "j.lee@company.com",
        "department": "Marketing",
        "title": "Marketing Manager",
    },
    "E100003": {
        "employee_id": "E100003",
        "full_name": "Morgan Chen",
        "email": "m.chen@company.com",
        "department": "Operations",
        "title": "Operations Analyst",
    },
}

# Swap this ID to simulate a different logged-in employee
CURRENT_USER_ID = "E100001"


def get_current_user() -> dict:
    """
    Returns the authenticated employee's profile.
    Raises an error if the session is invalid — same behavior
    as a real SSO provider rejecting an expired token.
    """
    user = MOCK_SSO_USERS.get(CURRENT_USER_ID)
    if not user:
        raise ValueError(f"No SSO session found for user ID: {CURRENT_USER_ID}")
    return user