# tool_registry.py
# Central registry of all tools the brain can call.
# Each tool maps to an agent file and describes when/how to use it.

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Tool:
    name: str                        # unique tool identifier
    description: str                 # what the tool does — used in LLM prompt
    agent_module: str                # dotted path to the agent file
    parameters: list[str]            # required parameters
    optional_params: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)  # example phrases that trigger this tool


TOOLS: dict[str, Tool] = {

    # ── Email ──────────────────────────────────────────────────────────────────
    "fetch_emails": Tool(
        name="fetch_emails",
        description=(
            "Connects to the IMAP inbox and fetches recent unread emails. "
            "Use when the user wants to check emails, sync inbox, or update contacts from email."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=[],
        optional_params=["limit", "folder", "since_date"],
        examples=[
            "check my emails",
            "pull from inbox",
            "any new emails?",
            "sync my inbox",
        ],
    ),

    "update_contact_from_email": Tool(
        name="update_contact_from_email",
        description=(
            "Reads an email and uses an AI agent to summarise it, then updates "
            "the matching contact record with the summary and interaction log."
        ),
        agent_module="src.Orchestrator.Agents.email_agent",
        parameters=["email_data"],
        optional_params=["contact_id"],
        examples=[
            "update contact from this email",
            "log this email against the contact",
            "summarise and save this email",
        ],
    ),

    # ── UI / Navigation ────────────────────────────────────────────────────────
    "open_tab": Tool(
        name="open_tab",
        description=(
            "Opens a tab in the frontend UI. Use when the user asks to navigate "
            "to a page, view a contact, open a project, or go to a section."
        ),
        agent_module="src.Orchestrator.Agents.ui_agent",
        parameters=["tab_id"],
        optional_params=["label"],
        examples=[
            "open the dashboard",
            "go to settings",
            "show me the contacts page",
            "open project X",
            "take me to tasks",
        ],
    ),

    "get_page_guidance": Tool(
        name="get_page_guidance",
        description=(
            "Provides contextual help and advice about the current page or feature "
            "the user is looking at. Use when the user asks how to do something "
            "in the app or what a section is for."
        ),
        agent_module="src.Orchestrator.Agents.ui_agent",
        parameters=["current_tab_id"],
        optional_params=["question"],
        examples=[
            "how do I use this page",
            "what can I do here",
            "help me with this section",
            "what does this tab do",
            "how do I add a contact",
        ],
    ),

    # ── Projects ───────────────────────────────────────────────────────────────
    "summarise_project": Tool(
        name="summarise_project",
        description=(
            "Generates an AI summary of a project including status, open tasks, "
            "recent activity, and next actions. Use when the user asks for a "
            "project overview or update."
        ),
        agent_module="src.Orchestrator.Agents.project_agent",
        parameters=["project_id"],
        optional_params=["detail_level"],
        examples=[
            "summarise project X",
            "give me an update on this project",
            "what's the status of project X",
            "how is project X going",
            "overview of current projects",
        ],
    ),

    # ── Contacts ───────────────────────────────────────────────────────────────
    "summarise_contact": Tool(
        name="summarise_contact",
        description=(
            "Generates an AI summary of a contact including recent interactions, "
            "open tasks, and relationship notes."
        ),
        agent_module="src.Orchestrator.Agents.contact_agent",
        parameters=["contact_id"],
        optional_params=[],
        examples=[
            "summarise this contact",
            "give me a rundown on John",
            "what's the history with this client",
            "who is Jane Smith",
        ],
    ),

    # ── General ────────────────────────────────────────────────────────────────
    "general_query": Tool(
        name="general_query",
        description=(
            "Handles general conversation, questions, and anything that doesn't "
            "map to a specific tool. Falls back to direct Qwen response."
        ),
        agent_module="src.Orchestrator.Agents.general_agent",
        parameters=["message"],
        optional_params=["history"],
        examples=[],
    ),
}


def get_tool(name: str) -> Optional[Tool]:
    return TOOLS.get(name)


def get_all_tools() -> list[Tool]:
    return list(TOOLS.values())


def get_tool_descriptions_for_prompt() -> str:
    """
    Formats all tools into a string for injection into the
    intent classification prompt so the LLM knows what's available.
    """
    lines = []
    for tool in TOOLS.values():
        lines.append(f"- {tool.name}: {tool.description}")
    return "\n".join(lines)