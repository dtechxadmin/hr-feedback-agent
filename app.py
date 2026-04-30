"""
app.py — Streamlit UI for the HR feedback agent.
Two tabs: Employee (submit feedback) and HR Manager View (dashboard).

Run with:
    streamlit run app.py
"""

import streamlit as st
from auth import MOCK_SSO_USERS
from records import get_feedback_summary, get_feedback_by_category

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HR Feedback Agent",
    page_icon="💬",
    layout="centered"
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
        | E100004 | Sam Torres | Human Resources |
        """)

    st.stop()

# ── Main app (logged in) ──────────────────────────────────────────────────────

from agent import run_agent

SSO_USER = st.session_state.current_user
is_hr_manager = SSO_USER["department"] == "Human Resources"

# ── HR Manager only view ──────────────────────────────────────────────────────

if is_hr_manager:
    st.header("HR Manager Dashboard")
    st.caption(
        f"Logged in as **{SSO_USER['full_name']}** · "
        f"{SSO_USER['title']} · {SSO_USER['department']}"
    )

    col1, col2 = st.columns([5, 1])
    with col2:
        st.write("")
        if st.button("Log Out", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.history = []
            st.session_state.display_messages = []
            st.session_state.show_suggestions = True
            st.rerun()

    st.divider()

    if st.button("Refresh data"):
        st.rerun()

    summary = get_feedback_summary()

    if not summary.get("total"):
        st.info("No feedback submitted yet.")
    else:
        total = summary["total"]
        by_cat = summary.get("by_category", {})
        by_sent = summary.get("by_sentiment", {})

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total submissions", total)
        col2.metric("Urgent", by_sent.get("urgent", 0))
        col3.metric("Concerns", by_sent.get("concern", 0))
        col4.metric("Positive", by_sent.get("positive", 0))

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader("By category")
            for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
                bar_pct = int((count / total) * 100)
                st.markdown(
                    f"`{cat.capitalize()}` &nbsp; **{count}** &nbsp; "
                    f"<span style='opacity:.4'>"
                    f"{'█' * (bar_pct // 10)}{'░' * (10 - bar_pct // 10)}"
                    f"</span>",
                    unsafe_allow_html=True,
                )

        with right:
            st.subheader("By sentiment")
            sentiment_labels = {
                "positive": "Positive",
                "constructive": "Constructive",
                "concern": "Concern",
                "urgent": "Urgent",
            }
            for sent, label in sentiment_labels.items():
                count = by_sent.get(sent, 0)
                if count:
                    st.markdown(f"**{label}**: {count}")

        st.divider()

        st.subheader("Drill into a category")
        selected = st.selectbox(
            "Select category",
            options=sorted(by_cat.keys()),
            label_visibility="collapsed",
        )
        if selected:
            result = get_feedback_by_category(selected)
            for rec in result.get("records", []):
                visibility_label = (
                    "Anonymous to manager"
                    if rec["visibility"] == "anonymous_to_manager"
                    else "Named"
                )
                with st.expander(
                    f"{rec['id']} · {rec['sentiment'].capitalize()} "
                    f"· {visibility_label} · {rec['submitted_at']}"
                ):
                    st.markdown(rec["feedback"])
                    st.caption(f"Status: {rec['status']}")

    st.stop()

# ── Employee view ─────────────────────────────────────────────────────────────

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
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.history = []
        st.session_state.display_messages = []
        st.session_state.show_suggestions = True
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