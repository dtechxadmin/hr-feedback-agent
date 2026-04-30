"""
app.py — Streamlit UI for the HR feedback agent.
Employee tab: chat interface
HR Manager View: filterable table + expanded card view

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from auth import MOCK_SSO_USERS
from records import get_feedback_summary, get_feedback_by_category, _load

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HR Feedback Agent",
    page_icon="💬",
    layout="wide"
)

# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
    <style>
    [data-testid="stChatInputContainer"] {
        border-color: #4A90D9 !important;
        box-shadow: 0 0 0 1px #4A90D9 !important;
    }
    [data-testid="stChatInputContainer"]:focus-within {
        border-color: #4A90D9 !important;
        box-shadow: 0 0 0 2px #4A90D9 !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        outline: none !important;
        box-shadow: none !important;
    }
    .feedback-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 0px;
        background-color: #fafafa;
    }
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-concern      { background-color: #FDECEA; color: #C0392B; }
    .badge-positive     { background-color: #E8F8F0; color: #1E8449; }
    .badge-constructive { background-color: #EBF5FB; color: #1A5276; }
    .badge-urgent       { background-color: #FDF2E9; color: #BA4A00; }
    .badge-anon         { background-color: #F4ECF7; color: #6C3483; }
    .badge-named        { background-color: #EBF5FB; color: #1A5276; }
    .record-table-header {
        display: grid;
        grid-template-columns: 1.5fr 1.2fr 1.2fr 1fr 1.5fr;
        padding: 6px 12px;
        background-color: #f0f2f6;
        border-radius: 4px;
        font-size: 13px;
        font-weight: 600;
        color: #444;
        margin-bottom: 4px;
    }
    .record-table-row {
        display: grid;
        grid-template-columns: 1.5fr 1.2fr 1.2fr 1fr 1.5fr;
        padding: 8px 12px;
        border-bottom: 1px solid #f0f0f0;
        font-size: 14px;
        align-items: center;
    }
    .record-table-row:hover {
        background-color: #f8f9fb;
    }
    div[data-testid="stButton"] button[kind="tertiary"] {
        background: none !important;
        border: none !important;
        color: #1A73E8 !important;
        padding: 0 !important;
        font-size: 14px !important;
        text-decoration: underline !important;
        cursor: pointer !important;
        box-shadow: none !important;
    }
    div[data-testid="stButton"] button[kind="tertiary"]:hover {
        color: #0d47a1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state.logged_in = True
if "current_user" not in st.session_state:
    st.session_state.current_user = MOCK_SSO_USERS["E100001"]
if "history" not in st.session_state:
    st.session_state.history = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []
if "show_suggestions" not in st.session_state:
    st.session_state.show_suggestions = True
if "selected_record" not in st.session_state:
    st.session_state.selected_record = None

# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_real_name(rec: dict) -> str:
    employee_id = rec.get("employee_id")
    if employee_id and employee_id in MOCK_SSO_USERS:
        return MOCK_SSO_USERS[employee_id]["full_name"]
    return rec.get("employee_name", "Unknown")


def render_feedback_card(rec: dict):
    sentiment = rec.get("sentiment", "general")
    visibility = rec.get("visibility", "anonymous_to_manager")
    is_anon = visibility == "anonymous_to_manager"

    sentiment_badge = f'<span class="badge badge-{sentiment}">{sentiment.capitalize()}</span>'
    anon_badge = (
        '<span class="badge badge-anon">Anonymous to Manager</span>'
        if is_anon else
        '<span class="badge badge-named">Named</span>'
    )

    submitted = rec.get("submitted_at", "")
    try:
        dt = datetime.strptime(submitted, "%Y-%m-%d %H:%M")
        formatted_date = dt.strftime("%m/%d/%Y %H:%M")
    except Exception:
        formatted_date = submitted

    st.markdown(f"""
        <div class="feedback-card">
            <div style="margin-bottom:10px;">
                <strong>{rec.get('id', '')}</strong>
                &nbsp;{sentiment_badge}{anon_badge}
            </div>
            <div style="font-size:14px; color:#444; margin-bottom:4px;">
                <strong>Name:</strong> {_get_real_name(rec)}
            </div>
            <div style="font-size:14px; color:#444; margin-bottom:4px;">
                <strong>Category:</strong> {rec.get('category', '').capitalize()}
            </div>
            <div style="font-size:14px; color:#444; margin-bottom:12px;">
                <strong>Date:</strong> {formatted_date}
            </div>
            <hr style="border:none; border-top:1px solid #e0e0e0; margin-bottom:12px;">
            <div style="font-size:15px; color:#222; line-height:1.6;">
                {rec.get('feedback', '')}
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_record_table(filtered: list):
    """Render a custom table with clickable Record ID links."""
    # Header row
    h1, h2, h3, h4, h5 = st.columns([1.5, 1.2, 1.2, 1, 1.5])
    h1.markdown("**Record ID**")
    h2.markdown("**Category**")
    h3.markdown("**Sentiment**")
    h4.markdown("**Date**")
    h5.markdown("**Visibility**")

    # Thin divider with no extra spacing
    st.markdown(
        "<hr style='margin: 4px 0 4px 0; border: none; border-top: 1px solid #e0e0e0;'>",
        unsafe_allow_html=True
    )

    for i, r in enumerate(filtered):
        submitted = r.get("submitted_at", "")
        try:
            dt = datetime.strptime(submitted, "%Y-%m-%d %H:%M")
            display_date = dt.strftime("%m/%d/%Y")
        except Exception:
            display_date = submitted

        visibility_label = (
            "Anonymous to Manager"
            if r.get("visibility") == "anonymous_to_manager"
            else "Named"
        )

        c1, c2, c3, c4, c5 = st.columns([1.5, 1.2, 1.2, 1, 1.5])
        with c1:
            if st.button(
                r.get("id", ""),
                key=f"rec_{i}_{r.get('id')}",
                type="tertiary",
            ):
                st.session_state.selected_record = r
                st.rerun()
        c2.write(r.get("category", "").capitalize())
        c3.write(r.get("sentiment", "").capitalize())
        c4.write(display_date)
        c5.write(visibility_label)

        # Row separator
        st.markdown(
            "<hr style='margin: 0; border: none; border-top: 1px solid #f0f0f0;'>",
            unsafe_allow_html=True
        )


# ── Login screen ──────────────────────────────────────────────────────────────

if not st.session_state.logged_in:
    st.title("HR Feedback Agent")
    st.caption("Please enter your Employee ID to continue.")
    st.divider()

    employee_id = st.text_input(
        "Employee ID",
        placeholder="e.g. E100001",
        max_chars=7,
    )

    if st.button("Log In", type="primary"):
        if employee_id.strip().upper() in MOCK_SSO_USERS:
            user = MOCK_SSO_USERS[employee_id.strip().upper()]
            st.session_state.logged_in = True
            st.session_state.current_user = user
            st.session_state.history = []
            st.session_state.display_messages = []
            st.session_state.show_suggestions = True
            st.session_state.selected_record = None
            st.rerun()
        else:
            st.error(
                f"Employee ID '{employee_id}' not found. "
                "Please check your ID and try again."
            )

    with st.expander("Available demo accounts"):
        st.markdown("""
        | Employee ID | Name | Department |
        |-------------|------|------------|
        | E100001 | Alex Rivera | Engineering |
        | E100002 | Jordan Lee | Marketing |
        | E100003 | Morgan Chen | Operations |
        | E100004 | Elena Vasquez | Human Resources |
        """)

    st.stop()

# ── Main app (logged in) ──────────────────────────────────────────────────────

from agent import run_agent

SSO_USER = st.session_state.current_user
is_hr_manager = SSO_USER["department"] == "Human Resources"

# ── Logout helper ─────────────────────────────────────────────────────────────

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.history = []
    st.session_state.display_messages = []
    st.session_state.show_suggestions = True
    st.session_state.selected_record = None

# ══════════════════════════════════════════════════════════════════════════════
# HR MANAGER VIEW
# ══════════════════════════════════════════════════════════════════════════════

if is_hr_manager:
    header_col, logout_col = st.columns([5, 1])
    with header_col:
        st.header("HR Manager Dashboard")
        st.caption(
            f"Logged in as **{SSO_USER['full_name']}** · "
            f"{SSO_USER['title']} · {SSO_USER['department']}"
        )
    with logout_col:
        st.write("")
        st.write("")
        if st.button("Log Out", type="secondary"):
            logout()
            st.rerun()

    st.divider()

    data = _load()
    all_records = data.get("feedback", [])

    if not all_records:
        st.info("No feedback submitted yet.")
        st.stop()

    # ── Metrics ───────────────────────────────────────────────────────────────
    total = len(all_records)
    by_sent = {}
    for r in all_records:
        s = r.get("sentiment", "general")
        by_sent[s] = by_sent.get(s, 0) + 1

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total submissions", total)
    col2.metric("Urgent", by_sent.get("urgent", 0))
    col3.metric("Concerns", by_sent.get("concern", 0))
    col4.metric("Positive", by_sent.get("positive", 0))

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    all_categories = sorted(set(r.get("category", "general") for r in all_records))

    f1, f2, f3, f4 = st.columns([2, 2, 2, 2])
    with f1:
        cat_filter = st.selectbox(
            "Category",
            options=["All"] + all_categories,
        )
    with f2:
        sent_filter = st.selectbox(
            "Sentiment",
            options=["All", "Positive", "Constructive", "Concern", "Urgent"],
        )
    with f3:
        date_filter = st.date_input(
            "From date",
            value=None,
            format="MM/DD/YYYY",
        )
    with f4:
        st.write("")
        st.write("")
        anon_only = st.checkbox("Show Anonymous Only")

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = all_records.copy()

    if cat_filter != "All":
        filtered = [r for r in filtered if r.get("category") == cat_filter.lower()]
    if sent_filter != "All":
        filtered = [r for r in filtered if r.get("sentiment") == sent_filter.lower()]
    if date_filter:
        filtered = [
            r for r in filtered
            if datetime.strptime(
                r.get("submitted_at", "2000-01-01 00:00"), "%Y-%m-%d %H:%M"
            ).date() >= date_filter
        ]
    if anon_only:
        filtered = [r for r in filtered if r.get("visibility") == "anonymous_to_manager"]

    # ── Table + card layout ───────────────────────────────────────────────────
    if not filtered:
        st.warning("No records match the selected filters.")
    else:
        table_col, card_col = st.columns([3, 2])

        with table_col:
            st.markdown("#### Feedback Records")
            st.caption("Click a Record ID to view the full feedback on the right.")
            render_record_table(filtered)

        with card_col:
            st.markdown(
                "<div style='height: 72px;'></div>",
                unsafe_allow_html=True
            )
            if st.session_state.selected_record:
                render_feedback_card(st.session_state.selected_record)
            else:
                st.caption("← Click a Record ID to view the full feedback here.")

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEE VIEW
# ══════════════════════════════════════════════════════════════════════════════

header_col, logout_col = st.columns([5, 1])
with header_col:
    st.header("HR Feedback Agent")
    st.caption(
        f"Logged in as **{SSO_USER['full_name']}** · "
        f"{SSO_USER['title']} · {SSO_USER['department']}"
    )
with logout_col:
    st.write("")
    st.write("")
    if st.button("Log Out", type="secondary"):
        logout()
        st.rerun()

st.info(
    "🔍 **Demo:** This is a proof-of-concept HR feedback agent built with "
    "the Claude API. You are logged in as a simulated employee via mock SSO. "
    "Try submitting feedback or asking a question, then switch to the "
    "HR Manager View tab to see the dashboard."
)

if st.session_state.show_suggestions:
    with st.expander("Not sure where to start? Try one of these", expanded=True):
        cols = st.columns(2)
        suggestions = [
            "Is my feedback really anonymous?",
            "What happens after I submit?",
            "I want to share feedback about my manager",
            "I have a concern about team culture",
            "Something happened that felt unfair",
            "I want to give positive feedback about onboarding",
        ]
        for i, s in enumerate(suggestions):
            if cols[i % 2].button(s, key=f"sug_{i}"):
                st.session_state["prefill"] = s
                st.session_state.show_suggestions = False
                st.rerun()

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

default_input = st.session_state.pop("prefill", None)

if default_input:
    prompt = default_input
else:
    prompt = st.chat_input("Ask a question or share feedback...")

if prompt:
    st.session_state.show_suggestions = False

    st.session_state.display_messages.append(
        {"role": "user", "content": prompt}
    )
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner(""):
            reply, st.session_state.history = run_agent(
                prompt, st.session_state.history
            )
        st.markdown(reply)

    st.session_state.display_messages.append(
        {"role": "assistant", "content": reply}
    )
    st.rerun()