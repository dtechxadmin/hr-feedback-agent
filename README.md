# HR Feedback Agent

An AI-powered internal HR feedback agent built with the Claude API and Streamlit.
Designed for any organization looking to improve how employees share feedback
with HR — removing friction, building trust, and closing the feedback loop.

## Live Demo

[Insert your Streamlit URL here once deployed]

Log in as any of the simulated SSO users to explore the employee experience,
then switch to the HR Manager View tab to see the feedback dashboard.

## What it does

- Answers employee questions about the feedback process in natural language
- Collects structured feedback without forms — one conversation, no navigation
- Simulates SSO authentication so the agent knows who it is talking to
- Gives employees control over visibility: anonymous to manager, or fully named
- HR always retains submitter identity for accountability and governance
- HR Manager dashboard shows real-time themes, sentiment, and category breakdown

## Why it matters

Most feedback tools fail because employees do not trust the channel or find it
too cumbersome to use. This agent addresses both: it answers trust questions
before asking for anything, and collects feedback through natural conversation
rather than a form.

## Tech stack

- Claude API (claude-sonnet-4-5) with tool use
- Streamlit for the chat interface and HR dashboard
- JSON file store (simulates HRIS API — Workday, Lattice, Culture Amp)
- Mock SSO session (simulates Okta / Azure AD token injection)

## Architecture

```
Streamlit
├── Employee tab        (chat interface)
└── HR Manager View tab (feedback dashboard)
         │
         ▼
Claude API — 4 tools
         │
         ├── lookup_faq
         │     └── faq.py (keyword search · 6 trust-focused entries)
         │
         ├── submit_feedback
         │     └── records.py (JSON store · category · sentiment · visibility)
         │
         ├── get_feedback_summary
         │     └── records.py (totals · by category · by sentiment)
         │
         └── get_feedback_by_category
               └── records.py (drill into a specific theme)
```

## Simulated SSO users

To demo as a different employee, change `CURRENT_USER_ID` in `auth.py`:

| ID | Name | Department | Title |
|----|------|------------|-------|
| E100001 | Alex Rivera | Engineering | Software Engineer |
| E100002 | Jordan Lee | Marketing | Marketing Manager |
| E100003 | Morgan Chen | Operations | Operations Analyst |

## Production path

| POC approach | Production replacement |
|---|---|
| Keyword FAQ matching | ChromaDB vector store over full HR handbook |
| JSON file store | Workday / Lattice / Culture Amp API |
| Mock SSO session | Okta / Azure AD JWT token |
| Manual dashboard refresh | n8n webhook — urgent submissions trigger Slack alert |
| Streamlit Community Cloud | Company intranet or Teams / Slack integration |