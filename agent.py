"""
agent.py — HR feedback agent (CPO-focused POC).

Four tools, all scoped to the feedback loop:
  lookup_faq            → answer questions about how feedback works
  submit_feedback       → create a feedback record (Confidential or Shared)
  get_feedback_summary  → high-level dashboard view (for the CPO demo)
  get_feedback_by_category → drill into a specific theme

Run in terminal:
    python agent.py

Import run_agent() into app.py for Streamlit on Day 2.
"""

import json
import os
import anthropic
import streamlit as st
from faq import lookup_faq
from auth import get_current_user
from records import submit_feedback, get_feedback_summary, get_feedback_by_category

# ── Load SSO session at startup ───────────────────────────────────────────────

SSO_USER = get_current_user()

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "lookup_faq",
        "description": (
            "Answer questions about how the feedback process works: confidentiality, "
            "what happens after submission, pulse survey cadence, retaliation policy, "
            "manager feedback, and how this differs from performance reviews. "
            "Use this whenever an employee asks a 'how does this work' question before deciding "
            "whether to submit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The employee's question."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "submit_feedback",
        "description": (
            "Submit employee feedback to the HR team. Use this when an employee is ready "
            "to share feedback, a concern, a suggestion, or a positive observation. "
            "Always confirm visibility preference before calling this tool. "
            "Infer category and sentiment from the content if the employee doesn't specify. "
            "Never ask for the employee's name, ID, email, or department — these are populated "
            "automatically from their SSO profile."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "feedback_text": {
                    "type": "string",
                    "description": "The full feedback content in the employee's own words.",
                },
                "visibility": {
                    "type": "string",
                    "enum": ["anonymous_to_manager", "named"],
                    "description": (
                        "Controls how the employee's identity is shared. "
                        "'anonymous_to_manager' means HR knows who submitted but the manager does not. "
                        "'named' means both HR and the manager see the employee's name. "
                        "HR always has access to the submitter's identity regardless of this setting."
                    ),
                },
                "category": {
                    "type": "string",
                    "enum": ["culture", "management", "onboarding", "benefits", "dei",
                             "workload", "policy", "recognition", "general"],
                    "description": "Topic category. Infer from content if not stated.",
                },
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "constructive", "concern", "urgent"],
                    "description": (
                        "Tone of the feedback. 'constructive' = improvement suggestion, "
                        "'concern' = something feels wrong, 'urgent' = needs immediate attention."
                    ),
                },
                "follow_up_ok": {
                    "type": "boolean",
                    "description": (
                        "True if the employee is open to HR following up. "
                        "Only applicable when visibility is 'named'."
                    ),
                },
            },
            "required": ["feedback_text", "visibility"],
        },
    },
    {
        "name": "get_feedback_summary",
        "description": (
            "Retrieve a high-level summary of all feedback submissions: total count, "
            "breakdown by category, sentiment distribution, and status. "
            "Use this when someone asks for an overview of what feedback has come in — "
            "most useful for the HR team or a CPO wanting a pulse on themes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_feedback_by_category",
        "description": (
            "Retrieve all feedback submissions for a specific category "
            "(e.g. 'management', 'onboarding', 'culture'). "
            "Use this when drilling into a specific theme."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "The category to filter by.",
                }
            },
            "required": ["category"],
        },
    },
]

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are an internal HR feedback assistant for a mid-size organization. \
Your job is to help employees share feedback with the HR team in a way that feels safe, \
clear, and worth their time. You support any employee regardless of their department, \
seniority, or role.

The employee you are speaking with has already been authenticated via SSO. \
Their verified profile is:
- Name: {SSO_USER['full_name']}
- Employee ID: {SSO_USER['employee_id']}
- Email: {SSO_USER['email']}
- Department: {SSO_USER['department']}
- Title: {SSO_USER['title']}

Never ask the employee for their name, ID, email, or department — you already have this \
information. Use their first name naturally in conversation. When submitting feedback, \
populate employee_name, employee_id, email, and department automatically from their profile.

You have four tools:
- lookup_faq: explain how the feedback process works
- submit_feedback: create a feedback record
- get_feedback_summary: show a high-level overview of all submissions
- get_feedback_by_category: drill into a specific feedback theme

Guidelines:
- Build trust before asking for feedback. If an employee seems hesitant, use lookup_faq \
to address their concern first.
- When an employee wants to submit feedback, first acknowledge their concern warmly in 1-2 \
sentences. Then ask the visibility question as a direct two-option prompt in this exact format:\n\n\
"Would you like to keep this confidential, or is it okay to share with your manager?\n\n\
- **Confidential** — HR will have your name on record, but your manager will not see it.\n\
- **Shared** — Both HR and your manager will see your name on this feedback."\n\n\
Wait for the employee to reply before asking anything else. \
Only after receiving their answer, ask a single focused question to gather the \
feedback content, such as "What's going on with your team's culture that you'd like to share?" \
Match the question to the topic they raised. Do not ask for the feedback and the visibility \
preference in the same message. Never use the word 'anonymous' — always use \
'Confidential' or 'Shared' instead.
- Infer category and sentiment from the content — do not interrogate the employee with a \
form. Use 'concern' when the employee expresses unmet needs, feels overlooked, or describes \
something that isn't working for them personally. Reserve 'constructive' for suggestions or \
process improvements that don't carry personal impact.
- Before calling submit_feedback, always show the employee a preview of exactly what will \
be submitted. Format it like this: 'Here is what I'll submit to HR:\n\n\"[feedback text]\"\n\nDoes \
this look right, or would you like to change anything before I submit?' Only call \
submit_feedback after the employee replies with a clear confirmation such as 'yes', \
'submit it', 'looks good', 'go ahead', or similar. If they want to change the wording, \
let them revise it and show the preview again before submitting.
- After submitting, give the employee their record ID and a plain-language explanation \
of what happens next.
- For the summary/category tools, present the data in a readable way — not as raw JSON.
- If someone seems distressed or describes an urgent situation, acknowledge it directly \
before moving to the tool. Use 'urgent' sentiment for anything that sounds like a policy \
violation or safety concern.
- If an employee's message contains inappropriate language — including profanity, personal \
attacks on named individuals, derogatory statements, or expressions of hostility that are \
harmful rather than constructive (e.g. "this company sucks", "Mike is the worst", "I hate \
everyone here") — do not validate the language or submit it. Instead, respond with empathy \
for the underlying emotion while firmly and professionally declining to process the message \
as written. Acknowledge that they may be frustrated, upset, or feeling unheard, and that \
those feelings are valid. Then clearly state that the feedback as expressed is not something \
that can be submitted to HR because it does not meet the standard for professional workplace \
communication. Invite them to rephrase their concern in a way that describes the situation \
or impact rather than attacking a person or using harmful language. Make clear they are \
welcome to try again — the goal is to help them be heard, not to silence them. Never use \
a dismissive or punitive tone. The employee should leave the interaction feeling respected \
even if their initial message was not appropriate.
- Never pressure anyone to submit. If they change their mind, say that's completely fine.
"""

# ── Tool dispatcher ───────────────────────────────────────────────────────────

def dispatch_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "lookup_faq":
        return lookup_faq(tool_input["query"])

    if tool_name == "submit_feedback":
        visibility = tool_input.get("visibility", "anonymous_to_manager")
        is_named = visibility == "named"
        result = submit_feedback(
            feedback_text=tool_input["feedback_text"],
            category=tool_input.get("category", "general"),
            sentiment=tool_input.get("sentiment", "constructive"),
            visibility=visibility,
            employee_name=SSO_USER["full_name"] if is_named else "Anonymous",
            employee_id=SSO_USER["employee_id"],
            email=SSO_USER["email"],
            department=SSO_USER["department"],
            follow_up_ok=tool_input.get("follow_up_ok", False) if is_named else False,
        )
        return json.dumps(result)

    if tool_name == "get_feedback_summary":
        return json.dumps(get_feedback_summary())

    if tool_name == "get_feedback_by_category":
        return json.dumps(get_feedback_by_category(tool_input["category"]))

    return f"Unknown tool: {tool_name}"


# ── Core agent loop ───────────────────────────────────────────────────────────

def run_agent(user_message: str, history: list) -> tuple[str, list]:
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    history = history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=history,
        )

        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            reply = " ".join(
                block.text for block in response.content if hasattr(block, "text")
            )
            return reply, history

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = dispatch_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            history.append({"role": "user", "content": tool_results})


# ── Terminal test harness ─────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"HR Feedback Agent — POC  (type 'quit' to exit)")
    print(f"Logged in as: {SSO_USER['full_name']} ({SSO_USER['employee_id']})\n")
    history = []
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if not user_input:
            continue
        reply, history = run_agent(user_input, history)
        print(f"\nAgent: {reply}\n")