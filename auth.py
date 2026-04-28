"""
auth.py — Mock SSO session for the HR feedback agent POC.

Simulates what an enterprise SSO provider (Okta, Azure AD) would inject
after authenticating the employee. In production, this dict would be
populated from the SSO token payload — the agent never asks for it.

To demo a different employee, change the values in MOCK_SSO_USERS and
update CURRENT_USER_ID before running.
"""

MOCK_SSO_USERS = {
    "E482193": {
        "employee_id": "E482193",
        "full_name": "Bryant Glover",
        "email": "bryant.glover@email.com",
        "department": "Product",
        "title": "AI Fellow",
    },
    "E291847": {
        "employee_id": "E291847",
        "full_name": "Jordan Kim",
        "email": "j.kim@company.com",
        "department": "Engineering",
        "title": "Software Engineer II",
    },
    "E739204": {
        "employee_id": "E739204",
        "full_name": "Sarah Chen",
        "email": "s.chen@company.com",
        "department": "People Operations",
        "title": "HR Business Partner",
    },
}

# Swap this ID to simulate a different logged-in employee
CURRENT_USER_ID = "E482193"


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