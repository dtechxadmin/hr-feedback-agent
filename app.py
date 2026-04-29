"""
app.py — Streamlit UI for the HR feedback agent.
Two tabs: Employee (submit feedback) and HR Manager View (summary dashboard).

Run with:
    streamlit run app.py
"""

import streamlit as st
from agent import run_agent, SSO_USER
from records import get_feedback_summary, get_feedback_by_category

st.set_page_config(
    page_title="HR Feedback Assistant",
    page_icon="💬",
    layout="centered"
)

st.markdown("""
    <style>
    * :focus {
        outline: none !important;
        box-shadow: none !important;
    }
    * {
        --primary-color: #e0e0e0 !important;
    }
    textarea:focus {
        border-color: #e0e0e0 !important;
        outline: none !important;
        box-shadow: none !important;
    }
    div[data-baseweb] * {
        border-color: #e0e0e0 !important;
    }
    div[data-baseweb]:focus-within * {
        border-color: #e0e0e0 !important;
        box-shadow: none !important;
    }
    </style>
""", unsafe_allow_html=True)

employee_tab, hrm_tab = st.tabs(["Employee", "HR Manager View"])

# ── Employee tab ──────────────────────────────────────────────────────────────

with employee_tab:
    st.header("HR Feedback Assistant")
    st.caption(
        f"Logged in as **{SSO_USER['full_name']}** · "
        f"{SSO_USER['title']} · {SSO_USER['department']}"
    )

    # Initialize session state on first load
    if "history" not in st.session_state:
        st.session_state.history = []
    if "display_messages" not in st.session_state:
        st.session_state.display_messages = []
    if "show_suggestions" not in st.session_state:
        st.session_state.show_suggestions = True

    # Only show suggestion buttons when conversation hasn't started
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

    # Render full conversation history
    for msg in st.session_state.display_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle prefill from suggestion buttons
    default_input = st.session_state.pop("prefill", None)

    if default_input:
        prompt = default_input
    else:
        prompt = st.chat_input("Ask a question or share feedback...")

    if prompt:
        # Hide suggestions once conversation starts
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

# ── HR Manager View tab ──────────────────────────────────────────────────────────────

with hrm_tab:
    st.header("HR Manager Dashboard")
    st.caption("Real-time view of all submissions — refreshes on each interaction.")

    if st.button("Refresh data"):
        st.rerun()

    summary = get_feedback_summary()

    if not summary.get("total"):
        st.info("No feedback submitted yet. Use the Employee tab to submit some.")
    else:
        total = summary["total"]
        by_cat = summary.get("by_category", {})
        by_sent = summary.get("by_sentiment", {})

        # ── Metric cards ──────────────────────────────────────────────────────
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total submissions", total)
        col2.metric("Urgent", by_sent.get("urgent", 0))
        col3.metric("Concerns", by_sent.get("concern", 0))
        col4.metric("Positive", by_sent.get("positive", 0))

        st.divider()

        # ── Category and sentiment breakdown ──────────────────────────────────
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

        # ── Drill-down by category ────────────────────────────────────────────
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