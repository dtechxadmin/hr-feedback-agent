# HR Feedback Agent

AI-powered internal HR feedback agent built with the Claude API and Streamlit.

## What it does
- Answers employee questions about the feedback process
- Collects feedback via natural language — no forms
- Simulates SSO authentication to identify the logged-in employee
- Submits structured records with category, sentiment, and visibility controls
- CPO dashboard tab shows real-time submission themes and sentiment breakdown

## Tech stack
- Claude API (claude-sonnet-4-5) with tool use
- Streamlit for the chat UI
- JSON file store simulating an HRIS API connection

## Setup
Install dependencies and run:
    python -m venv venv
    source venv/bin/activate
    pip install anthropic streamlit
    export ANTHROPIC_API_KEY=sk-ant-...
    streamlit run app.py

## Architecture
Two-tab Streamlit interface. Employee tab handles conversation and feedback
submission. CPO View tab shows real-time submission themes, sentiment
breakdown, and category drill-down. Agent uses Claude API tool use to route
between FAQ lookup, record creation, and record retrieval.
